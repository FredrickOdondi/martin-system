import os
import markdown
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS
from app.core.config import settings

class PDFService:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def generate_agenda_pdf(
        self,
        agenda_markdown: str,
        template_context: Dict[str, Any]
    ) -> bytes:
        """
        Generates a PDF agenda on official letterhead from markdown content.
        """
        # Convert Markdown to HTML
        agenda_html = markdown.markdown(agenda_markdown, extensions=['tables', 'fenced_code'])
        
        # Prepare context
        context = template_context.copy()
        context['agenda_html'] = agenda_html
        
        # Render Template
        template = self.jinja_env.get_template("agenda_pdf.html")
        rendered_html = template.render(**context)
        
        # Convert to PDF
        # Use simple default styling or load extra CSS if needed
        pdf_bytes = HTML(string=rendered_html).write_pdf()
        
        return pdf_bytes

    def generate_minutes_pdf(
        self,
        minutes_markdown: str,
        template_context: Dict[str, Any]
    ) -> bytes:
        """
        Generates a PDF of Meeting Minutes on official letterhead from markdown content.
        """
        # Convert Markdown to HTML
        # Use extensions for tables
        minutes_html = markdown.markdown(minutes_markdown, extensions=['tables', 'fenced_code', 'nl2br'])
        
        # Prepare context
        context = template_context.copy()
        context['minutes_html'] = minutes_html
        
        # Render Template
        template = self.jinja_env.get_template("minutes_pdf.html")
        rendered_html = template.render(**context)
        
        # Convert to PDF
        pdf_bytes = HTML(string=rendered_html).write_pdf()
        
        return pdf_bytes

# Global instance
pdf_service = PDFService()
