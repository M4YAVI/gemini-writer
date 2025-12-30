import os
import sys

# Add current dir to path so we can import agent
sys.path.append(os.getcwd())

try:
    from agent import agent
    print("Agent initialized successfully.")
except Exception as e:
    print(f"Agent initialization failed: {e}")
