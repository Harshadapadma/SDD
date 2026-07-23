"""
Beautiful, high-density HTML email templates for Negen SDD.
- Designed in accordance with Negen SDD Design Tokens & Visual Language:
  * Warm Earthy Sand background (#F9F8F5)
  * Signature Negen Orange Gradients (#fb923c -> #ea6c00 -> #c2570a)
  * Slate / Obsidian Dark Security accents (#1e2937 -> #0f172a)
  * Tactile dataset cards & monospace identifier badges
  * High-contrast CTA buttons
- Streamlined to present strictly essential information & datasets with zero text fluff.
- Supports both inline MIME CID attachments (cid:negen_logo) for real email clients (Gmail, Outlook)
  and base64 data URIs for web preview files.
"""

import base64
import io
import os
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

# ── Logo embedding & path detection ──────────────────────────────────────────
_THIS_FILE    = os.path.abspath(__file__)
_USERS_DIR    = os.path.dirname(_THIS_FILE)       # backend/apps/users
_APPS_DIR     = os.path.dirname(_USERS_DIR)       # backend/apps
_BACKEND_DIR  = os.path.dirname(_APPS_DIR)        # backend
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)     # project root

_LOGO_CANDIDATES = [
    os.path.join(_PROJECT_ROOT, "frontend", "src", "assets", "logo.png"),
    os.path.join(_PROJECT_ROOT, "frontend", "assets", "logo.png"),
    os.path.join(_BACKEND_DIR,  "assets", "logo.png"),
]

def get_logo_file_path() -> str | None:
    """Return absolute file path of logo.png if it exists."""
    for p in _LOGO_CANDIDATES:
        if os.path.isfile(p):
            return p
    return None

def _load_logo_b64(max_px: int = 90) -> str:
    """
    Find the logo, resize it to max_px × max_px using Pillow,
    and return a data URI string for static web previews.
    """
    logo_path = get_logo_file_path()
    if not logo_path:
        print(f"[email_templates] WARNING: logo not found. Tried: {_LOGO_CANDIDATES}")
        return ""

    try:
        from PIL import Image
        with Image.open(logo_path) as img:
            img = img.convert("RGBA")
            img.thumbnail((max_px, max_px), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"[email_templates] Pillow resize failed ({e}), checking raw file")

    try:
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"[email_templates] Could not read logo: {e}")
        return ""


LOGO_DATA_URI = _load_logo_b64(max_px=90)


