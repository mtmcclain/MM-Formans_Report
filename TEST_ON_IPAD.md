# Testing on iPad

## Option 1: Same Wi‑Fi (PC runs app, iPad opens in browser)

1. **On your PC** (in the project folder):
   ```bash
   streamlit run app.py --server.address 0.0.0.0
   ```
   This lets other devices on your network connect.

2. **Find your PC’s IP address**
   - Windows: `ipconfig` → look for "IPv4 Address" (e.g. `192.168.1.100`)
   - Or: Settings → Network → your Wi‑Fi → details

3. **On your iPad** (Safari or Chrome):
   - Open: `http://YOUR_PC_IP:8501`  
     Example: `http://192.168.1.100:8501`

4. **First time on this machine:** Create a user if needed:
   ```bash
   python create_user_interactive.py
   ```
   Then log in on the iPad with that username and password.

**Note:** The PC must stay on and the Streamlit window open. If the PC sleeps, the connection will drop.

---

## Option 2: Deploy online (e.g. Streamlit Community Cloud)

- Push this repo to GitHub, then connect it at [share.streamlit.io](https://share.streamlit.io) and deploy the app.
- You’ll get a public URL you can open on the iPad from anywhere (no same Wi‑Fi needed).
- You’ll need to add the database (and any secrets) via Streamlit’s config; the free tier has limits.

---

## iPad tips

- Use **Safari** or **Chrome**; request “Desktop site” if the layout looks mobile.
- **Save & Load** and **Generate Weekly PDFs** work the same; use “Save current report” then “Create PDF of Current Report” or the weekly section as needed.
- For long sessions, keep the iPad awake or the tab in the foreground so the connection doesn’t time out.
