from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import requests
import logging
import random
import os
from config import settings
from middleware.rate_limit import limiter
from models.user import User
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Saathi Wellbeing Companion"])

# ── Data Models ────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    sender: Literal["user", "saathi"] = Field(..., description="'user' or 'saathi'")
    content: str = Field(..., min_length=1, max_length=5000, description="Message text")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    history: List[ChatMessage] = Field(default_factory=list, max_length=50, description="Conversation history")
    current_mood: Optional[str] = Field(default="neutral")

class RecommendedActivity(BaseModel):
    title: str
    category: str
    duration: str
    action_type: str

class ChatResponse(BaseModel):
    reply: str
    companion_name: str = "Saathi"
    tagline: str = "Your wellbeing companion"
    recommended_activity: Optional[RecommendedActivity] = None
    crisis_flag: bool = False
    helpline_info: Optional[str] = None

# ── Constants ──────────────────────────────────────────────────────────────────

TELE_MANAS = "Tele-MANAS (Govt. of India): 14416 or 1-800-891-4416 (Free, 24/7)"
ICALL      = "iCall (TISS): 9152987821 (Mon–Sat, 8am–10pm)"

SYSTEM_PROMPT = """You are Saathi (साथी), a warm, empathetic, and culturally aware Indian mental wellbeing companion on the MindScreen platform.

Your role:
- Listen without judgment and reflect what the user shares back to them with care
- Ask thoughtful follow-up questions to help users unpack their emotions
- Acknowledge the specific Indian cultural context (family expectations, exam/career pressure, societal judgments)
- Keep responses conversational, warm, and 2-4 short paragraphs
- Gently suggest self-care activities (breathing, journaling, a chai break) when appropriate
- NEVER diagnose, prescribe, or claim to be a therapist
- ALWAYS maintain safety: if crisis signals appear, provide helplines immediately

Important conversation behavior:
- The user has already seen your initial welcome screen. DO NOT repeat "Namaste I'm Saathi" or re-introduce yourself.
- Jump directly into empathizing, reflecting their specific message, and offering a gentle question or grounding reflection.
- Always respond ONLY as Saathi. Do not add any preamble like "Here is Saathi's response:". Just respond directly."""

# ── Topic Classification ───────────────────────────────────────────────────────

TOPICS = {
    "family":   ["mom", "dad", "parent", "family", "arguing", "fight", "mother", "father",
                 "brother", "sister", "relatives", "ghar", "bhai", "behen", "amma", "appa"],
    "academic": ["exam", "marks", "grade", "study", "college", "school", "fail", "score",
                 "career", "future", "job", "interview", "boss", "office", "pariksha", "result"],
    "sleep":    ["sleep", "insomnia", "night", "overthinking", "mind racing", "bed", "awake",
                 "tired", "neend", "raat"],
    "anxiety":  ["anxious", "panic", "scared", "fear", "overwhelmed", "stressed", "stress",
                 "nervous", "worry", "worried", "tension", "ghabra"],
    "lonely":   ["lonely", "alone", "nobody", "isolated", "empty", "sad", "depressed",
                 "unhappy", "akela", "udaas"],
    "positive": ["thank", "thanks", "helpful", "good", "better", "peace", "calm",
                 "appreciate", "relief", "shukriya"],
}

ACTIVITIES = {
    "family":   {"title": "Communicating with Care",      "category": "Guided Reflection",   "duration": "5 min", "action_type": "breathing"},
    "academic": {"title": "Pranayama 4-7-8 Release",      "category": "Anxiety Relief",      "duration": "4 min", "action_type": "breathing"},
    "sleep":    {"title": "Saathi Nighttime Body Scan",   "category": "Sleep Grounding",     "duration": "8 min", "action_type": "breathing"},
    "anxiety":  {"title": "5-4-3-2-1 Sensory Grounding", "category": "Mindfulness",         "duration": "4 min", "action_type": "breathing"},
    "lonely":   {"title": "Mindful Reflection Journal",   "category": "Self-Care Writing",   "duration": "3 min", "action_type": "journal"},
    "positive": {"title": "Gratitude Breathing Space",    "category": "Positive Anchoring",  "duration": "3 min", "action_type": "breathing"},
    "general":  {"title": "Guided 4-7-8 Breath",          "category": "Relaxation",          "duration": "4 min", "action_type": "breathing"},
}

