"""
FastAPI Story Writer App - Premium Edition.
"""
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import sqlite3
import os
import json

from agent import create_agent, load_settings, save_settings, MODELS

# Setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database
DB_PATH = "data/chat_history.db"
os.makedirs("data", exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = get_db()
    messages = conn.execute("SELECT * FROM messages ORDER BY id").fetchall()
    conn.close()
    settings = load_settings()
    # Pass models directly to template, but we will also expose API
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "messages": messages,
        "settings": settings,
        "models": MODELS # Passing for server-side render if needed
    })


@app.get("/api/models")
async def get_models():
    """Return available models for frontend."""
    return JSONResponse(MODELS)


@app.get("/app/settings")
async def get_settings_api():
    """Return settings for frontend."""
    return JSONResponse(load_settings())


@app.get("/clear")
async def clear():
    conn = get_db()
    conn.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)


@app.post("/api/settings")
async def update_settings(
    provider: str = Form(...),
    model: str = Form(...),
    openrouter_api_key: str = Form(""),
    gemini_api_key: str = Form("")
):
    settings = {
        "provider": provider,
        "model": model,
        "openrouter_api_key": openrouter_api_key,
        "gemini_api_key": gemini_api_key
    }
    save_settings(settings)
    return RedirectResponse(url="/", status_code=303)


@app.post("/chat")
async def chat(prompt: str = Form(...)):
    # Save user message
    conn = get_db()
    conn.execute(
        "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
        ("user", prompt, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    async def stream():
        full_text = ""
        try:
            agent = create_agent()
            async with agent.run_stream(prompt) as result:
                async for chunk in result.stream_text(delta=True):
                    full_text += chunk
                    yield chunk
            
            # Save AI response
            if full_text:
                conn = get_db()
                conn.execute(
                    "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
                    ("assistant", full_text, datetime.now().isoformat())
                )
                conn.commit()
                conn.close()
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            yield error_msg
            conn = get_db()
            conn.execute(
                "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
                ("assistant", error_msg, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()

    return StreamingResponse(stream(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