def _logo_img(size: int = 48, radius: int = 12) -> str:
    """
    Return an <img> tag for the logo.
    By default uses LOGO_DATA_URI (which send_sdd_email dynamically transforms to cid:negen_logo for email sending).
    Includes styled alt text and fallback formatting.
    """
    src_val = LOGO_DATA_URI if LOGO_DATA_URI else "cid:negen_logo"
    return (
        f'<img src="{src_val}" alt="Negen SDD" width="{size}" height="{size}" '
        f'style="display:block;border:none;outline:none;border-radius:{radius}px;background:#ffffff;'
        f'padding:4px;box-shadow:0 2px 6px rgba(0,0,0,0.15);object-fit:contain;font-family:sans-serif;'
        f'font-size:10px;font-weight:bold;color:#ea6c00;text-align:center;" />'
    )


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL SENDER WRAPPER — CID Inline Logo Attachment
# ══════════════════════════════════════════════════════════════════════════════
def send_sdd_email(
    subject: str,
    message: str,
    recipient_list: list[str],
    html_message: str,
    from_email: str = None,
    fail_silently: bool = False
) -> bool:
    """
    Sends an HTML email with Negen SDD logo attached as an inline CID image (cid:negen_logo).
    This guarantees that Gmail, Outlook, Apple Mail, etc. display the logo natively without blocking it.
    """
    if from_email is None:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost')

    msg = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=from_email,
        to=recipient_list
    )

    # Convert data URI to cid:negen_logo for real email delivery
    html_to_send = html_message
    if LOGO_DATA_URI and LOGO_DATA_URI in html_to_send:
        html_to_send = html_to_send.replace(LOGO_DATA_URI, "cid:negen_logo")

    msg.attach_alternative(html_to_send, "text/html")

    # Attach inline logo image with Content-ID <negen_logo>
    logo_path = get_logo_file_path()
    if logo_path and os.path.isfile(logo_path):
        try:
            with open(logo_path, "rb") as f:
                logo_raw = f.read()

            logo_bytes = logo_raw
            try:
                from PIL import Image
                with Image.open(logo_path) as img:
                    img = img.convert("RGBA")
                    img.thumbnail((120, 120), Image.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="PNG", optimize=True)
                    logo_bytes = buf.getvalue()
            except Exception as pe:
                print(f"[send_sdd_email] Pillow thumbnail failed ({pe}), using raw bytes")

            img_mime = MIMEImage(logo_bytes, _subtype="png")
            img_mime.add_header("Content-ID", "<negen_logo>")
            img_mime.add_header("Content-Disposition", "inline", filename="logo.png")
            msg.attach(img_mime)
            print(f"[send_sdd_email] Attached inline CID logo to email for {recipient_list}")
        except Exception as e:
            print(f"[send_sdd_email] Failed to attach inline logo: {e}")

    return msg.send(fail_silently=fail_silently)


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE 1 — User Registration & Account Created (Warm Negen Orange Theme)
# ══════════════════════════════════════════════════════════════════════════════
def get_account_created_email(
    name: str, email: str, role: str, public_id: str, setup_url: str
) -> tuple[str, str]:
    """Returns (subject, html_body) for the Account Registration email."""

    role_colors = {
        "ADMIN":                ("#7c3aed", "#f3f0ff", "Administrator"),
        "COLLABORATOR":         ("#ea6c00", "#fff7ed", "Collaborator"),
        "VIEWER":               ("#2563eb", "#eff6ff", "Viewer"),
        "COMPLIANCE_OFFICER":   ("#059669", "#ecfdf5", "Compliance Officer"),
    }
    badge_color, badge_bg, role_label = role_colors.get(
        role.upper(), ("#ea6c00", "#fff7ed", role.capitalize())
    )
    initial = (name[0].upper() if name else "U")

    subject = "Negen SDD – Account Activation & Credentials"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Account Activation</title>
