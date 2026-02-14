from typing import List, Optional
from pydantic import BaseModel, HttpUrl, EmailStr

# --- Input Models ---
class ManualExperienceItem(BaseModel):
    company: str
    role: str
    duration: str
    description: str  # Raw description to be refined by LLM

class EducationItem(BaseModel):
    institution: str
    degree: str
    duration: str
    details: Optional[List[str]] = None
    gpa: Optional[str] = None
    coursework: Optional[List[str]] = []
    honors: Optional[List[str]] = []

class AnalyzeRequest(BaseModel):
    github_url: Optional[HttpUrl] = None
    linkedin_url: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    manual_experience: List[ManualExperienceItem] = []
    manual_education: List[EducationItem] = []
    manual_highlights: List[str] = []
    is_student: bool = False

class PersonalInfo(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

class ExperienceItem(BaseModel):
    company: str
    role: str
    duration: str
    location: Optional[str] = None
    bullets: List[str]

class ProjectItem(BaseModel):
    name: str
    technologies: List[str]
    description: str
    link: Optional[str] = None

class ResumeSchema(BaseModel):
    personal_info: PersonalInfo
    summary: str
    highlights: Optional[List[str]] = []
    experience: List[ExperienceItem]
    projects: List[ProjectItem]
    education: List[EducationItem]
    skills: List[str]
    is_student: bool = False  # Pass through for template rendering
