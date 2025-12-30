import sys
import os
import traceback

sys.path.append(os.getcwd())

try:
    print("Attempting to import app...")
    from app import get, messages
    print("Imported app successfully.")
    
    print("Checking database...")
    msgs = messages()
    print(f"Found {len(msgs)} messages.")
    
    print("Testing get() route...")
    res = get()
    print("get() route returned successfully.")
    
except Exception as e:
    print(f"Caught exception: {e}")
    traceback.print_exc()