</head>
<body style="margin:0;padding:0;background-color:#F9F8F5;font-family:'Inter', -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;-webkit-font-smoothing:antialiased;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#F9F8F5;padding:40px 16px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;width:100%;">

  <!-- BRAND HEADER -->
  <tr>
    <td style="background:linear-gradient(135deg, #fb923c 0%, #ea6c00 55%, #c2570a 100%);border-radius:20px 20px 0 0;padding:28px 32px;box-shadow:0 4px 20px rgba(234,108,0,0.25);">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="vertical-align:middle;">
            <table cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="padding-right:14px;vertical-align:middle;">{_logo_img(48, 12)}</td>
                <td style="vertical-align:middle;">
                  <div style="font-size:20px;font-weight:800;color:#ffffff;letter-spacing:-0.4px;line-height:1.2;">Negen SDD</div>
                  <div style="font-size:10px;color:rgba(255,255,255,0.85);letter-spacing:1.5px;text-transform:uppercase;font-weight:600;margin-top:2px;">Secure Document Dissemination</div>
                </td>
              </tr>
            </table>
          </td>
          <td align="right" style="vertical-align:middle;">
            <span style="background:rgba(255,255,255,0.22);border:1px solid rgba(255,255,255,0.4);color:#ffffff;font-size:10px;font-weight:700;padding:4px 12px;border-radius:99px;letter-spacing:1px;text-transform:uppercase;">
              NEW ACCOUNT
            </span>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- MAIN BODY SURFACE -->
  <tr>
    <td style="background:#ffffff;border-left:1px solid #E0D8CC;border-right:1px solid #E0D8CC;padding:32px 32px 28px;">
      
      <!-- Greeting & Summary -->
      <div style="font-size:18px;font-weight:800;color:#1f2937;margin-bottom:6px;">
        Account Ready for {name}
      </div>
      <div style="font-size:13px;color:#6b7585;line-height:1.5;margin-bottom:24px;">
        Your official Negen SDD portal credentials have been provisioned. Below is your account dataset.
      </div>

      <!-- DATASET ID CARD -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F9F8F5;border:1px solid #E0D8CC;border-radius:14px;margin-bottom:24px;overflow:hidden;">
        <tr>
          <td style="padding:20px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              
              <!-- Card Header Row -->
              <tr>
                <td style="padding-bottom:14px;border-bottom:1px solid #E8EAED;">
                  <div style="font-size:10px;font-weight:700;letter-spacing:1.2px;color:#9aa3b8;text-transform:uppercase;">USER IDENTIFIER DATASET</div>
                </td>
                <td align="right" style="padding-bottom:14px;border-bottom:1px solid #E8EAED;">
                  <span style="background:{badge_bg};color:{badge_color};border:1px solid {badge_color}40;font-size:10px;font-weight:800;padding:3px 10px;border-radius:99px;letter-spacing:0.5px;">
                    {role_label.upper()}
                  </span>
                </td>
              </tr>

              <!-- Avatar & Core Info -->
              <tr>
                <td colspan="2" style="padding-top:16px;padding-bottom:16px;">
                  <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                      <td width="48" style="vertical-align:middle;padding-right:14px;">
                        <div style="width:48px;height:48px;border-radius:50%;background:#ea6c00;color:#ffffff;font-size:20px;font-weight:800;line-height:48px;text-align:center;box-shadow:0 2px 8px rgba(234,108,0,0.3);">
                          {initial}
                        </div>
                      </td>
                      <td style="vertical-align:middle;">
                        <div style="font-size:15px;font-weight:700;color:#1f2937;line-height:1.2;">{name}</div>
                        <div style="font-size:12px;color:#6b7585;margin-top:3px;">{email}</div>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Key Value Table -->
              <tr>
                <td colspan="2" style="border-top:1px solid #E8EAED;padding-top:14px;">
                  <table width="100%" cellpadding="0" cellspacing="0" border="0">
                    <tr>
                      <td width="50%" style="vertical-align:top;padding-right:8px;">
                        <div style="font-size:10px;font-weight:600;color:#9aa3b8;text-transform:uppercase;margin-bottom:3px;">Public User ID</div>
                        <div style="font-family:'Courier New', Consolas, monospace;font-size:12px;font-weight:700;color:#1f2937;background:#E8EAED;display:inline-block;padding:3px 8px;border-radius:6px;">
                          {public_id}
                        </div>
                      </td>
                      <td width="50%" style="vertical-align:top;padding-left:8px;">
                        <div style="font-size:10px;font-weight:600;color:#9aa3b8;text-transform:uppercase;margin-bottom:3px;">Account Status</div>
                        <div style="font-size:12px;font-weight:700;color:#c2570a;">
                          Pending Password Setup
                        </div>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>

      <!-- CTA ACTION BUTTON -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:24px;">
        <tr>
          <td align="center">
            <a href="{setup_url}" target="_blank" style="display:inline-block;background:linear-gradient(135deg, #ea6c00 0%, #c2570a 100%);color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:10px;box-shadow:0 4px 14px rgba(234,108,0,0.35);letter-spacing:0.3px;">
              Activate Account &amp; Set Password &rarr;
            </a>
          </td>
        </tr>
      </table>

      <!-- Minimal Direct Link snippet -->
      <div style="background:#F9F8F5;border:1px solid #E8EAED;border-radius:8px;padding:10px 12px;font-size:11px;color:#6b7585;line-height:1.4;word-break:break-all;">
        <span style="font-weight:700;color:#374151;">Direct Link:</span> <a href="{setup_url}" style="color:#ea6c00;text-decoration:none;">{setup_url}</a>
      </div>

    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#F9F8F5;border:1px solid #E0D8CC;border-top:none;border-radius:0 0 20px 20px;padding:20px 32px;text-align:center;">
      <div style="font-size:11px;color:#9aa3b8;margin-bottom:4px;">Automated system email from Negen SDD. Please do not reply directly.</div>
      <div style="font-size:11px;color:#6b7585;font-weight:600;">
        &copy; Negen SDD &bull; Secure Document Dissemination Platform
      </div>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    return subject, html


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE 2 — Password Reset Request (Slate & Obsidian Dark Security Theme)
# ══════════════════════════════════════════════════════════════════════════════
def get_password_reset_email(name: str, email: str, reset_url: str) -> tuple[str, str]:
    """Returns (subject, html_body) for the Password Reset email."""

    subject = "Negen SDD – Security Alert: Password Reset Request"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Password Reset Request</title>
