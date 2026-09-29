from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from risk_engine.data import settlements
from risk_engine.risk_engine import calculate_risk


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app = FastAPI(
    title="FloodLens Risk Engine",
    description="Trust-weighted flood risk scoring API",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "FloodLens Risk Engine API",
        "status": "running"
    }


@app.get("/api/settlements")
def get_settlements():

    result = []

    for settlement in settlements:

        risk = calculate_risk(settlement)

        result.append({
            "id": settlement["id"],
            "name": settlement["name"],
            "lat": settlement["lat"],
            "lng": settlement["lng"],
            "population": settlement["population"],
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "confidence_pct": risk["confidence_pct"]
        })

    return {
        "settlements": result
    }


@app.get("/api/settlements/{settlement_id}/risk")
def get_settlement_risk(settlement_id: str):

    settlement = next(
        (
            s for s in settlements
            if s["id"] == settlement_id
        ),
        None
    )

    if settlement is None:
        raise HTTPException(
            status_code=404,
            detail="Settlement not found"
        )

    risk = calculate_risk(settlement)

    return {
        "settlement": {
            "id": settlement["id"],
            "name": settlement["name"],
            "lat": settlement["lat"],
            "lng": settlement["lng"]
        },

        "risk": {
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "confidence_pct": risk["confidence_pct"]
        },

        "evidence": risk["evidence"]
    }


@app.post("/api/simulation/trigger-flood")
def trigger_flood():

    # Simulate heavy rainfall
    for settlement in settlements:
        settlement["rainfall_mm_24h"] += 50

    return {
        "message": "Flood simulation triggered",
        "settlements": [
            {
                "id": s["id"],
                "rainfall_mm_24h": s["rainfall_mm_24h"],
                "risk": calculate_risk(s)
            }
            for s in settlements
        ]
    }


@app.post("/api/simulation/reset")
def reset_simulation():

    default_rainfall = {
        "S001": 45,
        "S002": 40,
        "S003": 30,
        "S004": 25,
        "S005": 35
    }

    for settlement in settlements:
        settlement["rainfall_mm_24h"] = default_rainfall[
            settlement["id"]
        ]

    return {
        "message": "Simulation reset successfully"
    }