#!/usr/bin/env python3
"""
Gemini Short Story Writer - "Classic Authors Edition"

An autonomous agent that writes short stories in the style of literature's masters.
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import List, Dict, Any, Union

# Load environment variables from .env file
load_dotenv()

from utils import (
    estimate_token_count, 
    get_tool_definitions, 
    get_tool_map,
    get_system_prompt,
)
from tools.compression import compress_context_impl


# Constants
MAX_ITERATIONS = 300
TOKEN_LIMIT = 1000000  # Gemini has 1M context window
COMPRESSION_THRESHOLD = 900000  # Trigger compression at 90% of limit
MODEL_NAME = "gemini-2.0-flash-exp" # Using the latest available model
BACKUP_INTERVAL = 50  # Save backup summary every N iterations


def load_context_from_file(file_path: str) -> str:
    """
    Loads context from a summary file for recovery.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✓ Loaded context from: {file_path}\n")
        return content
    except Exception as e:
        print(f"✗ Error loading context file: {e}")
        sys.exit(1)


def get_user_input() -> tuple[str, bool]:
    """
    Gets user input from command line, either as a prompt or recovery file.
    """
    parser = argparse.ArgumentParser(
        description="Gemini Short Story Writer - Classic Authors Style",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start writing a story
  python kimi-writer.py "Write a story about a lost letter in the style of Chekhov"
  
  # Recover from a previous session
  python kimi-writer.py --recover .context_summary_20250107_143022.md
        """
    )
    
    parser.add_argument(
        'prompt',
        nargs='?',
        help='Your writing request (e.g., "A ghost story set in a library")'
    )
    parser.add_argument(
        '--recover',
        type=str,
        help='Path to a context summary file to continue from'
    )
    
    args = parser.parse_args()
    
    if args.recover:
        context = load_context_from_file(args.recover)
        return context, True
    
    if args.prompt:
        return args.prompt, False
    
    print("=" * 60)
    print("Gemini Short Story Writer - Classic Authors Edition")
    print("=" * 60)
    print("\nEnter your story idea (or 'quit' to exit):")
    
    prompt = input("> ").strip()
    
    if prompt.lower() in ['quit', 'exit', 'q']:
        print("Goodbye!")
        sys.exit(0)
    
    if not prompt:
        print("Error: Empty prompt.")
        sys.exit(1)
    
    return prompt, False


def main():
    """Main agent loop."""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please create a .env file with GEMINI_API_KEY='your-key-here'")
        sys.exit(1)
    
    client = genai.Client(api_key=api_key)
    print(f"✓ Gemini client initialized\n")
    
    user_prompt, is_recovery = get_user_input()
    
    contents: List[types.Content] = []
    
    if is_recovery:
        initial_message = f"[RECOVERED CONTEXT]\n\n{user_prompt}\n\n[END RECOVERED CONTEXT]\n\nPlease continue the work from where we left off."
        print("🔄 Recovery mode: Continuing from previous context\n")
    else:
        initial_message = user_prompt
        print(f"\n📝 Request: {user_prompt}\n")
    
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=initial_message)]
    ))
    
    tools = get_tool_definitions()
    tool_map = get_tool_map()
    system_instruction = get_system_prompt()
    
    print("=" * 60)
    print("Starting Writing Session")
    print("=" * 60)
    
    # Main agent loop
    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n{'─' * 60}")
        print(f"Iteration {iteration}/{MAX_ITERATIONS}")
        
        # Token Management
        try:
            token_count = estimate_token_count(client, MODEL_NAME, contents)
            # print(f"📊 Tokens: {token_count:,}/{TOKEN_LIMIT:,}")
            
            if token_count >= COMPRESSION_THRESHOLD:
                print(f"\n⚠️  Compressing context...")
                simple_messages = []
                for content in contents:
                    role = content.role
                    text_parts = []
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    if text_parts:
                        simple_messages.append({"role": role, "content": " ".join(text_parts)})
                
                compression_result = compress_context_impl(
                    messages=[{"role": "system", "content": system_instruction}] + simple_messages,
                    client=client,
                    model=MODEL_NAME,
                    keep_recent=10
                )
                
                if "compressed_messages" in compression_result:
                    new_contents = []
                    for msg in compression_result["compressed_messages"]:
                        if msg.get("role") == "system":
                            continue
                        role = "model" if msg.get("role") in ["assistant", "model"] else "user"
                        if msg.get("content"):
                            new_contents.append(types.Content(
                                role=role,
                                parts=[types.Part.from_text(text=msg["content"])]
                            ))
                    contents = new_contents
                    print(f"✓ Context compressed.")
        
        except Exception as e:
            # print(f"⚠️  Token check skipped: {e}")
            pass
        
        # Generation Config
        generate_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[tools],
            temperature=1.0, 
        )
        
        # Call Model
        try:
            print("🤖 Writing/Thinking...\n")
            
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=generate_config,
            )
            
            thinking_text = ""
            content_text = ""
            function_calls_list = []
            
            model_content = None
            if response.candidates and response.candidates[0].content:
                model_content = response.candidates[0].content
                
                for part in model_content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        function_calls_list.append({
                            "name": fc.name,
                            "args": dict(fc.args) if fc.args else {}
                        })
                    elif hasattr(part, 'text') and part.text:
                        content_text += part.text
            
            if content_text:
                print("💬 Response:")
                print("-" * 60)
                print(content_text)
                print("-" * 60 + "\n")
            
            # Save context
            if model_content:
                contents.append(model_content)
            
            # Use Function Calls
            if function_calls_list:
                print(f"🔧 Calling tools: {[fc['name'] for fc in function_calls_list]}")
                
                function_response_parts = []
                
                for fc in function_calls_list:
                    func_name = fc["name"]
                    args = fc["args"]
                    tool_func = tool_map.get(func_name)
                    
                    if not tool_func:
                        result = f"Error: Unknown tool '{func_name}'"
                    else:
                        if func_name == "compress_context":
                            # Complex handling for compression tool calling itself (rare but possible)
                             result = "Context compression managed by system." 
                        else:
                            result = tool_func(**args)
                    
                    if len(str(result)) > 200:
                        print(f"    ✓ {func_name}: {str(result)[:200]}...")
                    else:
                        print(f"    ✓ {func_name}: {result}")
                    
                    function_response_parts.append(
                        types.Part.from_function_response(
                            name=func_name,
                            response={"result": str(result)}
                        )
                    )
                
                contents.append(types.Content(
                    role="user",
                    parts=function_response_parts
                ))
            else:
                # No tool calls = Done (usually)
                print("=" * 60)
                print("✅ Session Paused (Waiting for user input)")
                print("=" * 60)
                
                # Allow user to continue the conversation
                new_prompt = input("\nContinue (enter reply) or Quit (q): ").strip()
                if new_prompt.lower() in ['q', 'quit', 'exit']:
                    break
                
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=new_prompt)]
                ))
                
        except KeyboardInterrupt:
            print("\nSaved & Exiting.")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    main()
