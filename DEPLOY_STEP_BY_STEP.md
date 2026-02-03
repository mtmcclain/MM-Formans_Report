# Deploy to Streamlit Cloud — Step-by-Step (Beginner Guide)

This guide walks you through putting the Foreman's Report app on the internet so you can use it from your iPad (or any device) without running it on your PC.

---

## Step 1: Get a GitHub account and put your code there

### 1.1 Create a GitHub account (if you don’t have one)

1. Go to **https://github.com**
2. Click **Sign up**
3. Enter email, password, and username; complete sign-up

### 1.2 Create a new repository on GitHub

1. Log in to GitHub
2. Click the **+** (plus) at the top right → **New repository**
3. Fill in:
   - **Repository name**: e.g. `MM-Formans_Report` (or any name you like)
   - **Description**: optional, e.g. "Foreman's Report app"
   - Leave **Public** selected
   - **Do not** check "Add a README" (you already have code)
4. Click **Create repository**

### 1.3 Push your project folder to GitHub

You’ll do this from your PC, in the folder where your app code lives (e.g. `MM-Formans_Report`).

**If this is the first time you’re pushing this folder to GitHub:**

1. Open **PowerShell** (or Terminal)
2. Go to your project folder:
   ```powershell
   cd C:\MartinMechVDC\PaperWork\Paperwork_Automation\MartinMechAPP_repository\MM-Formans_Report
   ```
3. Turn the folder into a Git repo (if it isn’t already):
   ```powershell
   git init
   ```
4. Add GitHub as the remote (replace `YOUR_USERNAME` and `YOUR_REPO` with your GitHub username and repo name):
   ```powershell
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   ```
   Example: `git remote add origin https://github.com/jsmith/MM-Formans_Report.git`
5. Add all files, commit, and push:
   ```powershell
   git add .
   git commit -m "Initial commit - Foreman Report app"
   git branch -M main
   git push -u origin main
   ```
6. When asked, sign in to GitHub (browser or token as prompted)

**If the folder is already a Git repo and you’ve already added `origin`:**

1. Open PowerShell in the project folder (same `cd` as above)
2. Run:
   ```powershell
   git add .
   git status
   ```
   Check that the files you expect are listed.
3. Commit and push:
   ```powershell
   git commit -m "Add Streamlit Cloud and Postgres support"
   git push origin main
   ```

When Step 1 is done, you should see your code on GitHub when you open `https://github.com/YOUR_USERNAME/YOUR_REPO` in a browser.

---

## Step 2: Deploy the app on Streamlit Community Cloud

### 2.1 Open Streamlit Community Cloud

1. In your browser go to: **https://share.streamlit.io**
2. Click **Sign up** or **Get started**
3. Choose **Continue with GitHub**
4. If asked, authorize Streamlit to use your GitHub account (Authorize, etc.)

### 2.2 Create a new app

1. On the Streamlit Cloud page you should see something like “Welcome” or a list of apps.
2. Click the button **New app** (or **Deploy an app**).
3. You’ll see a form with:
   - **Repository**
   - **Branch**
   - **Main file path**

### 2.3 Fill in the form

1. **Repository**
   - Click the dropdown.
   - You should see your GitHub username and repos.
   - Select the repo you used in Step 1 (e.g. `YOUR_USERNAME/MM-Formans_Report`).
   - If you don’t see it, make sure you’re logged in with the right GitHub account and that the repo is pushed (Step 1).

2. **Branch**
   - Leave **main** (or select the branch where you pushed your code).

3. **Main file path**
   - Type exactly: **app.py**
   - This tells Streamlit which file to run.

4. **App URL** (if shown)
   - You can leave the default, e.g. `https://mm-formans-report.streamlit.app`, or type a short name you like (letters, numbers, hyphens only).

### 2.4 Add your database secret (important)

1. On the same “New app” screen, find and click **Advanced settings** (or **Secrets**).
2. A text box appears for “Secrets” or “TOML”.
3. Paste this, then **replace the placeholder with your real Neon URL** (the one you used for `create_user_simple`):

   ```toml
   DATABASE_URL = "postgresql://neondb_owner:YOUR_PASSWORD@ep-odd-mountain-ahzu9dc8-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
   ```

   - Change only `YOUR_PASSWORD` to your real Neon database password.
   - Do **not** put this file or this password in your code or in a file you commit to GitHub. It stays only in Streamlit’s “Secrets”.

