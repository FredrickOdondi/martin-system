# 🎨 Beautiful Email Templates - Documentation

## Overview

All AI-generated emails now automatically use the beautiful ECOWAS Summit design! This ensures consistent, professional branding across all communications.

## What Changed

### ✨ Automatic Template Wrapping

When the AI sends emails, they are now automatically wrapped in a beautiful, branded template that includes:

- **ECOWAS Summit 2026 Header** - Professional blue header with logo
- **TWG Pillar Badge** - Shows which working group the email relates to
- **AI Generated Badge** - Indicates the email was created by AI
- **Styled Content** - Professional typography and spacing
- **Footer** - Consistent branding and copyright

### 📧 Before vs After

**Before**: Plain, generic HTML emails
```html
<p>Dear participant,</p>
<p>Here is your meeting summary...</p>
```

**After**: Beautifully branded emails with ECOWAS design
![Beautiful Email Design](/home/evan/.gemini/antigravity/brain/baa1c6aa-84a2-495d-a258-b6d0824cae06/uploaded_image_1768062135940.png)

## For AI Agents

### Using the send_email Tool

The AI can now optionally specify a `pillar_name` to brand the email:

```python
await send_email(
    to="participant@example.com",
    subject="Meeting Summary",
    message="Plain text version...",
    html_body="<h2>Key Points</h2><p>Discussion highlights...</p>",
    pillar_name="Energy"  # ← NEW! Adds "ENERGY TWG" badge
)
```

### Available Pillar Names

- `"Energy"`
- `"Infrastructure"`
- `"Agriculture"`
- `"Digital"`
- `"Minerals"`
- `"Protocol"`
- `"Resource Mobilization"`

### Template Features

The wrapper automatically adds:

1. **ECOWAS Header** - Blue branded header
2. **Pillar Badge** - If `pillar_name` is provided
3. **AI Badge** - "✨ AI Generated" indicator
4. **Professional Styling** - Consistent fonts, colors, spacing
5. **Footer** - Copyright and branding

## For Developers

### Manual Template Usage

You can also manually wrap content in the template:

```python
from app.utils.email_templates import wrap_email_content

html = wrap_email_content(
    content="<h2>Your Content</h2><p>Body text...</p>",
    pillar_name="Agriculture",
    ai_generated=True
)
```

### Creating Info Boxes

For structured information:

```python
from app.utils.email_templates import create_info_box

box = create_info_box(
    title="Meeting Details",
    items={
        "Date": "2026-01-15",
        "Time": "10:00 UTC",
        "Location": "Virtual"
    }
)
```

### Disabling Template Wrapper

If you need to send a custom-designed email without the wrapper:

```python
await send_email(
    to="user@example.com",
    subject="Custom Email",
    html_body="<html>...fully custom HTML...</html>",
    use_template_wrapper=False  # ← Disable wrapper
)
```

## Template Files

### Main Template
- **Location**: `backend/app/templates/email/email_wrapper.html`
- **Purpose**: Base template for all emails
- **Variables**:
  - `content` - Main email body (required)
  - `pillar_name` - TWG pillar name (optional)
  - `ai_generated` - Show AI badge (optional)

### Utility Functions
- **Location**: `backend/app/utils/email_templates.py`
- **Functions**:
  - `wrap_email_content()` - Wrap content in template
  - `format_ai_email()` - Format AI emails with portal link
  - `create_info_box()` - Create styled info boxes

## Styling Guide

### Colors

- **Primary Blue**: `#004a99` (ECOWAS brand)
- **Button Blue**: `#007bff`
- **AI Badge**: Purple gradient (`#667eea` to `#764ba2`)
- **Text**: `#333` (dark gray)
- **Background**: `#f5f5f5` (light gray)

### Components

#### Header
```html
<div class="header">
    <h1>ECOWAS Summit 2026</h1>
    <p>Technical Working Group Portal</p>
</div>
```

#### Pillar Badge
```html
<div class="pillar-tag">ENERGY TWG</div>
```

#### AI Badge
```html
<span class="ai-badge">✨ AI Generated</span>
```

#### Button
```html
<a href="..." class="button">View in Portal</a>
```

#### Info Box
```html
<div class="info-box">
    <p><strong>Title</strong></p>
    <p><strong>Label:</strong> Value</p>
</div>
```

## Testing

### Test AI Email Generation

1. Ask the AI to send an email via chat
2. The AI will create a draft with approval required
3. Review the draft in the UI
4. You should see the beautiful ECOWAS template!

### Example Prompt

> "Send an email to john@example.com summarizing today's energy meeting. Include the key decisions and action items."

The AI will automatically:
- Generate the email content
- Wrap it in the ECOWAS template
- Add the "Energy" pillar badge
- Add the AI badge
- Create an approval request

## Benefits

✅ **Consistent Branding** - All emails look professional  
✅ **Clear Attribution** - AI badge shows it's AI-generated  
✅ **TWG Context** - Pillar badges provide context  
✅ **Better UX** - Recipients get beautiful, readable emails  
✅ **Automatic** - No extra work for AI or developers  

## Migration Notes

### Existing Email Templates

Meeting invites and other system emails already use similar styling. The new wrapper ensures AI-generated emails match this design.

### Backward Compatibility

- Old emails without `html_body` still work
- Plain text emails are unaffected
- Can disable wrapper with `use_template_wrapper=False`

## Future Enhancements

Potential improvements:

- [ ] Add more template variations (urgent, reminder, etc.)
- [ ] Support for custom color schemes per TWG
- [ ] Email preview in chat before approval
- [ ] Template customization via admin panel
- [ ] Multi-language support

---

**Questions?** Check the code in:
- `backend/app/templates/email/email_wrapper.html`
- `backend/app/utils/email_templates.py`
- `backend/app/tools/email_tools.py`
