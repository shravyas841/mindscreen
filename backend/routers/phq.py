from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.assessment import Assessment
from models.user import User
from schemas.assessment import PHQSubmitRequest, RiskResponse
from services.phq_service import calculate_phq_score
from services.auth_service import get_current_user
from services.fusion_service import apply_safety_rules
from config import crisis_helplines
from middleware.rate_limit import limiter

router = APIRouter(prefix="/api/phq", tags=["assessment"])

@router.post("/submit", response_model=RiskResponse)
@limiter.limit("30/minute")
async def submit_phq(
    request: Request,
    payload: PHQSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(payload.answers) != 9:
        raise HTTPException(status_code=422, detail="Exactly 9 PHQ-9 answers required")
    if any(a < 0 or a > 3 for a in payload.answers):
        raise HTTPException(status_code=422, detail="Each answer must be 0, 1, 2, or 3")

    phq_result = calculate_phq_score(payload.answers)
    safety = apply_safety_rules(
        fused_tier=phq_result.severity,
        phq_tier=phq_result.severity,
        item9_positive=payload.answers[8] > 0,
        text_crisis=False,
        base_score=phq_result.confidence,
    )

    assessment = Assessment(
        user_id       = current_user.id,
        phq_answers   = payload.answers,
        risk_level    = safety["risk_level"],
        confidence    = safety["priority_score"],
        probabilities = phq_result.probabilities,
        shap_data     = phq_result.shap_data,
        crisis_flag   = safety["crisis_flag"],
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    response = RiskResponse(
        risk_level       = safety["risk_level"],
        confidence       = safety["priority_score"],
        priority_score   = safety["priority_score"],
        probabilities    = phq_result.probabilities,
        shap_explanation = phq_result.shap_data,
        crisis_flag      = safety["crisis_flag"],
        resource_display_flag = safety["resource_display_flag"],
        helplines        = crisis_helplines() if safety["resource_display_flag"] else None,
    )

    return response

@router.get("/history")
async def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assessments = db.query(Assessment).filter(Assessment.user_id == current_user.id).order_by(Assessment.created_at.desc()).all()
    return assessments
