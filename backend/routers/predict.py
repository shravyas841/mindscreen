from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.assessment import Assessment
from models.user import User
from schemas.assessment import FusedPredictRequest, RiskResponse, PredictTextRequest
from services.fusion_service import apply_safety_rules, get_fused_prediction
from services.ml_service import get_text_prediction
from services.auth_service import get_current_user
from services.negation_service import detect_crisis_intent
from config import crisis_helplines
from middleware.rate_limit import limiter

router = APIRouter(prefix="/api/predict", tags=["prediction"])

@router.post("/text", response_model=RiskResponse)
@limiter.limit("30/minute")
async def predict_text(
    request: Request,
    payload: PredictTextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not payload.text.strip():
        raise HTTPException(status_code=422, detail="Text cannot be empty")
        
    result = get_text_prediction(payload.text)
    crisis_result = detect_crisis_intent(payload.text)
    safety = apply_safety_rules(
        fused_tier=result["risk_level"],
        phq_tier=result["risk_level"],
        item9_positive=False,
        text_crisis=bool(crisis_result["is_crisis"]),
        base_score=result["confidence"],
    )

    assessment = Assessment(
        user_id       = current_user.id,
        text_entry    = None,  # data minimisation: do not persist journal text
        risk_level    = safety["risk_level"],
        confidence    = safety["priority_score"],
        probabilities = result["probabilities"],
        shap_data     = result["shap_data"],
        crisis_flag   = safety["crisis_flag"],
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    response = RiskResponse(
        risk_level       = safety["risk_level"],
        confidence       = safety["priority_score"],
        priority_score   = safety["priority_score"],
        probabilities    = result["probabilities"],
        shap_explanation = result["shap_data"],
        crisis_flag      = safety["crisis_flag"],
        resource_display_flag = safety["resource_display_flag"],
        crisis_trigger   = crisis_result.get("trigger"),
        text_inference_source = result.get("inference_source", "unknown"),
        helplines        = crisis_helplines() if safety["resource_display_flag"] else None,
    )
    return response

@router.post("/fused", response_model=RiskResponse)
@limiter.limit("30/minute")
async def predict_fused(
    request: Request,
    payload: FusedPredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(payload.answers) != 9:
        raise HTTPException(status_code=422, detail="Exactly 9 PHQ-9 answers required")
    if any(a < 0 or a > 3 for a in payload.answers):
        raise HTTPException(status_code=422, detail="Each answer must be 0, 1, 2, or 3")
    if not payload.text.strip():
        raise HTTPException(status_code=422, detail="Text cannot be empty")

    result = get_fused_prediction(
        payload.answers,
        payload.text,
        audio_features=payload.audio_features.model_dump() if payload.audio_features else None,
    )

    assessment = Assessment(
        user_id       = current_user.id,
        phq_answers   = payload.answers,
        text_entry    = None,  # data minimisation: do not persist journal text
        risk_level    = result["risk_level"],
        confidence    = result["confidence"],
        probabilities = result["probabilities"],
        shap_data     = result["shap_data"],
        crisis_flag   = result["crisis_flag"],
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    response = RiskResponse(
        risk_level        = result["risk_level"],
        confidence        = result["confidence"],
        priority_score    = result["priority_score"],
        probabilities     = result["probabilities"],
        raw_probabilities = result.get("raw_probabilities"),
        shap_explanation  = result["shap_data"],
        audio_features    = result.get("audio_features"),
        crisis_flag       = result["crisis_flag"],
        resource_display_flag = result["resource_display_flag"],
        phq_floor_applied = result["phq_floor_applied"],
        audio_present     = result["audio_present"],
        text_inference_source = result["text_inference_source"],
        crisis_trigger   = result.get("crisis_trigger"),
        helplines         = crisis_helplines() if result["resource_display_flag"] else None,
    )
    return response
