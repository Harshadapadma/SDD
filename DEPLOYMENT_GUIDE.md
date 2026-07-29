# Step-by-Step Deployment Guide: Render (Frontend) & Firebase (Backend + Database)

This guide provides step-by-step instructions to deploy your **Vue Frontend on Render (Manual Static Site, No Blueprint)** and your **Django Backend & Database on Firebase (Cloud Functions + Cloud SQL PostgreSQL)**.

---

## 1. Step-by-Step Backend & Database Deployment on Firebase

### Step 1.1: Firebase CLI & Authentication
1. Ensure Node.js is installed on your computer.
2. Install the Firebase CLI globally:
   ```bash
   npm install -g firebase-tools
   ```
3. Log into your Firebase account:
   ```bash
   firebase login
   ```

### Step 1.2: Associate Your Firebase Project ID
1. Open `.firebaserc` in the project root.
2. Replace `YOUR-FIREBASE-PROJECT-ID` with your actual Firebase Project ID from the [Firebase Console](https://console.firebase.google.com/):
   ```json
   {
     "projects": {
       "default": "your-actual-firebase-project-id"
     }
   }
   ```

### Step 1.3: Provision PostgreSQL Database on Firebase / Google Cloud
Django requires a relational SQL database. Firebase projects run on Google Cloud Platform (GCP):
1. Open your GCP Console for your Firebase Project ([console.cloud.google.com](https://console.cloud.google.com)).
2. Navigate to **Cloud SQL** -> **Create Instance** -> Choose **PostgreSQL**.
3. Set database credentials and create a database named `negen_sdd_db`.
4. Obtain your PostgreSQL Connection String:
   `postgres://username:password@public_ip_or_cloudsql:5432/negen_sdd_db`
   *(Alternatively, you can use a free cloud PostgreSQL provider like Supabase or Neon and link it to your Firebase project)*.

### Step 1.4: Set Backend Environment Variables
Set production environment variables in Firebase Cloud Functions using Google Cloud Secrets Manager via Firebase CLI:
```bash
firebase functions:secrets:set SECRET_KEY
firebase functions:secrets:set DATABASE_URL
```
*(Or create a `backend/.env` file with `SECRET_KEY`, `DATABASE_URL`, `DEBUG=False`, `ALLOWED_HOSTS=.cloudfunctions.net,.run.app,localhost`, `FRONTEND_URL=https://negen-sdd-frontend.onrender.com`, `SECURE_COOKIE=True`)*.

### Step 1.5: Deploy Backend to Firebase Cloud Functions
Run the deploy command from the project root:
```bash
firebase deploy --only functions
```
Once deployment finishes, Firebase CLI will print your live backend endpoint URL:
```text
https://us-central1-YOUR-FIREBASE-PROJECT-ID.cloudfunctions.net/api/
```

---

## 2. Step-by-Step Frontend Deployment on Render (Manual / No Blueprint)

No Blueprint instance required. Follow these steps to set up your static site directly in the Render Dashboard:

### Step 2.1: Connect GitHub Repository to Render
1. Log into your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** -> **Static Site** *(Do NOT select Blueprint)*.
3. Connect your GitHub repository containing the codebase.

### Step 2.2: Configure Static Site Settings
Fill in the deployment configuration:
- **Name**: `negen-sdd-frontend`
- **Root Directory**: `frontend`
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `dist`

### Step 2.3: Add Environment Variables
Under the **Environment** tab on Render, click **Add Environment Variable**:
- **Key**: `VITE_API_BASE_URL`
- **Value**: `https://us-central1-YOUR-FIREBASE-PROJECT-ID.cloudfunctions.net/api/` *(Use the backend URL output by Firebase deployment in Step 1.5)*.

### Step 2.4: Configure Single-Page Application (SPA) Rewrite Rule
Under the **Redirects/Rewrites** tab on Render, add a rewrite rule so Vue Router works on page refreshes:
- **Source**: `/*`
- **Destination**: `/index.html`
- **Action**: `Rewrite`

### Step 2.5: Deploy Site
Click **Create Static Site**. Render will build and publish your Vue app to a URL like `https://negen-sdd-frontend.onrender.com`.

---

## 3. Verification & Testing

- [ ] Firebase Cloud Function backend returns valid JSON / API response at `https://us-central1-YOUR-FIREBASE-PROJECT-ID.cloudfunctions.net/api/auth/login/`.
- [ ] Render Frontend loads properly at `https://negen-sdd-frontend.onrender.com`.
- [ ] Log in with your admin credentials to verify full end-to-end functionality.
