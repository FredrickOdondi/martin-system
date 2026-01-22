"""
Standalone Resend email test - no dependencies on the app.
"""
import os

def test_resend():
    """Test Resend email sending directly."""
    
    print("=" * 60)
    print("RESEND EMAIL TEST")
    print("=" * 60)
    
    # Check for Resend API key
    api_key = os.getenv("RESEND_API_KEY")
    
    if not api_key:
        print("❌ ERROR: RESEND_API_KEY environment variable not set!")
        print("\nTo fix this:")
        print("1. Get your API key from https://resend.com/api-keys")
        print("2. Set it: export RESEND_API_KEY='your-key-here'")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Try to import resend
    try:
        import resend
        print("✅ Resend library installed")
    except ImportError:
        print("❌ Resend library not installed!")
        print("Install it with: pip install resend")
        return
    
    # Set the API key
    resend.api_key = api_key
    
    # Get test email
    test_email = input("\nEnter your email address for testing: ").strip()
    
    if not test_email or "@" not in test_email:
        print("❌ Invalid email address!")
        return
    
    print(f"\n📧 Sending test email to: {test_email}")
    print("Please wait...\n")
    
    try:
        # Send test email
        params = {
            "from": "ECOWAS Summit <noreply@ecowasiisummit.net>",
            "to": [test_email],
            "subject": "🎉 Test Email - ECOWAS Summit System",
            "html": """
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #f8fafc; padding: 30px; border-radius: 10px;">
                        <h1 style="color: #2563eb;">✅ Success!</h1>
                        <p style="font-size: 16px; color: #334155;">
                            Your Resend email configuration is working perfectly!
                        </p>
                        <div style="margin: 20px 0; padding: 15px; background-color: #dbeafe; border-radius: 5px;">
                            <strong>What this means:</strong>
                            <ul>
                                <li>✅ API key is valid</li>
                                <li>✅ Domain is verified</li>
                                <li>✅ Emails can be sent</li>
                            </ul>
                        </div>
                        <p style="color: #64748b; font-size: 14px;">
                            Sent from ECOWAS Summit Management System
                        </p>
                    </div>
                </body>
            </html>
            """
        }
        
        result = resend.Emails.send(params)
        
        print("=" * 60)
        print("✅ SUCCESS! Email sent!")
        print("=" * 60)
        print(f"Email ID: {result['id']}")
        print(f"\n📬 Check your inbox: {test_email}")
        print("\nNote:")
        print("- Email may take a few seconds to arrive")
        print("- Check spam folder if not in inbox")
        print("- First emails from new domains may be slower")
        print("=" * 60)
        
    except Exception as e:
        print("=" * 60)
        print("❌ ERROR!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print("\nPossible causes:")
        print("1. Invalid API key")
        print("2. Domain not verified in Resend dashboard")
        print("3. Network issues")
        print("=" * 60)

if __name__ == "__main__":
    test_resend()
