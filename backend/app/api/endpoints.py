from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import Response
from app.core.schemas import AnalyzeRequest, ResumeSchema
from app.services.llm import analyze_profiles
from app.services.pdf import generate_resume_pdf
from app.services.github import fetch_github_data
from app.core.config import settings

router = APIRouter()

# Mock Data for initial testing (since we don't have real scrapers yet)
MOCK_GITHUB = "Top Repo: resume-gen-ai using Python, FastAPI."

@router.post("/analyze", response_model=ResumeSchema)
async def analyze_profiles_endpoint(request: AnalyzeRequest):
    try:
        if not request.github_url and not request.manual_experience:
             raise HTTPException(status_code=400, detail="At least one input source (GitHub or Manual Experience) is required")

        # GitHub Data
        github_data = ""
        if request.github_url:
             try:
                github_data = await fetch_github_data(str(request.github_url))
             except Exception as e:
                print(f"GitHub Error: {e}")
                
        if not github_data and not request.manual_experience:
             raise HTTPException(status_code=400, detail="Could not fetch data from GitHub and no manual experience provided.")

        resume = await analyze_profiles(
            github_data,
            request.manual_experience,
            request.manual_education,
            request.manual_highlights,
            request.is_student,
            request.linkedin_url,
            request.email,
            request.phone
        )
        return resume
    except Exception as e:
        print(f"Error in analyze_profiles_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate_pdf")
async def generate_pdf_endpoint(resume_data: ResumeSchema):
    try:
        pdf_bytes = generate_resume_pdf(resume_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=resume.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF Generation failed: {str(e)}")