4. Click **Deploy** (or **Save and deploy**).

### 2.5 Wait for the first deploy

- The page will show “Building” or “Deploying” and logs.
- The first time can take a few minutes (installing Python, `requirements.txt`, etc.).
- When it’s done you’ll see “Your app is live” and a link like `https://something.streamlit.app`.

If the build fails, open the log on that page and look for red error lines; those usually say which file or dependency failed.

---

## Step 3: Create the first user in the cloud database

Right after deployment, the cloud database has no users. You create the first one from your PC (one time only).

### 3.1 Set the database URL on your PC (same as Neon)

1. Open **PowerShell**.
2. Go to your project folder:
   ```powershell
   cd C:\MartinMechVDC\PaperWork\Paperwork_Automation\MartinMechAPP_repository\MM-Formans_Report
   ```
3. Set the environment variable (use your **real** Neon URL and password):
   ```powershell
   $env:DATABASE_URL = "postgresql://neondb_owner:YOUR_PASSWORD@ep-odd-mountain-ahzu9dc8-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
   ```
   Replace `YOUR_PASSWORD` with your actual Neon password. This is the same URL you put in Streamlit secrets.

### 3.2 Run the user-creation script

1. In the same PowerShell window, run:
   ```powershell
   python -m create_user_simple
   ```
2. When prompted:
   - **Username**: pick a login name (e.g. `admin` or your name).
   - **Password**: type a password (you’ll use this to log in to the app).
   - **Confirm password**: same password again.
   - **Full name**: optional; press Enter to skip or type your name.
   - **Role**: type **admin** (so you can manage users later).
   - **Email**: optional; press Enter to skip.
3. When you see “User created successfully”, the first user is in the **cloud** Neon database.

### 3.3 Log in to the live app

1. In your browser, open the app URL from Step 2.5 (e.g. `https://something.streamlit.app`).
2. You should see the login page.
3. Enter the **username** and **password** you just created.
4. Click **Login**. You should see the main Foreman’s Report screen.

---

## Step 4: Use the app on your iPad

1. On your iPad, open **Safari** (or Chrome).
2. In the address bar, type or paste the **exact same URL** as on your PC (e.g. `https://something.streamlit.app`).
3. Log in with the same username and password you created in Step 3.
4. The app works the same as on the PC; all data is stored in the cloud database (Neon).

You can bookmark that URL on the iPad so you don’t have to type it each time.

---

## Quick reference

| Step | What you do |
|------|-------------|
| 1 | Put project on GitHub (account → new repo → push from PC). |
| 2 | On share.streamlit.io: New app → pick repo, branch `main`, file `app.py` → Advanced settings → add `DATABASE_URL` secret → Deploy. |
| 3 | On PC: set `DATABASE_URL`, run `python -m create_user_simple`, create one admin user. |
| 4 | Open the app URL in browser or iPad and log in. |

---

## If something goes wrong

- **“Repository not found” on Streamlit**  
  Make sure the repo is **Public** and that you selected the correct GitHub account when connecting Streamlit to GitHub.

- **Build fails with “Module not found”**  
  Check that `requirements.txt` is in the repo and includes at least: `streamlit`, `pymupdf`, `pyyaml`, `psycopg2-binary`.

- **App loads but “could not connect to database”**  
  In Streamlit Cloud → your app → **Settings** (or ⋮) → **Secrets**, check that `DATABASE_URL` is exactly your Neon connection string (no extra spaces, correct password).

- **I can’t log in on the live app**  
  Make sure you created the user **after** setting `DATABASE_URL` to the same Neon URL (Step 3). If you created the user without `DATABASE_URL`, that user was created in local SQLite, not in Neon. Run Step 3 again with `DATABASE_URL` set.

- **Changing the secret later**  
  Streamlit Cloud → your app → **Settings** → **Secrets** → edit the TOML → Save. The app will redeploy with the new secret.
