"""
Simple Story Writer Agent - No tools, just clean chat.
"""

from __future__ import annotations
import os
import json
from typing import Optional
from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()

# Settings file
SETTINGS_FILE = "data/settings.json"

def load_settings():
    """Load settings from JSON file."""
    os.makedirs("data", exist_ok=True)
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {
        "provider": "openrouter",
        "model": "xiaomi/mimo-v2-flash:free",
        "openrouter_api_key": "",
        "gemini_api_key": os.getenv("GEMINI_API_KEY", "")
    }

def save_settings(settings: dict):
    """Save settings to JSON file."""
    os.makedirs("data", exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

# Available models
MODELS = {
    "openrouter": [
        {"id": "xiaomi/mimo-v2-flash:free", "name": "Xiaomi MiMo v2 Flash (Free)"},
        {"id": "google/gemini-2.0-flash-exp:free", "name": "Gemini 2.0 Flash (Free)"},
        {"id": "deepseek/deepseek-chat-v3-0324:free", "name": "DeepSeek Chat v3 (Free)"},
        {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B (Free)"},
    ],
    "gemini": [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
        {"id": "gemini-3.0-flash", "name": "Gemini 3.0 Flash"},
    ]
}

SYSTEM_PROMPT = """You are an elite literary AI, a master short story writer. Write vivid, emotionally resonant stories.

Guidelines:
- Show, don't tell. Use sensory details.
- Every sentence must advance the story.
- Create memorable characters with distinct voices.
- Endings should be impactful - surprising or poignant.

When asked to write a story, write the COMPLETE story directly. No outlines, no asking for clarification - just write the story immediately.

Format stories in clean Markdown with a title."""


def create_agent():
    """Create agent with current settings."""
    settings = load_settings()
    
    provider = settings.get("provider", "openrouter")
    model = settings.get("model", "xiaomi/mimo-v2-flash:free")
    
    # Set API key
    if provider == "openrouter":
        api_key = settings.get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY", "")
        if api_key:
            os.environ["OPENROUTER_API_KEY"] = api_key
        model_str = f"openrouter:{model}"
    else:
        api_key = settings.get("gemini_api_key") or os.getenv("GEMINI_API_KEY", "")
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
        model_str = f"google-gla:{model}"
    
    return Agent(
        model=model_str,
        system_prompt=SYSTEM_PROMPT,
    )