</head>
<body style="margin:0;padding:0;background-color:#F9F8F5;font-family:'Inter', -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;-webkit-font-smoothing:antialiased;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#F9F8F5;padding:40px 16px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;width:100%;">

  <!-- SECURITY HEADER (DARK SLATE) -->
  <tr>
    <td style="background:linear-gradient(135deg, #1e2937 0%, #0f172a 100%);border-radius:20px 20px 0 0;padding:28px 32px;box-shadow:0 4px 20px rgba(15,23,42,0.3);">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="vertical-align:middle;">
            <table cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="padding-right:14px;vertical-align:middle;">{_logo_img(48, 12)}</td>
                <td style="vertical-align:middle;">
                  <div style="font-size:20px;font-weight:800;color:#ffffff;letter-spacing:-0.4px;line-height:1.2;">Negen SDD</div>
                  <div style="font-size:10px;color:rgba(255,255,255,0.65);letter-spacing:1.5px;text-transform:uppercase;font-weight:600;margin-top:2px;">Security &amp; Account Governance</div>
                </td>
              </tr>
            </table>
          </td>
          <td align="right" style="vertical-align:middle;">
            <span style="background:rgba(234,108,0,0.25);border:1px solid #ea6c00;color:#fb923c;font-size:10px;font-weight:800;padding:4px 12px;border-radius:99px;letter-spacing:1px;text-transform:uppercase;">
              PASSWORD RESET
            </span>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- MAIN BODY SURFACE -->
  <tr>
    <td style="background:#ffffff;border-left:1px solid #E0D8CC;border-right:1px solid #E0D8CC;padding:32px 32px 28px;">
      
      <!-- Security Heading -->
      <div style="font-size:18px;font-weight:800;color:#1f2937;margin-bottom:6px;">
        Password Reset Requested
      </div>
      <div style="font-size:13px;color:#6b7585;line-height:1.5;margin-bottom:20px;">
        A password reset request was initialized for the account associated with <strong style="color:#1f2937;">{email}</strong>.
      </div>

      <!-- SECURITY DATASET SUMMARY BOX -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F9F8F5;border:1px solid #E0D8CC;border-radius:14px;margin-bottom:20px;">
        <tr>
          <td style="padding:18px 20px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="padding-bottom:10px;border-bottom:1px solid #E8EAED;">
                  <div style="font-size:10px;font-weight:700;letter-spacing:1.2px;color:#9aa3b8;text-transform:uppercase;">REQUEST DETAILS</div>
                </td>
              </tr>
              <tr>
                <td style="padding-top:12px;">
                  <table width="100%" cellpadding="0" cellspacing="0" border="0">
                    <tr>
                      <td style="font-size:12px;color:#6b7585;padding-bottom:6px;">Account User:</td>
                      <td align="right" style="font-size:12px;font-weight:700;color:#1f2937;padding-bottom:6px;">{name}</td>
                    </tr>
                    <tr>
                      <td style="font-size:12px;color:#6b7585;padding-bottom:6px;">Target Email:</td>
                      <td align="right" style="font-size:12px;font-weight:700;color:#1f2937;padding-bottom:6px;">{email}</td>
                    </tr>
                    <tr>
                      <td style="font-size:12px;color:#6b7585;">Token Validity:</td>
                      <td align="right" style="font-size:12px;font-weight:700;color:#d97706;">Time-Sensitive Single-Use</td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- CTA ACTION BUTTON -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:24px;">
        <tr>
          <td align="center">
            <a href="{reset_url}" target="_blank" style="display:inline-block;background:linear-gradient(135deg, #ea6c00 0%, #c2570a 100%);color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:10px;box-shadow:0 4px 14px rgba(234,108,0,0.35);letter-spacing:0.3px;">
              Reset Password Now &rarr;
            </a>
          </td>
        </tr>
      </table>

      <!-- AMBER SECURITY NOTICE -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fffbeb;border:1px solid #fef3c7;border-radius:10px;margin-bottom:20px;">
        <tr>
          <td style="padding:12px 16px;">
            <div style="font-size:12px;color:#b45309;line-height:1.5;">
              <strong style="color:#92400e;">Did not request this change?</strong> You can safely disregard this message. Your existing password remains unchanged and secure.
            </div>
          </td>
        </tr>
      </table>

      <!-- Direct link snippet -->
      <div style="background:#F9F8F5;border:1px solid #E8EAED;border-radius:8px;padding:10px 12px;font-size:11px;color:#6b7585;line-height:1.4;word-break:break-all;">
        <span style="font-weight:700;color:#374151;">Direct Link:</span> <a href="{reset_url}" style="color:#ea6c00;text-decoration:none;">{reset_url}</a>
      </div>

    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#F9F8F5;border:1px solid #E0D8CC;border-top:none;border-radius:0 0 20px 20px;padding:20px 32px;text-align:center;">
      <div style="font-size:11px;color:#9aa3b8;margin-bottom:4px;">Automated security notification from Negen SDD.</div>
      <div style="font-size:11px;color:#6b7585;font-weight:600;">
        &copy; Negen SDD &bull; Secure Document Dissemination Platform
      </div>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    return subject, html


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE 3 — Password Successfully Changed (Security Confirmation Helper)
# ══════════════════════════════════════════════════════════════════════════════
def get_password_changed_email(name: str, email: str, timestamp_str: str) -> tuple[str, str]:
    """Returns (subject, html_body) for Password Changed notification."""

    subject = "Negen SDD – Security Alert: Password Updated"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Password Updated</title>
