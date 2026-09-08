import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
UPLOADS_DIR = os.path.join(ROOT_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

class Settings:
    PROJECT_NAME: str = "PRAGATI AI"
    API_V1_STR: str = "/api"
    raw_db = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(ROOT_DIR, 'pragati_ai.db')}")
    if raw_db.startswith("postgres://"):
        raw_db = raw_db.replace("postgres://", "postgresql://", 1)
    DATABASE_URL: str = raw_db
    
    # AI Provider Settings
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "fallback")  # "fallback" or "gemini" or "openai"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Matching Engine Weights
    WEIGHT_SEMANTIC: float = float(os.getenv("WEIGHT_SEMANTIC", "0.50"))
    WEIGHT_DISCIPLINE: float = float(os.getenv("WEIGHT_DISCIPLINE", "0.15"))
    WEIGHT_ENTITY: float = float(os.getenv("WEIGHT_ENTITY", "0.15"))
    WEIGHT_LOCATION: float = float(os.getenv("WEIGHT_LOCATION", "0.10"))
    WEIGHT_TEMPORAL: float = float(os.getenv("WEIGHT_TEMPORAL", "0.10"))
    
    # Confidence Routing Thresholds
    THRESHOLD_HIGH: float = float(os.getenv("THRESHOLD_HIGH", "0.70"))
    THRESHOLD_MEDIUM: float = float(os.getenv("THRESHOLD_MEDIUM", "0.48"))
    THRESHOLD_UNMATCHED: float = float(os.getenv("THRESHOLD_UNMATCHED", "0.32"))
    MARGIN_HIGH_CONFIDENCE: float = float(os.getenv("MARGIN_HIGH_CONFIDENCE", "0.08"))

settings = Settings()
