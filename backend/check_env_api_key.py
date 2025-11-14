#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check API Key from .env file
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from multiple possible locations
env_paths = [
    Path(__file__).parent / '.env',  # backend/.env
    Path(__file__).parent.parent / '.env',  # root/.env
]

print("=" * 60)
print("CHECKING API KEY FROM .ENV")
print("=" * 60)

for env_path in env_paths:
    if env_path.exists():
        print(f"\n[FOUND] .env file at: {env_path}")
        load_dotenv(env_path)
        break
else:
    print("\n[WARNING] No .env file found in expected locations")
    print("Trying to load from current directory...")
    load_dotenv()

# Get API key
api_key = os.getenv('GOOGLE_CSE_API_KEY')
api_key_alt = os.getenv('GOOGLE_API_KEY')  # Alternative name

print("\n" + "-" * 60)
print("ENVIRONMENT VARIABLES:")
print("-" * 60)

if api_key:
    print(f"GOOGLE_CSE_API_KEY: {api_key[:20]}...{api_key[-10:] if len(api_key) > 30 else ''}")
    print(f"Length: {len(api_key)} characters")
else:
    print("GOOGLE_CSE_API_KEY: NOT FOUND")

if api_key_alt:
    print(f"GOOGLE_API_KEY: {api_key_alt[:20]}...{api_key_alt[-10:] if len(api_key_alt) > 30 else ''}")
    print(f"Length: {len(api_key_alt)} characters")

# Use the first available key
final_key = api_key or api_key_alt

if final_key:
    print("\n" + "=" * 60)
    print(f"[OK] API Key found: {final_key[:30]}...")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print("[ERROR] No API key found in environment variables!")
    print("\nPlease check:")
    print("  1. File .env exists in backend/ or root/")
    print("  2. Contains: GOOGLE_CSE_API_KEY=your_api_key_here")
    print("=" * 60)



