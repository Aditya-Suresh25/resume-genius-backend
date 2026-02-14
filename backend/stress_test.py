
import asyncio
import os
import json
import sys
from app.mock_data import MOCK_PROFILES
from app.services.llm import analyze_profiles
from app.services.pdf import generate_resume_pdf
from app.core.schemas import ResumeSchema

# Add parent dir to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUTPUT_DIR = "test_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def test_profile(name, data):
    print(f"\n--- Testing Profile: {name.upper()} ---")
    
    # 1. Test LLM Generation (Mock or Real)
    print("1. Generating JSON from LLM...")
    try:
        # Check if API key is present
        if not os.getenv("GEMINI_API_KEY"):
            print("SKIPPING LLM: No GEMINI_API_KEY found. Using fallback mock JSON if available.")
            # For now, we fail if no key, because the user wants to stress test LLM.
            # But to be useful without key, let's create a dummy schema here if needed?
            # No, let's just error out or return.
            print("Please set GEMINI_API_KEY to test LLM generation.")
            return
            
        resume_schema = await analyze_profiles(data["linkedin"], data["github"])
        
        json_path = os.path.join(OUTPUT_DIR, f"{name}.json")
        with open(json_path, "w") as f:
            f.write(resume_schema.model_dump_json(indent=2))
        print(f"   JSON saved to {json_path}")
        
    except Exception as e:
        print(f"!! LLM FAILURE: {e}")
        return

    # 2. Test PDF Generation
    print("2. Generating PDF...")
    try:
        pdf_bytes = generate_resume_pdf(resume_schema)
        pdf_path = os.path.join(OUTPUT_DIR, f"{name}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"   PDF saved to {pdf_path}")
    except Exception as e:
        print(f"!! PDF FAILURE: {e}")

async def main():
    if not os.path.exists("backend"):
        # simple check if running from root or backend
        if os.path.exists("app"):
            pass # running inside backend
        else:
             print("Please run this script from the 'backend' directory or ensure paths are correct.")

    for profile_name, data in MOCK_PROFILES.items():
        await test_profile(profile_name, data)

if __name__ == "__main__":
    # Load env vars if managing via dotenv in script (optional, but good for local run)
    from app.core.config import settings
    # settings are already loaded by app.core.config import, checking key
    if not settings.GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY not set. LLM calls will fail.")
    
    asyncio.run(main())
