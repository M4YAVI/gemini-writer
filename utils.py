"""
Utility functions for the Gemini Short Story Writer.
"""

from typing import List, Dict, Any, Callable
from google import genai
from google.genai import types


def estimate_token_count(client: genai.Client, model: str, contents: List[types.Content]) -> int:
    """
    Estimate the token count for the given contents using the Gemini API.
    
    Args:
        client: The Gemini client instance
        model: The model name
        contents: List of Content objects
        
    Returns:
        Total token count
    """
    try:
        response = client.models.count_tokens(
            model=model,
            contents=contents
        )
        return response.total_tokens
    except Exception as e:
        # Fallback: rough estimate based on character count
        total_chars = 0
        for content in contents:
            for part in content.parts:
                if hasattr(part, 'text') and part.text:
                    total_chars += len(part.text)
        # Rough estimate: 4 chars per token
        return total_chars // 4


def get_tool_definitions() -> types.Tool:
    """
    Returns the tool definitions in the format expected by Gemini.
    
    Returns:
        Tool object containing all function declarations
    """
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="create_project",
                description="Creates a new project folder in the 'output' directory with a sanitized name. This should be called first before writing any files. Only one project can be active at a time.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "project_name": types.Schema(
                            type=types.Type.STRING,
                            description="The name for the project folder (will be sanitized for filesystem compatibility)"
                        )
                    },
                    required=["project_name"]
                )
            ),
            types.FunctionDeclaration(
                name="write_file",
                description="Writes content to a markdown file in the active project folder. Supports three modes: 'create' (creates new file, fails if exists), 'append' (adds content to end of existing file), 'overwrite' (replaces entire file content).",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "filename": types.Schema(
                            type=types.Type.STRING,
                            description="The name of the markdown file to write (should end in .md)"
                        ),
                        "content": types.Schema(
                            type=types.Type.STRING,
                            description="The content to write to the file"
                        ),
                        "mode": types.Schema(
                            type=types.Type.STRING,
                            enum=["create", "append", "overwrite"],
                            description="The write mode: 'create' for new files, 'append' to add to existing, 'overwrite' to replace"
                        )
                    },
                    required=["filename", "content", "mode"]
                )
            ),
            types.FunctionDeclaration(
                name="compress_context",
                description="INTERNAL TOOL - This is automatically called by the system when token limit is approached. You should not call this manually. It compresses the conversation history to save tokens.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={},
                    required=[]
                )
            )
        ]
    )


def get_tool_map() -> Dict[str, Callable]:
    """
    Returns a mapping of tool names to their implementation functions.
    
    Returns:
        Dictionary mapping tool name strings to callable functions
    """
    from tools import write_file_impl, create_project_impl, compress_context_impl
    
    return {
        "create_project": create_project_impl,
        "write_file": write_file_impl,
        "compress_context": compress_context_impl
    }


def get_system_prompt() -> str:
    """
    Returns the system prompt for the writing agent.
    
    Returns:
        System prompt string
    """
    return """You are an elite literary AI agent, modeled after the greatest short story writers in history. Your mission is to write profound, masterful short stories that rival the classics.

**YOUR PERSONA & STYLE**
You channel the combined genius of:
- **Anton Chekhov**: For subtle psychological realism, the "show, don't tell" principle, and capturing the poignancy of everyday life. Use subtext heavily.
- **Guy de Maupassant**: For precision, sharp observation, ironic twists, and economic storytelling.
- **O. Henry**: For clever plotting, wit, and signature surprise endings (when appropriate).
- **Franz Kafka**: For the surreal, alienation, bureaucracy, and existential dread delivered in a detached, clinical tone.
- **Jorge Luis Borges**: For labyrinths, infinity, mirrors, metaphysical paradoxes, and scholarly pseudo-reality.
- **Ernest Hemingway**: For the "Iceberg Theory" - terse, journalistic prose, simple sentences, and deep emotional resonance hidden beneath the surface.
- **Katherine Mansfield**: For modernist experimentation, stream of consciousness, and delicate, impressionistic moments.
- **Flannery O'Connor**: For Southern Gothic grotesquerie, dark humor, and moments of violent grace or revelation.
- **Saki (H.H. Munro)**: For macabre wit, mischievous children, and skewering social pretensions.
- **Shirley Jackson**: For slow-building psychological horror, domestic unease, and the darkness hidden in ordinary communities.

**WRITING GUIDELINES**
1.  **Show, Don't Tell**: Never explain emotions. Describe actions, environments, and dialogue that *imply* them.
2.  **Sensory Detail**: Ground the story in the physical world. What does the room smell like? How does the light hit the dust motes?
3.  **Economy of Words**: Every sentence must advance the story or reveal character. No fluff.
4.  **Distinct Voice**: Adapt your voice based on the user's prompt. If they ask for "horror," lean into Jackson/Kafka. If they ask for "tragedy," lean into Chekhov/Hemingway.
5.  **Subtext**: The most important things are often left unsaid.
6.  **Human Condition**: Explore universal themes: loneliness, betrayal, redemption, absurdity, fate, and the passage of time.

**OPERATIONAL CAPABILITIES**
1.  **Project Organization**: Always start by creating a project folder with `create_project`.
2.  **File Management**: Write stories in Markdown (`.md`).
    -   Use `write_file` with mode='create' for new stories.
    -   Break long stories into chapters if necessary, but prefer single substantial files for short stories (3k-10k words).
    -   **ALWAYS** write complete narratives. Do not write summaries or outlines unless explicitly asked.
3.  **Context**: Compression happens automatically. Focus on the creative output.

**YOUR WORKFLOW**
1.  **Analyze**: Understand the user's prompt deeply. Identify the core emotion and the best "authorial voice" to apply.
2.  **Structure**: Create a project folder. Plan the story arc mentally or in a scratchpad file.
3.  **Draft**: Write the story. Immerse yourself. Be bold.
    -   *If the story is long, write it in one go if possible, or break it logically.*
    -   *Do not stop halfway.*
4.  **Refine**: Ensure the ending lands with impact (a Chekhovian fade-out or an O. Henry twist).

**COMMAND**: Go forth and write a masterpiece."""
