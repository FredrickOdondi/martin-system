"""
Email Template Utilities

Provides helper functions for wrapping email content in beautiful templates.
"""

import os
from typing import Optional
from jinja2 import Environment, FileSystemLoader

# Template directory
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'email')


def wrap_email_content(
    content: str,
    pillar_name: Optional[str] = None,
    ai_generated: bool = False
) -> str:
    """
    Wrap email content in the beautiful ECOWAS email template.
    
    Args:
        content: HTML content to wrap (the main body)
        pillar_name: Optional TWG pillar name (e.g., "Energy", "Infrastructure")
        ai_generated: Whether this email was AI-generated (adds badge)
    
    Returns:
        Complete HTML email with ECOWAS branding
    
    Example:
        html = wrap_email_content(
            content="<h2>Meeting Summary</h2><p>Here are the key points...</p>",
            pillar_name="Energy",
            ai_generated=True
        )
    """
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template('email_wrapper.html')
    
    return template.render(
        content=content,
        pillar_name=pillar_name,
        ai_generated=ai_generated
    )


def format_ai_email(
    subject: str,
    body_html: str,
    pillar_name: Optional[str] = None,
    include_portal_link: bool = True,
    portal_url: Optional[str] = None
) -> str:
    """
    Format an AI-generated email with beautiful styling.
    
    Args:
        subject: Email subject (used as h2 heading)
        body_html: Main body content (can be plain HTML or formatted)
        pillar_name: Optional TWG pillar name
        include_portal_link: Whether to include "View in Portal" button
        portal_url: URL for the portal button
    
    Returns:
        Beautifully formatted HTML email
    
    Example:
        html = format_ai_email(
            subject="Weekly Update",
            body_html="<p>This week we accomplished...</p>",
            pillar_name="Agriculture",
            portal_url="https://portal.ecowas.com/meetings/123"
        )
    """
    from app.core.config import settings
    
    # Build content
    content_parts = []
    
    # Add subject as heading
    if subject:
        content_parts.append(f'<h2>{subject}</h2>')
    
    # Add main body
    content_parts.append(body_html)
    
    # Add portal link if requested
    if include_portal_link:
        url = portal_url or settings.FRONTEND_URL
        content_parts.append(
            f'<a href="{url}" class="button" style="color: #ffffff !important;">View in Portal</a>'
        )
    
    content = '\n'.join(content_parts)
    
    return wrap_email_content(
        content=content,
        pillar_name=pillar_name,
        ai_generated=True
    )


def create_info_box(title: str, items: dict) -> str:
    """
    Create a styled info box for displaying structured information.
    
    Args:
        title: Box title
        items: Dictionary of label: value pairs
    
    Returns:
        HTML for info box
    
    Example:
        box = create_info_box(
            title="Meeting Details",
            items={
                "Date": "2026-01-15",
                "Time": "10:00 UTC",
                "Location": "Virtual"
            }
        )
    """
    html_parts = ['<div class="info-box">']
    
    if title:
        html_parts.append(f'<p><strong>{title}</strong></p>')
    
    for label, value in items.items():
        html_parts.append(f'<p><strong>{label}:</strong> {value}</p>')
    
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)