CRISIS_KEYWORDS = [
    "kill myself", "suicide", "want to die", "end my life", "self harm",
    "no reason to live", "end it all", "can't go on", "done with life",
]

FALLBACK_RESPONSES = {
    "family": [
        "It's so tough when the people closest to us don't seem to understand where we're coming from.\n\nFamily dynamics can carry years of unspoken tension, and it's completely natural to feel drained or frustrated. Setting gentle emotional boundaries isn't disrespect—it's an act of quiet self-care.\n\nTell me more about what happened. What do you wish they understood about how you're feeling?",
        "Navigating relationships at home can be genuinely exhausting, especially when expectations and reality keep clashing.\n\nYou deserve to feel heard and valued inside your own home. Sometimes just naming what hurt helps release some of the tightness it creates.\n\nWhat feels most heavy about this situation right now?",
        "Family arguments have this way of leaving a lingering exhaustion long after the words stop.\n\nYou're carrying something real right now. I'm here. Would it help to talk through what triggered things today, or would you rather try a short breathing exercise together to settle your nervous system first?",
    ],
    "academic": [
        "The weight of academic expectations can feel absolutely crushing—especially when it feels like your entire future is riding on a single score or moment.\n\nPlease pause for a second and breathe. Your worth as a human being cannot be measured by any exam result. You are doing your best, and that genuinely matters.\n\nWhat's the most overwhelming part of this pressure for you right now?",
        "Exam stress has this way of making everything feel urgent and impossible all at once. I hear how heavy this is.\n\nRemember—the pressure you feel right now is real, but so is your resilience. You've gotten through difficult things before.\n\nIs it the fear of failing, the expectations from others, or the uncertainty about the future that feels the most suffocating?",
        "Career anxiety in India carries so many layers—family expectations, competition, comparison. It's not just about you, it's about everyone watching.\n\nThat's an enormous weight to carry quietly. Let's unpack it together.\n\nWhat would feel like 'enough' to you, if the pressure from outside disappeared for a moment?",
    ],
    "sleep": [
        "When the world gets quiet at night, our minds often turn up the volume on every unresolved worry.\n\nRacing thoughts at bedtime are your nervous system's way of trying to solve everything at once—but tonight, you don't need to solve anything. You just need to rest.\n\nLet's try something: soften your shoulders, unclench your jaw, and take one slow breath. Can you feel that small release?",
        "Insomnia is so exhausting—not just physically, but emotionally too. Lying awake when your body desperately wants rest is its own kind of suffering.\n\nYou're not alone in this. What kinds of thoughts tend to visit you most when sleep won't come?",
        "It sounds like your mind is working overtime, even when your body is ready to rest.\n\nSometimes our thoughts need a gentle place to land before we can let go. Would it help to do a short body scan together, or would you like to write out the thoughts that are looping?",
    ],
    "anxiety": [
        "I can hear how overwhelming this wave of anxiety feels right now. Anxiety has a way of making everything feel urgent and out of control all at once.\n\nLet's slow down together. Take a breath with me—in through the nose for 4 counts, hold for 7, out through the mouth for 8. You don't have to solve anything in this moment.\n\nWhat does this feeling in your body right now remind you of? When did it start?",
        "That feeling of being overwhelmed—when everything presses in at once—is so real and so valid.\n\nYour nervous system may be reacting as though everything is an emergency. If you can, pause and notice what is around you while taking one slow breath.\n\nWhat's the single biggest thing your mind keeps returning to?",
        "Panic and anxiety are your body's alarm system going off, even when the immediate danger isn't as large as it feels.\n\nYou reached out here, which means part of you knows you can move through this. I'm right here with you.\n\nLet's breathe first, then talk. Can you feel your feet on the ground right now?",
    ],
    "lonely": [
        "Feeling alone—even when surrounded by people—is one of the most quietly painful experiences there is.\n\nI want you to know: you reaching out right now, even here, is a courageous thing. You don't have to carry this in silence.\n\nWhat does this loneliness feel like for you? Is it about not being understood, or more about physical isolation?",
        "Loneliness has layers—sometimes it's about not having people around, and sometimes it's about being around people who still don't really see you.\n\nI see you right now. I'm listening. Your feelings are valid and deeply human.\n\nHas there been a specific moment recently that made the loneliness feel sharper?",
        "That feeling of being unseen or disconnected deserves to be named and held gently.\n\nI'm sitting right here with you. You don't have to pretend to be okay with me.\n\nTell me—when did you last feel truly connected to someone or something? What did that feel like?",
    ],
    "positive": [
        "I'm really glad you're feeling a little lighter. That shift, however small, is worth acknowledging.\n\nWellbeing isn't always about solving big problems—sometimes it's about noticing and honoring these quieter moments of relief.\n\nWhat helped you get to this feeling? I'd love to understand what worked for you.",
        "That's genuinely beautiful to hear. Moments of peace and gratitude are worth pausing and really feeling—don't rush past them.\n\nWhat's one thing you'd like to carry forward from how you're feeling right now?",
    ],
    "general": [
        "Thank you for sharing that with me. Unpacking what we hold inside takes real courage, and I'm honoured you brought it here.\n\nWhatever you're carrying right now—exhaustion, confusion, quiet sadness, or just a feeling you can't name—it's valid. You don't have to explain or justify it.\n\nWhat feels like the most important thing you want me to understand about where you are today?",
        "I'm listening, gently and fully. You don't have to have it all figured out to talk to me—you can think out loud, share fragments, or just describe how your body feels right now.\n\nSometimes the act of saying something out loud to someone who truly listens is itself the beginning of feeling better.\n\nWhat's on your heart today?",
        "It means a lot that you're here. Take your time—there's no pressure to have the right words.\n\nI'm here not to fix or solve, but to sit with you and help you find your own clarity, at your own pace.\n\nWhere would you like to start?",
    ],
}

