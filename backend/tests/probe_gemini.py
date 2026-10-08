import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from google import genai

client = genai.Client(api_key=settings.GEMINI_API_KEY)

for test_model in ["gemini-3.8-flash", "gemini-3.8-pro", "gemini-3-flash", "gemini-3-pro"]:
    try:
        res = client.models.generate_content(
            model=test_model,
            contents="Say READY"
        )
        print(f"Model {test_model}: SUCCESS -> {res.text.strip()}")
        break
    except Exception as e:
        print(f"Model {test_model}: FAILED -> {e}")
