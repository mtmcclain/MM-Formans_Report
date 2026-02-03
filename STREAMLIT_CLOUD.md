# Run the app on Streamlit Community Cloud

You can run the Foreman's Report app on **Streamlit Community Cloud** so it’s available from any device (including your iPad) without running it on your PC.

> **New to deploying?** See **DEPLOY_STEP_BY_STEP.md** for a detailed, beginner-friendly walkthrough of each step (GitHub, push, Streamlit signup, deploy, secrets, first user, iPad).

## Requirements

1. **GitHub** – Your app code in a GitHub repository.
2. **PostgreSQL database** – Streamlit Cloud doesn’t keep files between restarts, so the app uses a **cloud PostgreSQL** database when `DATABASE_URL` is set.

## 1. Create a free PostgreSQL database

Use one of these (free tiers are enough for this app):

- **[Neon](https://neon.tech)** – Sign up, create a project, copy the connection string (e.g. `postgresql://user:pass@host/dbname?sslmode=require`).
- **[Supabase](https://supabase.com)** – Create a project → Settings → Database → Connection string (URI).
- **[ElephantSQL](https://www.elephantsql.com)** – Create a instance, copy the URL.

Keep the URL secret; you’ll add it as a secret in Streamlit Cloud.

## 2. Deploy on Streamlit Community Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.
2. Click **“New app”**.
3. Choose:
   - **Repository**: `YourOrg/MM-Formans_Report` (or your fork).
   - **Branch**: `main`.
   - **Main file path**: `app.py`.
4. Click **“Advanced settings”** and add a secret:
   - **Key**: `DATABASE_URL`
   - **Value**: your PostgreSQL connection string (e.g. `postgresql://user:pass@host/dbname?sslmode=require`).
5. Click **“Deploy”**.

Streamlit will install dependencies from `requirements.txt`, set `DATABASE_URL`, and start the app. Tables are created automatically on first run.

## 3. Create the first user (cloud database starts empty)

After the app is deployed, the database has no users. Create an admin from your PC once:

1. Set your cloud database URL locally (PowerShell):
   ```powershell
   $env:DATABASE_URL = "postgresql://user:pass@host/dbname?sslmode=require"
   ```
2. Run the user-creation script (from the repo root):
   ```powershell
   python create_user_simple.py
   ```
   Enter username, password, full name, and choose role `admin` when prompted.
3. Open the deployed app URL in your browser or on your iPad and log in with that user.

## 4. After deployment

- **URL**: You’ll get a link like `https://your-app-name.streamlit.app`. Open it on your iPad (or any browser).
- **Local vs cloud**:  
  - **No `DATABASE_URL`** (e.g. on your PC): app uses **SQLite** in the `data/` folder.  
  - **With `DATABASE_URL`** (Streamlit Cloud): app uses **PostgreSQL**; data persists in the cloud DB.

## 5. Optional: `packages.txt` for system libraries

If you see errors about missing system libraries (e.g. for PDFs), add a `packages.txt` in the repo root with the needed packages (Streamlit Cloud uses Ubuntu). For many setups, `requirements.txt` is enough.

## Summary

| Where you run      | Database   | Use case                    |
|--------------------|------------|-----------------------------|
| Your PC (local)    | SQLite     | Development / local use     |
| Streamlit Cloud    | PostgreSQL | Use from iPad / anywhere    |

Set `DATABASE_URL` only in Streamlit Cloud secrets so the app automatically uses PostgreSQL there and SQLite when you run it locally.
