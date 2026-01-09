import os
from typing import Optional
from jinja2 import Environment, FileSystemLoader
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from datetime import datetime
import io

class FormatService:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(self.template_dir))
        
    def generate_pdf(
        self,
        title: str,
        content: str,
        footer: Optional[str] = "ECOWAS Summit 2026 Official Document"
    ) -> bytes:
        """
        Generates a branded PDF from text/markdown content.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1 # Center
        )
        
        body_style = styles['BodyText']
        
        elements = []
        
        # Add Header (Placeholder for logo)
        elements.append(Paragraph("<b>ECOWAS Economic Integration & Investment Summit 2026</b>", title_style))
        elements.append(Spacer(1, 12))
        
        # Add Document Title
        elements.append(Paragraph(f"<u>{title}</u>", styles['Heading2']))
        elements.append(Paragraph(f"Date Generated: {datetime.now().strftime('%Y-%m-%d')}", styles['Italic']))
        elements.append(Spacer(1, 24))
        
        # Add Content (Splitting by lines for simplicity, ideally use a markdown-to-reportlab parser)
        for line in content.split('\n'):
            if line.strip():
                elements.append(Paragraph(line, body_style))
                elements.append(Spacer(1, 6))
        
        # Footer
        elements.append(Spacer(1, 48))
        elements.append(Paragraph(footer, styles['Italic']))
        
        doc.build(elements)
        return buffer.getvalue()

    def generate_agenda_pdf(
        self,
        twg_pillar: str,
        meeting_title: str,
        meeting_date: datetime,
        meeting_location: str,
        agenda_content: str,
        duration_minutes: int = 60
    ) -> tuple[bytes, str]:
        """
        Generates a branded Agenda PDF on official summit letterhead.
        
        Returns:
            Tuple of (pdf_bytes, filename)
            Filename follows convention: {TWGPillar}_Agenda_{YYYY-MM-DD}.pdf
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        
        # Custom styles for letterhead
        header_style = ParagraphStyle(
            'Letterhead',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#004a99'),
            alignment=1,  # Center
            spaceAfter=6
        )
        
        subheader_style = ParagraphStyle(
            'Subheader',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=1,
            spaceAfter=20
        )
        
        title_style = ParagraphStyle(
            'AgendaTitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            alignment=1
        )
        
        meta_style = ParagraphStyle(
            'Meta',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=4
        )
        
        body_style = ParagraphStyle(
            'AgendaBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=14,
            spaceAfter=8
        )
        
        elements = []
        
        # === LETTERHEAD ===
        elements.append(Paragraph("<b>ECOWAS</b>", header_style))
        elements.append(Paragraph("Economic Community of West African States", subheader_style))
        elements.append(Paragraph("<b>Economic Integration & Investment Summit 2026</b>", header_style))
        elements.append(Paragraph("Technical Working Group Portal", subheader_style))
        elements.append(Spacer(1, 20))
        
        # Horizontal line effect
        elements.append(Paragraph("━" * 60, ParagraphStyle('Line', alignment=1, textColor=colors.HexColor('#004a99'))))
        elements.append(Spacer(1, 20))
        
        # === DOCUMENT TITLE ===
        pillar_display = twg_pillar.replace("_", " ").title()
        elements.append(Paragraph(f"<b>MEETING AGENDA</b>", title_style))
        elements.append(Paragraph(f"<i>{pillar_display} Technical Working Group</i>", subheader_style))
        elements.append(Spacer(1, 16))
        
        # === MEETING METADATA ===
        elements.append(Paragraph(f"<b>Title:</b> {meeting_title}", meta_style))
        elements.append(Paragraph(f"<b>Date:</b> {meeting_date.strftime('%A, %d %B %Y at %H:%M UTC')}", meta_style))
        elements.append(Paragraph(f"<b>Duration:</b> {duration_minutes} minutes", meta_style))
        elements.append(Paragraph(f"<b>Location:</b> {meeting_location or 'Virtual (Link to follow)'}", meta_style))
        elements.append(Spacer(1, 24))
        
        # === AGENDA CONTENT ===
        elements.append(Paragraph("<b>AGENDA</b>", styles['Heading3']))
        elements.append(Spacer(1, 8))
        
        for line in agenda_content.split('\n'):
            if line.strip():
                # Handle numbered items
                if line.strip()[0].isdigit():
                    elements.append(Paragraph(f"<b>{line.strip()}</b>", body_style))
                else:
                    elements.append(Paragraph(line.strip(), body_style))
        
        elements.append(Spacer(1, 40))
        
        # === FOOTER ===
        elements.append(Paragraph("━" * 60, ParagraphStyle('Line', alignment=1, textColor=colors.HexColor('#004a99'))))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(
            f"Document generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
            ParagraphStyle('Footer', fontSize=8, textColor=colors.gray, alignment=1)
        ))
        elements.append(Paragraph(
            "ECOWAS Summit 2026 - Abuja, Nigeria | summit.ecowas.int",
            ParagraphStyle('Footer', fontSize=8, textColor=colors.gray, alignment=1)
        ))
        
        doc.build(elements)
        
        # Generate filename with naming convention
        pillar_short = twg_pillar.split("_")[0].title() + "TWG"
        date_str = meeting_date.strftime('%Y-%m-%d')
        filename = f"{pillar_short}_Agenda_{date_str}.pdf"
        
        return buffer.getvalue(), filename


format_service = FormatService()
