# 🚀 Local Testing Guide - Email Functionality

## ✅ Servers Running

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

## 📧 How to Test Email Sending

### Option 1: Create a Meeting (Easiest)

1. **Open the app**: http://localhost:5173
2. **Login** with your credentials
3. **Navigate to**: TWG Workspace or Schedule page
4. **Click**: "New Meeting" or "Schedule Meeting"
5. **Fill in the form**:
   - Title: "Test Meeting"
   - Date/Time: Any future date
   - Add participants with email addresses
6. **Submit** the form
7. **Check**: The participant emails should receive meeting invites!

### Option 2: Use API Directly (via Swagger)

1. **Open**: http://localhost:8000/docs
2. **Authorize**: Click "Authorize" and enter your JWT token
3. **Find**: POST `/api/v1/meetings` endpoint
4. **Try it out** with this payload:

```json
{
  "title": "Email Test Meeting",
  "description": "Testing email functionality",
  "scheduled_at": "2026-01-15T10:00:00Z",
  "duration_minutes": 60,
  "twg_id": "your-twg-id-here",
  "type": "regular",
  "location": "Virtual",
  "participant_emails": ["your-email@example.com"]
}
```

5. **Execute** - Check your email!

### Option 3: Direct Email Test Script

Run the standalone test script:

```bash
cd /home/evan/Desktop/martin\ os\ v2/martin-system/backend

# Set your Resend API key
export RESEND_API_KEY="your-resend-api-key"

# Activate virtual environment
source venv/bin/activate

# Install resend if needed
pip install resend

# Run test
python3 test_resend_simple.py
```

## 🔍 Where to Find Your Resend API Key

1. Go to: https://resend.com/api-keys
2. Copy your API key
3. In Railway, set it as: `RESEND_API_KEY`
4. Locally, export it: `export RESEND_API_KEY="re_..."`

## ✅ What Emails to Expect

When you create a meeting, the system will send:

- **Meeting Invite** with ICS attachment (calendar file)
- **To**: All participant emails
- **From**: noreply@ecowasiisummit.net
- **Subject**: "Meeting Invitation: [Meeting Title]"

## 🐛 Troubleshooting

### Email not received?

1. **Check spam folder**
2. **Verify Resend API key** is set correctly
3. **Check backend logs** for errors:
   ```bash
   # Look for email-related errors in terminal
   ```
4. **Verify domain** in Resend dashboard shows as verified
5. **Check Resend logs**: https://resend.com/logs

### Backend errors?

- Check terminal running backend for error messages
- Verify `.env` file has `RESEND_API_KEY`
- Ensure database is running

### Frontend not connecting?

- Check that `VITE_API_URL` points to `http://localhost:8000`
- Clear browser cache
- Check browser console for errors

## 📝 Testing Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Logged into the application
- [ ] Created a test meeting with your email
- [ ] Checked inbox (and spam) for meeting invite
- [ ] Verified ICS attachment is included
- [ ] Calendar invite can be added to calendar

## 🎯 Next Steps After Testing

Once emails work locally:

1. ✅ Verify Railway has `RESEND_API_KEY` set
2. ✅ Test on production: https://ecowasiisummit.net
3. ✅ Monitor Resend dashboard for delivery stats
4. ✅ Set up email templates for other notifications

---

**Current Status**: 
- ✅ Backend: Running on http://localhost:8000
- ✅ Frontend: Running on http://localhost:5173
- ⏳ Ready to test emails!
