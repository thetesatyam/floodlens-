def rainfall_score(rainfall):
    if rainfall < 30:
        return 10
    elif rainfall < 60:
        return 35
    elif rainfall < 100:
        return 65
    else:
        return 95


def elevation_score(category):
    scores = {
        "high": 10,
        "medium": 50,
        "low": 90
    }

    return scores.get(category, 50)


def historical_score(category):
    scores = {
        "low": 20,
        "medium": 55,
        "high": 90
    }

    return scores.get(category, 50)


def ground_report_score(reports):
    if not reports:
        return 0

    total_trust = sum(report["trust_score"] for report in reports)

    return min(100, total_trust * 20)


def calculate_risk(settlement):

    rainfall = settlement["rainfall_mm_24h"]
    elevation = settlement["elevation_category"]
    historical = settlement["historical_risk"]
    reports = settlement["ground_reports"]

    rainfall_component = rainfall_score(rainfall)
    elevation_component = elevation_score(elevation)
    historical_component = historical_score(historical)
    ground_component = ground_report_score(reports)

    risk_score = (
        rainfall_component * 0.40
        + elevation_component * 0.20
        + historical_component * 0.20
        + ground_component * 0.20
    )

    risk_score = round(risk_score, 2)

    if risk_score >= 80:
        risk_level = "critical"
    elif risk_score >= 60:
        risk_level = "high"
    elif risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Prototype confidence calculation
    confidence = calculate_confidence(
        rainfall_component,
        elevation_component,
        historical_component,
        reports
    )

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "confidence_pct": confidence,

        "evidence": {
            "rainfall": {
                "value_mm_24h": rainfall,
                "score": rainfall_component,
                "weight": 0.40
            },

            "elevation": {
                "category": elevation,
                "score": elevation_component,
                "weight": 0.20
            },

            "historical_risk": {
                "category": historical,
                "score": historical_component,
                "weight": 0.20
            },

            "ground_reports": {
                "count": len(reports),
                "score": ground_component,
                "weight": 0.20
            }
        }
    }


def calculate_confidence(
    rainfall_component,
    elevation_component,
    historical_component,
    reports
):

    confidence = 60

    # More ground reports → more confidence
    if len(reports) >= 3:
        confidence += 20
    elif len(reports) >= 1:
        confidence += 10

    # Keep within 0–100
    return min(confidence, 95)

def calculate_report_trust(
    nearby_reports,
    rainfall_agreement
):
    """
    Prototype trust model.

    nearby_reports:
        Number of corroborating reports nearby.

    rainfall_agreement:
        0 to 1 indicating agreement with rainfall conditions.
    """

    corroboration_score = min(1.0, nearby_reports / 3)

    trust = (
        corroboration_score * 0.60
        + rainfall_agreement * 0.40
    )

    return round(trust, 2)