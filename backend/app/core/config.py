import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
UPLOADS_DIR = os.path.join(ROOT_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Load .env file into environment
env_file = os.path.join(ROOT_DIR, ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k not in os.environ:
                    os.environ[k] = v


class Settings:
    PROJECT_NAME: str = "PRAGATI AI"
    API_V1_STR: str = "/api"
    raw_db = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(ROOT_DIR, 'pragati_ai.db')}")
    if raw_db.startswith("postgres://"):
        raw_db = raw_db.replace("postgres://", "postgresql://", 1)
    DATABASE_URL: str = raw_db
    
    # AI Provider Settings (auto-detects Gemini/OpenAI if key is present)
    raw_provider = os.getenv("AI_PROVIDER", "").strip().lower()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()

    if raw_provider in ["gemini", "openai", "fallback"]:
        AI_PROVIDER: str = raw_provider
    elif GEMINI_API_KEY:
        AI_PROVIDER: str = "gemini"
    elif OPENAI_API_KEY:
        AI_PROVIDER: str = "openai"
    else:
        AI_PROVIDER: str = "fallback"

    
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