# ── Utility Functions ──────────────────────────────────────────────────────────

def detect_topic(text: str) -> str:
    lower = text.lower()
    for topic, keywords in TOPICS.items():
        if any(k in lower for k in keywords):
            return topic
    return "general"

def is_crisis(text: str) -> bool:
    from services.negation_service import detect_crisis_intent
    return detect_crisis_intent(text)["is_crisis"]

def get_fallback_reply(topic: str, turn_count: int) -> str:
    pool = FALLBACK_RESPONSES.get(topic, FALLBACK_RESPONSES["general"])
    return pool[turn_count % len(pool)]

def call_gemini_llm(message: str, history: List[ChatMessage], gemini_key: str) -> Optional[str]:
    """
    Call Google Gemini 2.5 Flash via official REST API.
    Lightweight, fast (<1s), warm conversational output.
    """
    try:
        contents = []
        for msg in history[-8:]:
            role = "user" if msg.sender == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800,
                "thinkingConfig": {"thinkingBudget": 0}
            }
        }
        for model in ["gemini-2.5-flash", "gemini-flash-lite-latest"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    # Filter for actual text part (ignore thought parts if any)
                    text_parts = [p.get("text", "") for p in parts if "text" in p and not p.get("thought")]
                    if text_parts:
                        text = "".join(text_parts).strip()
                        if len(text) > 10:
                            return text
                    elif parts and "text" in parts[0]:
                        text = parts[0]["text"].strip()
                        if len(text) > 10:
                            return text
            logger.warning("Gemini %s API returned status %s", model, resp.status_code)
    except Exception as e:
        logger.warning("Gemini API unavailable (%s)", type(e).__name__)
    return None

def call_hf_llm(message: str, history: List[ChatMessage], hf_token: str) -> Optional[str]:
    """
    Call HuggingFace Inference API with proper ChatML prompt format.
    Uses Mistral-7B-Instruct which is fast and reliable on the free HF tier.
    """
    try:
        # Build conversation history in ChatML format
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in history[-8:]:  # last 4 exchanges (8 messages)
            role = "user" if msg.sender == "user" else "assistant"
            messages_payload.append({"role": role, "content": msg.content})

        messages_payload.append({"role": "user", "content": message})

        # Use the Messages API (chat completions style) via HF serverless router
        url = "https://router.huggingface.co/hf-inference/models/mistralai/Mistral-7B-Instruct-v0.2/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "mistralai/Mistral-7B-Instruct-v0.2",
            "messages": messages_payload,
            "max_tokens": 350,
            "temperature": 0.75,
            "top_p": 0.9,
            "stream": False,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=25)

        if resp.status_code == 200:
            data = resp.json()
            # OpenAI-compatible response format
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content and len(content.strip()) > 20:
                return content.strip()

        logger.warning("HF API returned status %s", resp.status_code)

    except requests.Timeout:
        logger.warning("HF API timeout — falling back to rule-based engine")
    except Exception as e:
        logger.warning("HF API unavailable (%s)", type(e).__name__)

    return None

