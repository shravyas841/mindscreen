from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class PHQResult:
    total_score: int
    severity: str
    confidence: float
    probabilities: Dict[str, float]
    shap_data: Dict[str, Any]

def calculate_phq_score(answers: List[int]) -> PHQResult:
    total = sum(answers)
    
    if total < 5:
        severity = "minimal"
        probabilities = {"minimal": 0.8, "mild": 0.15, "moderate": 0.05, "severe": 0.0}
    elif total < 10:
        severity = "mild"
        probabilities = {"minimal": 0.1, "mild": 0.7, "moderate": 0.15, "severe": 0.05}
    elif total < 15:
        severity = "moderate"
        probabilities = {"minimal": 0.0, "mild": 0.15, "moderate": 0.7, "severe": 0.15}
    else:
        severity = "severe"
        probabilities = {"minimal": 0.0, "mild": 0.05, "moderate": 0.15, "severe": 0.8}
        
    shap_data = {
        "phq_factors": [
            {"question": f"Q{i+1}", "value": val} for i, val in enumerate(answers) if val > 0
        ]
    }
    
    return PHQResult(
        total_score=total,
        severity=severity,
        confidence=probabilities[severity],
        probabilities=probabilities,
        shap_data=shap_data
    )
