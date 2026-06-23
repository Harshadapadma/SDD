"""
Beautiful HTML email templates for Negen SDD.
- All styles are inlined for maximum email-client compatibility.
- Logo is resized to a small thumbnail via Pillow to keep emails
  well under Gmail's 102 KB clip threshold.
- Logo is embedded as a base64 data URI (no external URL needed).
"""

import base64
import io
import os

# ── Logo embedding ─────────────────────────────────────────────────────────────
# __file__ = <project_root>/backend/apps/users/email_templates.py
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

def _load_logo_b64(max_px: int = 90) -> str:
    """
    Find the logo, resize it to max_px × max_px using Pillow (to keep
    the base64 payload tiny), and return a data URI string.
    Falls back to an empty string if the file is not found or Pillow fails.
    """
    logo_path = None
    for p in _LOGO_CANDIDATES:
        if os.path.isfile(p):
            logo_path = p
            break

    if not logo_path:
        print(f"[email_templates] WARNING: logo not found. Tried: {_LOGO_CANDIDATES}")
        return ""

    # Try Pillow resize first (keeps size tiny)
    try:
        from PIL import Image
        with Image.open(logo_path) as img:
            img = img.convert("RGBA")
            img.thumbnail((max_px, max_px), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            print(f"[email_templates] Logo loaded & resized ({max_px}px): {logo_path}")
            return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"[email_templates] Pillow resize failed ({e}), falling back to raw file")

    # Fallback: encode raw file (large, but better than nothing)
    try:
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        print(f"[email_templates] Logo loaded (raw): {logo_path}")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"[email_templates] Could not read logo: {e}")
        return ""


LOGO_DATA_URI = _load_logo_b64(max_px=90)
# ──────────────────────────────────────────────────────────────────────────────


