"""
FastAPI App with plain HTML/CSS.
"""
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import sqlite3
import os

from agent import agent

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
    return templates.TemplateResponse("index.html", {"request": request, "messages": messages})


@app.get("/clear")
async def clear():
    conn = get_db()
    conn.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
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
            async with agent.run_stream(prompt) as result:
                async for chunk in result.stream_text(delta=True):
                    full_text += chunk
                    yield chunk
            
            # Save AI response
            conn = get_db()
            conn.execute(
                "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
                ("assistant", full_text, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            yield f"\n\nError: {str(e)}"

    return StreamingResponse(stream(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
