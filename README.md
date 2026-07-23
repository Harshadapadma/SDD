<div align="center">

# 🛡️ Negen SDD (Structured Digital Database)

### *Enterprise-Grade SEBI PIT Compliance & UPSI Security System*

[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-8.x-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST](https://img.shields.io/badge/Django_REST-Framework-red?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Security Hardened](https://img.shields.io/badge/Security-SEBI_Audit_Ready-orange?style=for-the-badge&logo=shieldsdotio&logoColor=white)](#-security--compliance-posture)

---

<p align="center">
  <b>Negen SDD</b> is a state-of-the-art Structured Digital Database engineered to satisfy <b>SEBI (Prohibition of Insider Trading) Regulations</b>. It provides corporate entities, compliance officers, and market participants with a non-tamperable, multi-tiered platform to manage <b>Unpublished Price Sensitive Information (UPSI)</b>, track legal disclosures, and maintain immutable audit trails.
</p>

</div>

---

## 🌟 Executive Overview

In compliance with SEBI PIT Regulation 3(5) & 3(6), listed companies and designated intermediaries must maintain a structured digital database containing the names, PANs, and disclosure details of persons with whom UPSI is shared. 

**Negen SDD** addresses these requirements with an enterprise-grade platform featuring:

- 🔒 **Immutable Audit Trail**: Every creation, modification, access request, and role change is permanently captured with cryptographic timestamps.
- 🛡️ **Zero-Trust Security**: HttpOnly cookie-based JWT authentication, Email OTP Multi-Factor Authentication (MFA), and automated account lockout.
- 👥 **Four-Tier Access Control**: Strict privilege separation for **Admin**, **Compliance Officer**, **Collaborator**, and **Viewer**.
- 📋 **Multi-Stage Workflow Clearance**: Request-approval pipelines for record creation, editing, deletion, and role upgrades with built-in clarification messaging.
- 💎 **Glassmorphic Tactile Interface**: Micro-animated Vue 3 frontend offering dynamic visual clarity and responsive dashboard analytics.

---

## 🚀 Key Features & Capability Matrix

| Feature | Description | Target Role |
| :--- | :--- | :---: |
| **UPSI Record Vault** | Track PAN, recipient company, disclosure source, and nature of UPSI with timestamping. | Compliance Officer / Collaborator |
| **Granular Authorization (RBAC)** | Per-record permission management with restricted view-only access for Viewers. | All Roles |
| **Email OTP MFA** | 2FA verification via 6-digit email OTP for high-privilege roles. | Admin & Compliance Officer |
| **Clearance Workflows** | Structured request pipeline with interactive clarification threads before approval. | Compliance Officer & Users |
| **Automated Inactivity Lock** | 15-minute idle timer with modal password re-verification to protect unattended screens. | All Users |
| **Real-time Notifications** | System notifications for status changes, role updates, and pending clearances. | All Users |
| **Compliance Analytics** | Infographic dashboard reporting database metrics, growth trends, and workflow clearance stats. | Admin & Compliance Officer |

---

## 🛡️ Security & Compliance Posture

```
                               ┌──────────────────────────────────────────┐
                               │           Client Browser (SPA)           │
                               └────────────────────┬─────────────────────┘
                                                    │
                                   Bearer Access    │   HttpOnly Cookie
                                   Token (Memory)   │   (sdd_refresh_token)
                                                    ▼
                               ┌──────────────────────────────────────────┐
                               │  Content Security Policy & Security HW    │
                               └────────────────────┬─────────────────────┘
                                                    │
                                                    ▼
                               ┌──────────────────────────────────────────┐
                               │        Django REST API Gateway           │
                               │  - Anti-Brute-Force Rate Throttling      │
                               │  - Account Lockout Enforcement           │
                               │  - Security Event Logger (security.log)  │
                               └────────────────────┬─────────────────────┘
                                                    │
                                                    ▼
                               ┌──────────────────────────────────────────┐
                               │       Encrypted Relational Storage        │
                               │  (AES-256 Storage & Token Blacklist)     │
                               └──────────────────────────────────────────┘
```

1. **HttpOnly Refresh Cookies**: Refresh tokens are stored in `HttpOnly`, `SameSite=Lax/Strict`, `Secure` cookies — immune to XSS token theft.
2. **Token Rotation & Blacklisting**: Single-use refresh token rotation invalidates old tokens upon renewal and immediate server-side revocation on logout.
3. **Anti-Brute-Force Lockout**: Automatically locks accounts for 15 minutes after 10 failed login attempts.
4. **Content Security Policy (CSP)**: Strict HTTP response headers (`CSP`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`).
5. **Session Lifetime Tuning**: Short-lived 15-minute access tokens minimize exposure windows.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend Framework** | Vue 3 (Composition API, `<script setup lang="ts">`), TypeScript |
| **Build & Styling** | Vite 8, Vanilla CSS3 (Custom Glassmorphism Tokens), Font Awesome 6 |
| **State & Routing** | Vue Router 4, Axios (Cross-Origin Cookie Credentials) |
| **Backend Framework** | Python 3.10+, Django 5.x, Django REST Framework |
| **Authentication** | SimpleJWT (Token Blacklist), Custom Email OTP Engine, Custom RBAC Backend |
| **Security & Logging** | Custom Security Logger, DRF Throttling, SecurityHeadersMiddleware |
| **Database Support** | SQLite (Development), PostgreSQL 16 (Production Target) |

---

## 📁 Repository Architecture

```text
Negen SDD/
├── backend/
│   ├── apps/
│   │   ├── users/           # User authentication, RBAC, MFA, security models
│   │   ├── records/         # UPSI records, encryption, per-record permissions
│   │   ├── workflows/       # Request clearance engine & clarification messaging
│   │   └── notifications/   # System alert system & notifications
│   ├── config/              # Django settings, security middleware, URL routes
│   ├── requirements.txt     # Python backend dependencies
│   └── manage.py            # Django CLI management entrypoint
│
└── frontend/
    ├── src/
    │   ├── api/             # Axios client with credentials & auth interceptors
    │   ├── composables/     # Inactivity session lock & notification hooks
    │   ├── Layouts/         # Admin, User, and Navigation Layouts
    │   ├── router/          # Vue Router definitions & role guards
    │   ├── views/           # Admin & User views (Dashboards, Records, Requests)
    │   └── App.vue          # Root application & session lock modal
    ├── package.json         # Node dependencies & build scripts
    └── vite.config.ts       # Vite bundler configuration
```

---

## 🚦 Local Installation & Setup

### Prerequisites
- **Python** `3.10+`
- **Node.js** `18+` & `npm`

---

### 1️⃣ Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install backend dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the `backend/` directory:
   ```env
   # Security Configuration
   SECRET_KEY=your-secure-64-character-random-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # SMTP Email Configuration (For MFA & Setup Links)
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-email@example.com
   EMAIL_HOST_PASSWORD=your-app-password-here

   # Initial Setup Credentials
   ADMIN_NAME=Administrator
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=your-admin-password

   COMPLIANCE_NAME=Compliance Officer
   COMPLIANCE_EMAIL=compliance@example.com
   COMPLIANCE_PASSWORD=your-compliance-password

   # Frontend URL
   FRONTEND_URL=http://localhost:5173
   ```

5. **Run database migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Initialize default administrator accounts**:
   ```bash
   python manage.py setup_admin
   ```

7. **Start the Django development server**:
   ```bash
   python manage.py runserver
   ```
   *Backend REST API running at `http://127.0.0.1:8000/`*

---

### 2️⃣ Frontend Setup

1. **Open a new terminal and navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   *Frontend application running at `http://localhost:5173/`*

4. **Verify TypeScript & Production Build**:
   ```bash
   npm run build
   ```

---

## 🌐 Production Deployment Guide (Render / Cloud)

When deploying Negen SDD to Render or cloud infrastructure:

1. **Database**: Provision a managed **PostgreSQL 16** instance and set `DATABASE_URL` in environment variables.
2. **Environment Variables**:
   - Set `DEBUG=False`
   - Set `FRONTEND_URL=https://your-app-name.onrender.com`
   - Set `CORS_ALLOWED_ORIGINS=https://your-app-name.onrender.com`
   - Set a strong 64-character `SECRET_KEY`
3. **Static Files & HTTPS**: Enable TLS/SSL certificates and configure `SECURE_PROXY_SSL_HEADER`.

---

## 📄 License & Compliance Disclaimer

*This software is designed to assist corporate organizations in maintaining compliance with SEBI (Prohibition of Insider Trading) Regulations. Users should consult their legal and compliance departments for organization-specific insider trading policies.*

---

<div align="center">
  <sub>Built with ❤️ by Negen SDD Team</sub>
</div>
