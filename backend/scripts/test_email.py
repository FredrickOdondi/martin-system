"""
Test script to verify Resend email configuration.
Run this to test if emails are being sent successfully.
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.email_service import email_service
from app.core.config import settings

def test_email_sending():
    """Test if email sending works with current Resend configuration."""
    
    print("=" * 60)
    print("RESEND EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    # Check if Resend API key is configured
    if not settings.RESEND_API_KEY:
        print("❌ ERROR: RESEND_API_KEY is not configured!")
        print("Please set RESEND_API_KEY in your environment variables.")
        return False
    
    print(f"✅ Resend API Key: {settings.RESEND_API_KEY[:10]}...{settings.RESEND_API_KEY[-4:]}")
    print(f"✅ From Email: {settings.EMAIL_FROM}")
    print(f"✅ From Name: {settings.EMAIL_FROM_NAME}")
    print()
    
    # Get test email address
    test_email = input("Enter your email address to receive a test email: ").strip()
    
    if not test_email or "@" not in test_email:
        print("❌ Invalid email address!")
        return False
    
    print(f"\n📧 Sending test email to: {test_email}")
    print("Please wait...")
    
    try:
        # Send a simple test email
        result = email_service._send_via_resend(
            to_emails=[test_email],
            subject="🎉 Test Email from ECOWAS Summit System",
            html_content="""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h1 style="color: #2563eb; margin-bottom: 20px;">✅ Email Configuration Successful!</h1>
                        <p style="font-size: 16px; color: #333; line-height: 1.6;">
                            Congratulations! Your Resend email integration is working correctly.
                        </p>
                        <p style="font-size: 16px; color: #333; line-height: 1.6;">
                            This test email confirms that:
                        </p>
                        <ul style="font-size: 14px; color: #666; line-height: 1.8;">
                            <li>✅ Resend API key is valid</li>
                            <li>✅ Domain verification is working</li>
                            <li>✅ Email service is properly configured</li>
                            <li>✅ Your application can send emails</li>
                        </ul>
                        <div style="margin-top: 30px; padding: 15px; background-color: #eff6ff; border-left: 4px solid #2563eb; border-radius: 4px;">
                            <p style="margin: 0; font-size: 14px; color: #1e40af;">
                                <strong>Next Steps:</strong> Your email system is ready to send meeting invites, reminders, and notifications!
                            </p>
                        </div>
                        <p style="margin-top: 30px; font-size: 12px; color: #999; text-align: center;">
                            Sent from ECOWAS Summit Management System
                        </p>
                    </div>
                </body>
            </html>
            """
        )
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Email sent successfully!")
        print("=" * 60)
        print(f"Email ID: {result.get('id', 'N/A')}")
        print(f"\n📬 Check your inbox at: {test_email}")
        print("\nNote: It may take a few seconds to arrive.")
        print("Check your spam folder if you don't see it in your inbox.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ ERROR: Failed to send email!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print("\nPossible issues:")
        print("1. Invalid Resend API key")
        print("2. Domain not verified in Resend")
        print("3. Network connectivity issues")
        print("4. Resend service temporarily unavailable")
        print("=" * 60)
        return False

if __name__ == "__main__":
    test_email_sending()
