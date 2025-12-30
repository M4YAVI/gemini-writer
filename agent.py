"""
PydanticAI Agent for the Short Story Writer.
"""

from __future__ import annotations
import os
import logfire
from typing import Optional, List
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from dotenv import load_dotenv

from tools.project import create_project_impl, get_active_project_folder, set_active_project_folder
from tools.write_file import write_file_impl

# Load environment variables
load_dotenv()

# Configure Logfire for observability if available
try:
    logfire.configure()
except Exception:
    pass

# System Prompt (reused from utils.py but adapted for PydanticAI)
SYSTEM_PROMPT = """You are an elite literary AI agent, modeled after the greatest short story writers in history. Your mission is to write profound, masterful short stories that rival the classics.

**YOUR PERSONA & STYLE**
You channel the combined genius of:
- **Anton Chekhov**: For subtle psychological realism, the "show, don't tell" principle.
- **Guy de Maupassant**: For precision, sharp observation, ironic twists.
- **O. Henry**: For clever plotting and surprise endings.
- **Franz Kafka**: For the surreal, alienation, and existential dread.
- **Ernest Hemingway**: For terse, journalistic prose and deep emotional resonance.
- **Shirley Jackson**: For slow-building psychological horror.

**WRITING GUIDELINES**
1.  **Show, Don't Tell**: Never explain emotions. Describe actions and environments.
2.  **Sensory Detail**: Ground the story in the physical world.
3.  **Economy of Words**: Every sentence must advance the story.
4.  **Distinct Voice**: Adapt your voice based on the user's prompt.
5.  **Subtext**: The most important things are often left unsaid.

**OPERATIONAL CAPABILITIES**
1.  **Project Organization**: Always start by creating a project folder with `create_project` if one hasn't been created for the current request.
2.  **File Management**: Write stories in Markdown (`.md`).
    -   Use `write_file` with mode='create' for new stories.
    -   **ALWAYS** write complete narratives. (3k-10k words).

**COMMAND**: Go forth and write a masterpiece."""

agent = Agent(
    model='google-gla:gemini-3.0-flash',
    system_prompt=SYSTEM_PROMPT,
    deps_type=Optional[str],
)

# --- Tools ---

@agent.tool
def create_project(ctx: RunContext[Optional[str]], project_name: str) -> str:
    """
    Creates a new project folder in the 'output' directory.
    This should be called first before writing any files.
    """
    return create_project_impl(project_name)

@agent.tool
def write_file(ctx: RunContext[Optional[str]], filename: str, content: str, mode: str = "create") -> str:
    """
    Writes content to a markdown file in the active project folder.
    
    Args:
        filename: Name of the file (e.g. 'story.md')
        content: The text content to write.
        mode: 'create', 'append', or 'overwrite'.
    """
    # Ensure we use the active project folder. 
    # In a stateless web req, we might need to restore it from context/session, 
    # but for now rely on the global in tools/project.py or set it via deps.
    
    # Check if a project folder is active in the global state
    current_proj = get_active_project_folder()
    if not current_proj:
         return "Error: No active project folder. Please generate a project first using `create_project`."
         
    return write_file_impl(filename, content, mode)