# ── Main Endpoint ──────────────────────────────────────────────────────────────

@router.post("/companion", response_model=ChatResponse)
@limiter.limit("30/minute")
def talk_to_saathi(request: Request, req: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    Saathi (साथी) — Your Wellbeing Companion.
    
    Pipeline:
    1. Crisis safety check (always runs first)
    2. Attempt Gemini 1.5 Flash (if GEMINI_API_KEY is configured)
    3. Attempt Mistral-7B via HF Inference API (if HF_TOKEN is configured)
    4. Fallback to rich multi-turn rule-based engine
    """
    if not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    history = req.history or []
    turn_count = len([m for m in history if m.sender == "user"])
    topic = detect_topic(req.message)

    # ── Step 1: Crisis Safety Check (always first, non-negotiable) ────────────
    if is_crisis(req.message):
        return ChatResponse(
            reply=(
                "I hear how deeply heavy things feel right now, and I want you to know "
                "that your presence in this world matters immensely. You don't have to "
                "carry this weight alone.\n\n"
                "Please reach out to one of these caring professionals right now — "
                "they are available 24/7 and are there specifically for moments like this. "
                "I am right here with you."
            ),
            crisis_flag=True,
            helpline_info=f"{TELE_MANAS} | {ICALL}",
            recommended_activity=RecommendedActivity(
                title="432Hz Calm Sanctuary Breathwork",
                category="Immediate Crisis Grounding",
                duration="5 min",
                action_type="breathing"
            )
        )

    # ── Step 2: Try Gemini API first if configured ───────────────────────────
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None) or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    llm_reply = None
    if gemini_key:
        llm_reply = call_gemini_llm(req.message, history, gemini_key)

    # ── Step 3: Try HuggingFace if Gemini not available or failed ────────────
    if not llm_reply:
        hf_token = settings.HF_TOKEN or os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
        if hf_token:
            llm_reply = call_hf_llm(req.message, history, hf_token)

    # ── Step 3: Fallback to rich rule-based engine ────────────────────────────
    final_reply = llm_reply if llm_reply else get_fallback_reply(topic, turn_count)

    # ── Step 4: Smart activity suggestion — NOT forced every turn ─────────────
    # High-distress topics (anxiety, sleep): offer on first message + every 3 turns.
    # Emotional topics (family, academic, lonely): offer only after turn 1, every 4 turns.
    # General / positive: never push the activity card — let the conversation breathe.
    HIGH_DISTRESS = {"anxiety", "sleep"}
    EMOTIONAL     = {"family", "academic", "lonely"}

    suggest = False
    if topic in HIGH_DISTRESS:
        suggest = (turn_count == 0) or (turn_count % 3 == 0)
    elif topic in EMOTIONAL:
        suggest = (turn_count > 0) and (turn_count % 4 == 0)
    # "general" and "positive" → suggest = False (no card)

    activity_payload = RecommendedActivity(**ACTIVITIES.get(topic, ACTIVITIES["general"])) if suggest else None

    return ChatResponse(
        reply=final_reply,
        companion_name="Saathi",
        tagline="Your wellbeing companion",
        recommended_activity=activity_payload,
        crisis_flag=False,
        helpline_info=None
    )