</head>
<body style="margin:0;padding:0;background-color:#F9F8F5;font-family:'Inter', -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;-webkit-font-smoothing:antialiased;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#F9F8F5;padding:40px 16px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;width:100%;">

  <!-- HEADER -->
  <tr>
    <td style="background:linear-gradient(135deg, #059669 0%, #047857 100%);border-radius:20px 20px 0 0;padding:28px 32px;box-shadow:0 4px 20px rgba(5,150,105,0.25);">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="vertical-align:middle;">
            <table cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="padding-right:14px;vertical-align:middle;">{_logo_img(48, 12)}</td>
                <td style="vertical-align:middle;">
                  <div style="font-size:20px;font-weight:800;color:#ffffff;letter-spacing:-0.4px;line-height:1.2;">Negen SDD</div>
                  <div style="font-size:10px;color:rgba(255,255,255,0.85);letter-spacing:1.5px;text-transform:uppercase;font-weight:600;margin-top:2px;">Security Confirmation</div>
                </td>
              </tr>
            </table>
          </td>
          <td align="right" style="vertical-align:middle;">
            <span style="background:rgba(255,255,255,0.25);color:#ffffff;font-size:10px;font-weight:800;padding:4px 12px;border-radius:99px;letter-spacing:1px;text-transform:uppercase;">
              CONFIRMED
            </span>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- BODY -->
  <tr>
    <td style="background:#ffffff;border-left:1px solid #E0D8CC;border-right:1px solid #E0D8CC;padding:32px 32px 28px;">
      <div style="font-size:18px;font-weight:800;color:#1f2937;margin-bottom:6px;">Password Successfully Changed</div>
      <div style="font-size:13px;color:#6b7585;line-height:1.5;margin-bottom:20px;">
        Your password for Negen SDD account <strong style="color:#1f2937;">{email}</strong> was updated successfully.
      </div>

      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F9F8F5;border:1px solid #E0D8CC;border-radius:14px;padding:16px 20px;margin-bottom:20px;">
        <tr>
          <td style="font-size:12px;color:#6b7585;">Update Timestamp:</td>
          <td align="right" style="font-size:12px;font-weight:700;color:#1f2937;">{timestamp_str}</td>
        </tr>
      </table>

      <div style="font-size:12px;color:#dc2626;background:#fef2f2;border:1px solid #fee2e2;border-radius:8px;padding:12px 14px;line-height:1.4;">
        <strong>Unrecognized activity?</strong> Contact your Negen SDD administrator immediately to safeguard your account.
      </div>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#F9F8F5;border:1px solid #E0D8CC;border-top:none;border-radius:0 0 20px 20px;padding:20px 32px;text-align:center;">
      <div style="font-size:11px;color:#6b7585;font-weight:600;">
        &copy; Negen SDD &bull; Secure Document Dissemination Platform
      </div>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    return subject, html
