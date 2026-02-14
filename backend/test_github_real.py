
import asyncio
import os
import sys

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.github import fetch_github_data
from app.core.config import settings

# Force enable real GitHub for this test
settings.USE_REAL_GITHUB = True

async def main():
    test_user = "tiangolo" # Creator of FastAPI
    print(f"--- Testing Real GitHub Fetch for user: {test_user} ---")
    
    url = f"https://github.com/{test_user}"
    summary = await fetch_github_data(url)
    
    print("\n--- Fetched Summary ---")
    print(summary)
    
    if "FastAPI" in summary:
        print("\n[SUCCESS] Found 'FastAPI' in summary.")
    else:
        print("\n[WARNING] 'FastAPI' not found. Check output.")

if __name__ == "__main__":
    asyncio.run(main())
