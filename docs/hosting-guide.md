# PRAGATI AI — Hosting & Live Judge Access Guide

**Team:** InfraNexus  
**Project:** PRAGATI AI  
**Problem Statement:** SIH26122 (Oil India Limited)  

---

## 3 Guaranteed Ways to Show the Live App to Judges

---

### Option 1: Instant Local Wi-Fi / Hotspot Access (No Internet Needed!)
*Best for: Hackathon venues where you want judges to open the app on their own phones or tablets right at your stall.*

1. **Start the server:**
   ```powershell
   python run.py
   ```
   *(The server automatically binds to `0.0.0.0:8000`, making it accessible to any device on the same network).*

2. **Find your laptop's Wi-Fi IP address:**
   In PowerShell, run:
   ```powershell
   ipconfig
   ```
   Look for **IPv4 Address** under `Wireless LAN adapter Wi-Fi` (e.g., `192.168.1.45` or `192.168.43.120`).

3. **Tell the judge or open on your phone:**
   Visit:
   👉 **`http://<YOUR-IP>:8000`** *(e.g., `http://192.168.1.45:8000`)*

4. **Generate a QR Code (Pro Tip):**
   Paste `http://<YOUR-IP>:8000` into any free QR code generator (or Edge/Chrome right-click "Create QR code for this page") and print/display it on your stall. Judges can scan and browse instantly!

---

### Option 2: Instant 1-Command Public HTTPS URL (Cloudflare / Localtunnel)
*Best for: Creating a secure live HTTPS link that judges can access from any network or 5G.*

#### Method A: Using Free Cloudflare Tunnel (Recommended — No signup required)
1. Download `cloudflared.exe` or run via winget / chocolatey:
   ```powershell
   # Run tunnel directly to port 8000:
   cloudflared tunnel --url http://localhost:8000
   ```
2. Cloudflare will output a public HTTPS URL like:
   👉 `https://random-subdomain.trycloudflare.com`

#### Method B: Using LocalTunnel (If Node/npx is available)
```powershell
npx localtunnel --port 8000
```

---

### Option 3: Free Cloud Hosting on Render.com (Permanent 24/7 Deployment)
*Best for: A permanent live demo link you can submit in the SIH portal.*

1. **Push your code to GitHub:**
   ```powershell
   git add .
   git commit -m "Deploy PRAGATI AI demo prototype"
   git push origin main
   ```

2. **Deploy on Render (Free Web Service):**
   - Go to [render.com](https://render.com) & click **New + &rarr; Web Service**.
   - Connect your GitHub repository.
   - Configure:
     - **Name:** `pragati-ai`
     - **Environment:** `Python 3`
     - **Build Command:**
       ```bash
       pip install -r requirements.txt && python scripts/generate_dataset.py && python scripts/seed_demo.py
       ```
     - **Start Command:**
       ```bash
       python run.py
       ```
   - Click **Deploy Web Service**!
   - Render gives you a free permanent HTTPS link like `https://pragati-ai.onrender.com`.

---

## Pre-Flight Hosting Checklist

- [x] **Mobile Responsive:** Verified with responsive media queries (`<= 768px` and `<= 480px`) with touch-friendly controls.
- [x] **Official Logo:** Branding placed in header and favicon linked.
- [x] **Host Binding:** `run.py` configured with `0.0.0.0` to permit LAN, mobile, and cloud connections.
- [x] **Dependencies:** `requirements.txt` and `Procfile` created for cloud deployment.
- [x] **CORS:** Enabled with `allow_origins=["*"]` in `backend/app/main.py`.
- [x] **Offline Fallback:** Evaluates matching locally without internet dependencies.
- [x] **One-Click Reset:** "Reset Demo" button enables instant rehearsal cleanup.