def _logo_img(size: int = 72, radius: int = 16) -> str:
    """Return an <img> tag for the logo, or empty string if not available."""
    if not LOGO_DATA_URI:
        return ""
    return (
        f'<img src="{LOGO_DATA_URI}" alt="Negen SDD" width="{size}" height="{size}" '
        f'style="display:block;border-radius:{radius}px;background:#fff;'
        f'padding:6px;object-fit:contain;" />'
    )


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL 1 — Account Created
# ══════════════════════════════════════════════════════════════════════════════
def get_account_created_email(
    name: str, email: str, role: str, public_id: str, setup_url: str
) -> tuple[str, str]:
    """Returns (subject, html_body) for the Account Created email."""

    role_colors = {
        "COLLABORATOR": ("#CA5728", "#fff3ee", "#7c2d12"),
        "VIEWER":       ("#3d5a80", "#e8f0f8", "#1e3a5f"),
        "ADMIN":        ("#7c3aed", "#f3f0ff", "#4c1d95"),
    }
    accent, light_bg, dark = role_colors.get(role, ("#CA5728", "#fff3ee", "#7c2d12"))
    role_label = role.capitalize()
    initial = name[0].upper() if name else "U"

    subject = "Welcome to Negen SDD \u2013 Your Account is Ready"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Welcome to Negen SDD</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f1f5f9;padding:32px 12px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;width:100%;">

  <!-- HEADER -->
  <tr>
    <td style="background:linear-gradient(135deg,#CA5728,#8b2e0e);border-radius:18px 18px 0 0;padding:32px;text-align:center;">
      <table cellpadding="0" cellspacing="0" border="0" align="center">
        <tr>
          <td style="padding-right:12px;vertical-align:middle;">{_logo_img(72, 18)}</td>
          <td style="vertical-align:middle;text-align:left;">
            <div style="font-size:22px;font-weight:900;color:#fff;letter-spacing:-0.5px;">Negen SDD</div>
            <div style="font-size:10px;color:rgba(255,255,255,0.65);letter-spacing:2px;text-transform:uppercase;margin-top:2px;">Secure Document Dissemination</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- BODY -->
  <tr>
    <td style="background:#fff;padding:32px 32px 0;">
      <h1 style="margin:0 0 8px;font-size:22px;font-weight:800;color:#1e293b;">Welcome, {name}! &#128075;</h1>
      <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;">
        Your Negen SDD account has been created. Here are your credentials — activate your account using the button below.
      </p>

      <!-- LIGHT ID CARD -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:#f8fafc;border:2px solid #e2e8f0;border-radius:16px;margin-bottom:24px;">
        <tr>
          <td width="6" style="background:{accent};border-radius:14px 0 0 14px;">&nbsp;</td>
          <td style="padding:22px 20px;">

            <!-- Card header -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:16px;">
              <tr>
                <td>
                  <div style="font-size:9px;font-weight:700;letter-spacing:2px;color:#94a3b8;text-transform:uppercase;">Identity Card</div>
                  <div style="font-size:10px;color:#cbd5e1;margin-top:1px;">Negen SDD Portal</div>
                </td>
                <td align="right">
                  <span style="background:{accent};color:#fff;font-size:10px;font-weight:700;
                               padding:3px 12px;border-radius:999px;text-transform:uppercase;letter-spacing:0.5px;">
                    {role_label}
                  </span>
                </td>
              </tr>
            </table>

            <!-- Avatar + name -->
            <table cellpadding="0" cellspacing="0" border="0" style="margin-bottom:16px;">
              <tr>
                <td style="padding-right:14px;">
                  <table cellpadding="0" cellspacing="0" border="0">
                    <tr>
                      <td style="width:54px;height:54px;border-radius:50%;background:{light_bg};
                                 text-align:center;vertical-align:middle;font-size:22px;
                                 font-weight:800;color:{accent};line-height:54px;
                                 border:2px solid {accent};">
                        {initial}
                      </td>
                    </tr>
                  </table>
                </td>
                <td>
                  <div style="font-size:18px;font-weight:800;color:#1e293b;">{name}</div>
                  <div style="font-size:12px;color:#64748b;margin-top:2px;">{email}</div>
                </td>
              </tr>
            </table>

            <!-- Divider -->
            <div style="height:1px;background:#e2e8f0;margin-bottom:14px;"></div>

            <!-- ID + role row -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td>
                  <div style="font-size:9px;font-weight:600;letter-spacing:1px;color:#94a3b8;text-transform:uppercase;margin-bottom:4px;">User ID</div>
                  <span style="font-family:'Courier New',monospace;font-size:12px;font-weight:700;
                               color:#1e293b;background:#e2e8f0;padding:4px 10px;border-radius:6px;">
                    {public_id}
                  </span>
                </td>
                <td align="right">
                  <div style="font-size:9px;font-weight:600;letter-spacing:1px;color:#94a3b8;text-transform:uppercase;margin-bottom:4px;">Access Level</div>
                  <span style="font-size:13px;font-weight:700;color:{accent};">{role_label}</span>
                </td>
              </tr>
            </table>

          </td>
        </tr>
      </table>
      <!-- END ID CARD -->

      <!-- Info box -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:24px;">
        <tr>
          <td style="background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:12px;padding:14px 16px;
                     font-size:13px;color:#475569;line-height:1.6;">
            &#128272; <strong style="color:#1e293b;">Next Step:</strong>
            Click below to set your password. The link is time-sensitive.
          </td>
        </tr>
      </table>

      <!-- CTA -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:32px;">
        <tr>
          <td align="center">
            <a href="{setup_url}"
               style="display:inline-block;background:linear-gradient(135deg,#CA5728,#8b2e0e);
                      color:#fff;font-size:15px;font-weight:700;text-decoration:none;
                      padding:14px 44px;border-radius:12px;letter-spacing:0.3px;">
              &#10022; &nbsp;Activate My Account
            </a>
          </td>
        </tr>
      </table>

      <div style="height:1px;background:#f1f5f9;"></div>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#f8fafc;border-radius:0 0 18px 18px;padding:20px 32px;text-align:center;">
      <p style="margin:0 0 4px;font-size:11px;color:#94a3b8;">If you did not expect this email, you can safely ignore it.</p>
      <p style="margin:0;font-size:11px;color:#cbd5e1;">
        &copy; 2025 <strong style="color:#CA5728;">Negen SDD</strong> &mdash; Secure Document Dissemination Platform
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    return subject, html


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL 2 — Password Reset
# ══════════════════════════════════════════════════════════════════════════════
def get_password_reset_email(name: str, email: str, reset_url: str) -> tuple[str, str]:
    """Returns (subject, html_body) for the Password Reset email."""

    subject = "Negen SDD \u2013 Password Reset Request"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Reset Your Password</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f1f5f9;padding:32px 12px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;width:100%;">

  <!-- HEADER -->
  <tr>
    <td style="background:linear-gradient(135deg,#1e293b,#0f172a);border-radius:18px 18px 0 0;padding:32px;text-align:center;">
      <table cellpadding="0" cellspacing="0" border="0" align="center" style="margin-bottom:20px;">
        <tr>
          <td style="padding-right:12px;vertical-align:middle;">{_logo_img(72, 18)}</td>
          <td style="vertical-align:middle;text-align:left;">
            <div style="font-size:22px;font-weight:900;color:#fff;letter-spacing:-0.5px;">Negen SDD</div>
            <div style="font-size:10px;color:rgba(255,255,255,0.4);letter-spacing:2px;text-transform:uppercase;margin-top:2px;">Secure Document Dissemination</div>
          </td>
        </tr>
      </table>
      <div style="display:inline-block;background:rgba(202,87,40,0.15);border:2px solid rgba(202,87,40,0.35);
                  border-radius:50%;width:52px;height:52px;line-height:52px;font-size:24px;margin-bottom:12px;">
        &#128273;
      </div>
      <div style="font-size:22px;font-weight:900;color:#fff;margin-bottom:4px;">Password Reset</div>
      <p style="margin:0;color:rgba(255,255,255,0.4);font-size:11px;letter-spacing:1.5px;text-transform:uppercase;">
        Security &bull; Account Access
      </p>
    </td>
  </tr>

  <!-- BODY -->
  <tr>
    <td style="background:#fff;padding:32px 32px 0;">
      <h2 style="margin:0 0 8px;font-size:20px;font-weight:800;color:#1e293b;">Hi, {name}!</h2>
      <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.7;">
        We received a request to reset the password for the Negen SDD account associated with
        <strong style="color:#1e293b;">{email}</strong>.
        If this was you, click the button below to choose a new password.
      </p>

      <!-- CTA -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:20px;">
        <tr>
          <td align="center">
            <a href="{reset_url}"
               style="display:inline-block;background:linear-gradient(135deg,#CA5728,#8b2e0e);
                      color:#fff;font-size:15px;font-weight:700;text-decoration:none;
                      padding:14px 44px;border-radius:12px;letter-spacing:0.3px;">
              &#128274; &nbsp;Reset My Password
            </a>
          </td>
        </tr>
      </table>

      <!-- Warning -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:14px;">
        <tr>
          <td style="background:#fffbeb;border:1.5px solid #fcd34d;border-radius:12px;padding:14px 16px;">
            <table cellpadding="0" cellspacing="0" border="0"><tr>
              <td style="padding-right:10px;font-size:18px;vertical-align:top;">&#9888;&#65039;</td>
              <td style="font-size:13px;color:#92400e;line-height:1.6;">
                <strong>This link will expire shortly.</strong> If it has expired, request a new one from the login page.
              </td>
            </tr></table>
          </td>
        </tr>
      </table>

      <!-- Not you -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:20px;">
        <tr>
          <td style="background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:12px;padding:14px 16px;">
            <table cellpadding="0" cellspacing="0" border="0"><tr>
              <td style="padding-right:10px;font-size:18px;vertical-align:top;">&#128737;&#65039;</td>
              <td style="font-size:13px;color:#475569;line-height:1.6;">
                <strong style="color:#1e293b;">Didn't request this?</strong>
                You can safely ignore this email. Your password will remain unchanged.
              </td>
            </tr></table>
          </td>
        </tr>
      </table>

      <!-- Fallback URL -->
      <p style="font-size:11px;color:#94a3b8;margin:0 0 24px;line-height:1.6;word-break:break-all;">
        Button not working? Paste this link in your browser:<br/>
        <span style="color:#CA5728;">{reset_url}</span>
      </p>

      <div style="height:1px;background:#f1f5f9;"></div>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#f8fafc;border-radius:0 0 18px 18px;padding:20px 32px;text-align:center;">
      <p style="margin:0 0 4px;font-size:11px;color:#94a3b8;">This is an automated security email. Please do not reply.</p>
      <p style="margin:0;font-size:11px;color:#cbd5e1;">
        &copy; 2025 <strong style="color:#CA5728;">Negen SDD</strong> &mdash; Secure Document Dissemination Platform
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    return subject, html
