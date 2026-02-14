from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
import os
from app.core.schemas import ResumeSchema

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def generate_resume_pdf(resume_data: ResumeSchema) -> bytes:
    template = env.get_template("resume.html")
    
    # Render HTML with data
    html_content = template.render(r=resume_data)
    
    # Generate PDF using WeasyPrint
    # WeasyPrint handles modern CSS (flexbox, etc.) much better than xhtml2pdf
    pdf_bytes = HTML(string=html_content).write_pdf()
        
    return pdf_bytes
