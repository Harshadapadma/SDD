<div align="center">
  <h1>🌟 Negen SDD</h1>
  <p><i>A comprehensive, modern web application featuring a glassmorphic Vue 3 frontend and a robust Django backend.</i></p>
</div>

---

## ✨ Features
- 🎨 **Modern Interface**: Beautiful, responsive, and intuitive glassmorphic design system.
- 🔐 **Secure Authentication**: Robust role-based access control and user validation.
- ⚡ **High Performance**: Powered by Vite and Vue 3 for a lightning-fast frontend experience.
- 🛡️ **Reliable Backend**: Django-powered RESTful APIs.

---

## 🛠️ Prerequisites
Before you begin, ensure you have the following installed on your machine:
- **Python** (v3.8 or higher)
- **Node.js** (v18 or higher)
- **npm** or **yarn**

---

## 🚀 Getting Started

Follow these instructions to set up and run the project on your local machine.

### 1️⃣ Backend Setup (Django)

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run database migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Setup the admin account**:
   Create the initial admin user using the credentials specified in your `.env` file:
   ```bash
   python manage.py setup_admin
   ```

7. **Run the development server**:
   ```bash
   python manage.py runserver
   ```
   *The backend server will start on `http://127.0.0.1:8000/`*

---

### 2️⃣ Frontend Setup (Vue 3 + Vite)

Open a **new terminal window** to run the frontend server simultaneously.

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install the dependencies**:
   ```bash
   npm install
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```
   *The frontend server will start (typically on `http://localhost:5173/`). Follow the terminal prompt to open it in your browser.*

---

## 🏗️ Project Structure
```text
Negen SDD/
├── backend/          # Django application, APIs, and database models
│   ├── apps/         # Django apps (e.g., users, records)
│   ├── config/       # Django project settings
│   ├── requirements.txt # Python dependencies
│   └── manage.py     # Django management script
└── frontend/         # Vue 3 application built with Vite
    ├── src/          # Vue components, views, and assets
    ├── package.json  # Node dependencies and scripts
    └── vite.config.ts # Vite configuration
```

---

## 🤝 Contribution

Contributions, issues, and feature requests are welcome! Feel free to check the issues page if you want to contribute.
