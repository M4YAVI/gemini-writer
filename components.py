"""
UI Components - Pure inline styles to guarantee it works.
"""
from fasthtml.common import *


def ChatMessage(role: str, content: str):
    """Single chat message bubble."""
    if role == 'user':
        return Div(
            Div(
                content,
                style="background: #2563eb; color: white; padding: 8px 16px; border-radius: 12px; max-width: 500px; word-wrap: break-word;"
            ),
            style="display: flex; justify-content: flex-end; margin-bottom: 12px;"
        )
    else:
        return Div(
            Div(
                content,
                cls="markdown-body",
                style="background: #374151; color: white; padding: 8px 16px; border-radius: 12px; max-width: 500px; word-wrap: break-word;"
            ),
            style="display: flex; justify-content: flex-start; margin-bottom: 12px;"
        )


def LoadingDots(response_id: str):
    """Loading indicator."""
    return Div(
        Div(
            "● ● ●",
            style="color: #34d399; font-size: 14px; letter-spacing: 4px;"
        ),
        Div(id=f"{response_id}-text", cls="markdown-body", style="margin-top: 8px;"),
        style="background: #374151; padding: 12px 16px; border-radius: 12px; max-width: 500px; margin-bottom: 12px;",
        id=response_id
    )


def ChatInput():
    """Chat input form - using table layout for reliable sizing."""
    return Form(
        Div(
            Input(
                type="text",
                name="prompt",
                id="prompt-input",
                placeholder="Type your story idea...",
                style="width: 100%; background: #1f2937; color: white; padding: 12px 16px; border-radius: 8px; border: 1px solid #4b5563; outline: none; font-size: 14px; box-sizing: border-box;"
            ),
            style="flex: 1; min-width: 0;"
        ),
        Button(
            "Send",
            type="submit",
            id="send-btn",
            style="background: #059669; color: white; padding: 12px 24px; border-radius: 8px; border: none; font-weight: 500; cursor: pointer; white-space: nowrap;"
        ),
        style="display: flex; gap: 12px; width: 100%;",
        hx_post="/chat",
        hx_target="#chat-messages",
        hx_swap="beforeend",
        hx_on__after_request="this.reset()",
        hx_disabled_elt="#send-btn"
    )


def Page(chat_messages):
    """Main page layout."""
    return (
        Title("Gemini Writer"),
        
        # Markdown parser
        Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
        Script("""
            function render() {
                document.querySelectorAll('.markdown-body').forEach(el => {
                    if (!el.dataset.done && el.textContent.trim()) {
                        el.innerHTML = marked.parse(el.textContent);
                        el.dataset.done = '1';
                    }
                });
            }
            document.addEventListener('DOMContentLoaded', render);
            document.addEventListener('htmx:afterSwap', render);
        """),
        
        Style("""
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: system-ui, -apple-system, sans-serif; background: #111827; color: white; min-height: 100vh; }
            input:focus { border-color: #059669 !important; }
            button:hover { background: #047857 !important; }
        """),
        
        Body(
            # Header
            Div(
                Div(
                    Span("◈ ", style="color: #34d399; font-size: 20px;"),
                    Span("Gemini Writer", style="font-weight: bold; font-size: 18px;"),
                    style="display: flex; align-items: center;"
                ),
                A("Clear", href="/clear", style="color: #9ca3af; text-decoration: none; font-size: 14px;"),
                style="display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid #1f2937;"
            ),
            
            # Chat area
            Div(
                Div(*chat_messages, id="chat-messages"),
                style="flex: 1; overflow-y: auto; padding: 24px;"
            ),
            
            # Input area
            Div(
                ChatInput(),
                style="padding: 16px 24px; border-top: 1px solid #1f2937;"
            ),
            
            style="display: flex; flex-direction: column; min-height: 100vh;"
        )
    )