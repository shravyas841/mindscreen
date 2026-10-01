from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.assessment import Assessment
from models.user import User
from schemas.assessment import FusedPredictRequest, RiskResponse, PredictTextRequest
from services.fusion_service import get_fused_prediction
from services.ml_service import get_text_prediction
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/predict", tags=["prediction"])

@router.post("/text", response_model=RiskResponse)
async def predict_text(
    request: PredictTextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not request.text.strip():
        raise HTTPException(status_code=422, detail="Text cannot be empty")
        
    result = get_text_prediction(request.text)
    crisis_flag = result["risk_level"] == "severe"

    assessment = Assessment(
        user_id       = current_user.id,
        text_entry    = request.text,
        risk_level    = result["risk_level"],
        confidence    = result["confidence"],
        probabilities = result["probabilities"],
        shap_data     = result["shap_data"],
        crisis_flag   = crisis_flag,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    response = RiskResponse(
        risk_level       = result["risk_level"],
        confidence       = result["confidence"],
        probabilities    = result["probabilities"],
        shap_explanation = result["shap_data"],
        crisis_flag      = crisis_flag,
        helplines        = [
            "iCall: 9152987821",
            "NIMHANS: 080-46110007",
            "Vandrevala Foundation: 1860-2662-345"
        ] if crisis_flag else None,
    )
    return response

@router.post("/fused", response_model=RiskResponse)
async def predict_fused(
    request: FusedPredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(request.answers) != 9:
        raise HTTPException(status_code=422, detail="Exactly 9 PHQ-9 answers required")
    if any(a < 0 or a > 3 for a in request.answers):
        raise HTTPException(status_code=422, detail="Each answer must be 0, 1, 2, or 3")
    if not request.text.strip():
        raise HTTPException(status_code=422, detail="Text cannot be empty")

    result = get_fused_prediction(
        request.answers,
        request.text,
        audio_features=request.audio_features.model_dump() if request.audio_features else None,
        audio_base64=request.audio_base64,
    )
    crisis_flag = result["risk_level"] == "severe" or request.answers[8] > 0

    assessment = Assessment(
        user_id       = current_user.id,
        phq_answers   = request.answers,
        text_entry    = request.text,
        risk_level    = result["risk_level"],
        confidence    = result["confidence"],
        probabilities = result["probabilities"],
        shap_data     = result["shap_data"],
        crisis_flag   = crisis_flag,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    response = RiskResponse(
        risk_level        = result["risk_level"],
        confidence        = result["confidence"],
        probabilities     = result["probabilities"],
        raw_probabilities = result.get("raw_probabilities"),
        shap_explanation  = result["shap_data"],
        audio_features    = result.get("audio_features"),
        crisis_flag       = crisis_flag,
        helplines         = [
            "iCall: 9152987821",
            "NIMHANS: 080-46110007",
            "Vandrevala Foundation: 1860-2662-345"
        ] if crisis_flag else None,
    )
    return response
