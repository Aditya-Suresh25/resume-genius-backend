from google import genai
from google.genai import types
from app.core.config import settings
from app.core.schemas import ResumeSchema
from fastapi import HTTPException
import logging
from pydantic import ValidationError

logger = logging.getLogger(__name__)

# Initialize the new Client
# Note: We don't configure the model globally anymore; we pass config per call.
client = genai.Client(api_key=settings.GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are an expert Resume Writer. Your Goal: Produce a high-impact, single-page resume.

CRITICAL SINGLE-PAGE CONSTRAINTS:
1. **Summary:** MAX 50 words. Strict.
2. **Experience:** Include MAX 3 most relevant roles. MAX 3 bullets per role.
3. **Projects:** Include MAX 3 projects. MAX 2 bullets per project.
4. **Highlights:** MAX 2 bullets.
5. **Skills:** Dense format. One line per category. MAX 4 categories.

CONTENT RULES:
1. **Active Voice:** Use strong action verbs (Engineered, Deployed). No passive voice.
2. **No Fluff:** Remove generic adjectives ("passionate", "hardworking"). Focus on tech and impact.
3. **Truth:** Do NOT invent metrics or facts. Infer skills from repo data if needed.

Output MUST be valid JSON matching the schema.
"""

async def analyze_profiles(github_data: str, manual_experience: list = [], manual_education: list = [], manual_highlights: list = [], is_student: bool = False, linkedin_url: str = None, email: str = None, phone: str = None) -> ResumeSchema:
    
    manual_exp_str = ""
    if manual_experience:
        manual_exp_str = "MANUAL EXPERIENCE INPUT:\n" + "\n".join(
            [f"- Company: {m.company}, Role: {m.role}, Duration: {m.duration}, Details: {m.description}" for m in manual_experience]
        )

    manual_edu_str = ""
    if manual_education:
        manual_edu_str = "MANUAL EDUCATION INPUT (Use this heavily, refine wording but keep facts):\n" + "\n".join(
            [f"- School: {e.institution}, Degree: {e.degree}, Time: {e.duration}, GPA: {e.gpa}, Courses: {e.coursework}, Honors: {e.honors}" for e in manual_education]
        )

    manual_highlights_str = ""
    if manual_highlights:
        manual_highlights_str = "MANUAL HIGHLIGHTS INPUT (Refine clarity, keep to 3-4 bullets):\n" + "\n".join(
            [f"- {h}" for h in manual_highlights]
        )

    student_focus = ""
    if is_student:
        student_focus = """
        IMPORTANT - STUDENT MODE ACTIVE:
        1. prioritize EDUCATION and ACADEMIC PROJECTS over professional experience if the latter is sparse.
        2. Ensure the summary mentions "Student" or "Aspiring Software Engineer".
        3. If professional experience is missing, infer "Experience" from major academic projects or open source contributions if applicable, OR leave Experience empty.
        4. Include Coursework in the Education section if provided.
        """
    else:
        student_focus = "PROFESSIONAL MODE: Prioritize Work Experience."

    prompt = f"""
    RAW GITHUB DATA:
    {github_data}
    
    {manual_exp_str}
    {manual_edu_str}
    {manual_highlights_str}
    
    CONTEXT:
    {student_focus}
    
    Extract and synthesize the resume data in the required JSON format.
    If manual experience/education/highlights are provided, INTEGRATE them.
    Refine wording for clarity and impact, but DO NOT invent facts or metrics.
    """
    
    retries = 3
    for attempt in range(retries):
        try:
            # New SDK Async Call
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash',  # Updated to valid model version
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                    top_k=40,
                    response_mime_type='application/json',
                    response_schema=ResumeSchema  # Pass Pydantic class directly for strict validation
                )
            )

            # Log raw response for debugging (only if enabled)
            if settings.DEBUG:
                logger.info(f"Gemini Response: {response.text}")
            
            # The new SDK automatically validates and parses the JSON into your Pydantic model
            # Access it via response.parsed
            if not response.parsed:
                raise ValueError("Empty response or failed parsing from Gemini")
            
            # Enforce is_student from input, independent of LLM's interpretation
            response.parsed.is_student = is_student
            
            # Enforce linkedin from input, independent of LLM's generation
            if linkedin_url:
                response.parsed.personal_info.linkedin = linkedin_url

            # Enforce email and phone if provided
            if email:
                response.parsed.personal_info.email = email
            if phone:
                response.parsed.personal_info.phone = phone

            # --- HARD CONSTRAINT ENFORCEMENT ---
            # Ensure single page by truncating lists if LLM ignores prompt
            
            # Max 3 Experience roles
            if response.parsed.experience:
                response.parsed.experience = response.parsed.experience[:3]
                for item in response.parsed.experience:
                    # Max 3 bullets per role
                    if item.bullets:
                        item.bullets = item.bullets[:3]

            # Max 3 Projects
            if response.parsed.projects:
                response.parsed.projects = response.parsed.projects[:3]
                # Note: Project description is a single string, so we trust the prompt for length.

            # Max 2 Highlights
            if response.parsed.highlights:
                response.parsed.highlights = response.parsed.highlights[:2]

            # Max 4 Skill Categories (Dense format)
            if response.parsed.skills:
                response.parsed.skills = response.parsed.skills[:4]

            return response.parsed

        except (ValidationError, ValueError) as e:
            logger.error(f"Validation/Parsing Error (Attempt {attempt+1}): {e}")
            if attempt == retries - 1:
                raise HTTPException(status_code=500, detail=f"LLM structure failed: {str(e)}")
        except Exception as e:
            logger.error(f"GenAI API Error (Attempt {attempt+1}): {e}")
            if attempt == retries - 1:
                raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")
    
    raise HTTPException(status_code=500, detail="LLM generation failed after retries")