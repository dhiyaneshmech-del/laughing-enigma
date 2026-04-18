import os
import sqlite3
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BACKEND_DIR)
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

DB_FILE = os.path.join(BASE_DIR, "survey.db")

# Pydantic model for validation
class SurveyEntry(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    party: str = Field(..., min_length=1, max_length=100)
    probability: int = Field(..., ge=0, le=100)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            party TEXT NOT NULL,
            probability INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

async def send_telegram_notification(entry: SurveyEntry):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Telegram credentials not configured. Skipping notification.")
        return

    message = (
        f"🗳️ *New Survey Entry*\n\n"
        f"👤 *Name:* {entry.name}\n"
        f"📧 *Email:* {entry.email}\n"
        f"🏛️ *Favorite Party:* {entry.party}\n"
        f"📈 *Win Probability:* {entry.probability}%"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/submit-survey")
async def submit_survey(entry: SurveyEntry, background_tasks: BackgroundTasks):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO surveys (name, email, party, probability) VALUES (?, ?, ?, ?)",
            (entry.name, entry.email, entry.party, entry.probability)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Send Telegram notification in background
    background_tasks.add_task(send_telegram_notification, entry)

    return {"status": "success", "message": "Survey submitted successfully!"}

# Mount the static files directory
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
os.makedirs(FRONTEND_DIR, exist_ok=True)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
