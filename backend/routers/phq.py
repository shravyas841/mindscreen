from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.assessment import Assessment
from models.user import User
from schemas.assessment import PHQSubmitRequest, RiskResponse
from services.phq_service import calculate_phq_score
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/phq", tags=["assessment"])

@router.post("/submit", response_model=RiskResponse)
async def submit_phq(
    request: PHQSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(request.answers) != 9:
        raise HTTPException(status_code=422, detail="Exactly 9 PHQ-9 answers required")
    if any(a < 0 or a > 3 for a in request.answers):
        raise HTTPException(status_code=422, detail="Each answer must be 0, 1, 2, or 3")

    phq_result = calculate_phq_score(request.answers)
    crisis_flag = phq_result.total_score >= 15 or request.answers[8] > 0

    assessment = Assessment(
        user_id       = current_user.id,
        phq_answers   = request.answers,
        risk_level    = phq_result.severity,
        confidence    = phq_result.confidence,
        probabilities = phq_result.probabilities,
        shap_data     = phq_result.shap_data,
        crisis_flag   = crisis_flag,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    response = RiskResponse(
        risk_level       = phq_result.severity,
        confidence       = phq_result.confidence,
        probabilities    = phq_result.probabilities,
        shap_explanation = phq_result.shap_data,
        crisis_flag      = crisis_flag,
        helplines        = [
            "iCall: 9152987821",
            "NIMHANS: 080-46110007",
            "Vandrevala Foundation: 1860-2662-345"
        ] if crisis_flag else None,
    )

    return response

@router.get("/history")
async def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assessments = db.query(Assessment).filter(Assessment.user_id == current_user.id).order_by(Assessment.created_at.desc()).all()
    return assessments
