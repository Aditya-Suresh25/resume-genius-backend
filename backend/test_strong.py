
import asyncio
import os
import sys
# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.mock_data import MOCK_PROFILES
from stress_test import test_profile

async def main():
    print("Running TARGETED test for STRONG profile...")
    if "strong" in MOCK_PROFILES:
        await test_profile("strong", MOCK_PROFILES["strong"])
    else:
        print("Error: 'strong' profile not found in mock data.")

if __name__ == "__main__":
    asyncio.run(main())
