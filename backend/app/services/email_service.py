import os
from typing import List, Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz

from app.core.config import settings

# Try to import resend, fall back gracefully if not available
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False


class EmailService:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
            
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME
        
        # Configure Resend if available
        if RESEND_AVAILABLE and settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY
            self.use_resend = True
        else:
            self.use_resend = False
            # SMTP fallback settings
            self.smtp_server = settings.SMTP_HOST
            self.smtp_port = settings.SMTP_PORT
            self.smtp_user = settings.SMTP_USER
            self.smtp_password = settings.SMTP_PASSWORD

    def _create_calendar_invite(
        self,
        title: str,
        description: str,
        start_time: datetime,
        duration_minutes: int,
        location: Optional[str] = None,
        attendees: List[str] = None
    ) -> bytes:
        """
        Creates an iCalendar (.ics) invite.
        """
        cal = Calendar()
        cal.add('prodid', '-//ECOWAS Summit TWG//martin-system//EN')
        cal.add('version', '2.0')
        cal.add('method', 'REQUEST')

        event = Event()
        event.add('summary', title)
        event.add('description', description)
        event.add('dtstart', start_time)
        event.add('dtend', start_time + timedelta(minutes=duration_minutes))
        event.add('dtstamp', datetime.now(pytz.utc))
        
        if location:
            event.add('location', location)

        if attendees:
            for email in attendees:
                event.add('attendee', f'MAILTO:{email}', parameters={'RSVP': 'TRUE'})

        cal.add_component(event)
        return cal.to_ical()

    async def send_meeting_invite(
        self,
        to_emails: List[str],
        subject: str,
        template_name: str,
        template_context: Dict[str, Any],
        meeting_details: Dict[str, Any]
    ):
        """
        Sends a meeting invitation with an ICS attachment.
        """
        template = self.jinja_env.get_template(template_name)
        html_content = template.render(**template_context)
        
        # Create ICS
        ics_content = self._create_calendar_invite(
            title=meeting_details['title'],
            description=meeting_details.get('description', ''),
            start_time=meeting_details['start_time'],
            duration_minutes=meeting_details.get('duration', 60),
            location=meeting_details.get('location'),
            attendees=to_emails
        )

        if not settings.EMAILS_ENABLED:
            print(f"[EmailService] Emails disabled. Would send to: {to_emails}")
            return True

        if self.use_resend:
            return await self._send_via_resend(
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                ics_content=ics_content,
                ics_filename="invite.ics"
            )
        else:
            return await self._send_via_smtp(
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                ics_content=ics_content,
                ics_filename="invite.ics"
            )

    async def send_meeting_update(
        self,
        to_emails: List[str],
        template_context: Dict[str, Any],
        meeting_details: Dict[str, Any],
        changes: List[str] = None
    ):
        """
        Sends a meeting update notification with an updated ICS attachment.
        """
        template = self.jinja_env.get_template("meeting_update.html")
        template_context["changes"] = changes or []
        html_content = template.render(**template_context)
        
        ics_content = self._create_calendar_invite(
            title=meeting_details['title'],
            description=meeting_details.get('description', ''),
            start_time=meeting_details['start_time'],
            duration_minutes=meeting_details.get('duration', 60),
            location=meeting_details.get('location'),
            attendees=to_emails
        )

        subject = f"UPDATED: {meeting_details['title']}"

        if not settings.EMAILS_ENABLED:
            print(f"[EmailService] Emails disabled. Would send update to: {to_emails}")
            return True

        if self.use_resend:
            return await self._send_via_resend(
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                ics_content=ics_content,
                ics_filename="meeting_update.ics"
            )
        else:
            return await self._send_via_smtp(
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                ics_content=ics_content,
                ics_filename="meeting_update.ics"
            )

    def _create_cancel_invite(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int,
        location: Optional[str] = None
    ) -> bytes:
        """
        Creates an iCalendar (.ics) cancellation notice.
        """
        cal = Calendar()
        cal.add('prodid', '-//ECOWAS Summit TWG//martin-system//EN')
        cal.add('version', '2.0')
        cal.add('method', 'CANCEL')

        event = Event()
        event.add('summary', f"CANCELLED: {title}")
        event.add('dtstart', start_time)
        event.add('dtend', start_time + timedelta(minutes=duration_minutes))
        event.add('dtstamp', datetime.now(pytz.utc))
        event.add('status', 'CANCELLED')
        
        if location:
            event.add('location', location)

        cal.add_component(event)
        return cal.to_ical()

    async def send_meeting_cancellation(
        self,
        to_emails: List[str],
        template_context: Dict[str, Any],
        meeting_details: Dict[str, Any],
        reason: str = None
    ):
        """
        Sends a meeting cancellation notification with a CANCEL ICS attachment.
        """
        template = self.jinja_env.get_template("meeting_cancellation.html")
        template_context["reason"] = reason
        html_content = template.render(**template_context)
        
        ics_content = self._create_cancel_invite(
            title=meeting_details['title'],
            start_time=meeting_details['start_time'],
            duration_minutes=meeting_details.get('duration', 60),
            location=meeting_details.get('location')
        )

        subject = f"CANCELLED: {meeting_details['title']}"

        if not settings.EMAILS_ENABLED:
            print(f"[EmailService] Emails disabled. Would send cancellation to: {to_emails}")
            return True

        if self.use_resend:
            return await self._send_via_resend(
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                ics_content=ics_content,
                ics_filename="cancellation.ics"
            )
        else:
            return await self._send_via_smtp(
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                ics_content=ics_content,
                ics_filename="cancellation.ics"
            )

    async def _send_via_resend(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        ics_content: bytes = None,
        ics_filename: str = "invite.ics"
    ) -> bool:
        """
        Send email using Resend API (works on Railway).
        """
        import base64
        
        attachments = []
        if ics_content:
            attachments.append({
                "filename": ics_filename,
                "content": base64.b64encode(ics_content).decode('utf-8'),
                "content_type": "text/calendar"
            })

        params = {
            "from": f"{self.from_name} <{self.from_email}>",
            "to": to_emails,
            "subject": subject,
            "html": html_content,
        }
        
        if attachments:
            params["attachments"] = attachments

        try:
            result = resend.Emails.send(params)
            print(f"[Resend] Email sent successfully: {result}")
            return True
        except Exception as e:
            print(f"[Resend] Failed to send email: {e}")
            raise

    async def _send_via_smtp(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        ics_content: bytes = None,
        ics_filename: str = "invite.ics"
    ) -> bool:
        """
        Send email using SMTP (fallback, may not work on some cloud platforms).
        """
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders

        message = MIMEMultipart("mixed")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = ", ".join(to_emails)

        part_html = MIMEText(html_content, "html")
        message.attach(part_html)

        if ics_content:
            part_ics = MIMEBase("text", "calendar", method="REQUEST")
            part_ics.set_payload(ics_content)
            encoders.encode_base64(part_ics)
            part_ics.add_header("Content-Disposition", "attachment", filename=ics_filename)
            part_ics.add_header("Content-Class", "urn:content-classes:calendarmessage")
            message.attach(part_ics)

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, to_emails, message.as_string())
        
        return True


email_service = EmailService()
