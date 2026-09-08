# PRAGATI AI — Render.com 1-Click Deployment Guide
**SIH26122 - Oil India Limited | Team: InfraNexus**

This repository is pre-configured for 100% plug-and-play cloud deployment on [Render.com](https://render.com) (Free Tier).

---

## 🚀 Quick Deployment (3 Simple Steps)

### Step 1: Push Code to GitHub
Open your terminal in `d:\Projects\Pragati AI` and run:

```bash
# 1. Initialize git (if not already done)
git init

# 2. Stage all project files (.gitignore will automatically skip venv and temporary files)
git add .

# 3. Create initial commit
git commit -m "feat: complete PRAGATI AI demo-ready deployment"

# 4. Link to your GitHub repository (replace with your actual GitHub repo URL)
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/pragati-ai.git
git push -u origin main
```

---

### Step 2: Deploy on Render.com

#### Option A: Blueprint Deploy (Automatic - Recommended)
Because this repository includes [`render.yaml`](./render.yaml), Render can configure everything automatically:
1. Log in to [Render.com](https://render.com).
2. Click **"New +"** in the top navigation bar and select **"Blueprint"**.
3. Connect your GitHub repository (`pragati-ai`).
4. Render will detect `render.yaml` and set up the Web Service automatically.
5. Click **"Apply"**!

---

#### Option B: Manual Web Service Setup
If creating a Web Service manually:
1. Click **"New +"** -> **"Web Service"**.
2. Connect your GitHub repository (`pragati-ai`).
3. Fill in the following settings:
   - **Name**: `pragati-ai` (or your preferred name)
   - **Region**: Choose the closest region (e.g., *Singapore* or *Oregon*)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python scripts/generate_dataset.py && python scripts/seed_demo.py
     ```
   - **Start Command**:
     ```bash
     python run.py
     ```
   - **Plan**: `Free`

4. Add **Environment Variables** (under *Advanced*):
   - `AI_PROVIDER`: `fallback` *(ensures 100% offline-resilient AI without requiring external API keys)*
   - `PORT`: `10000` *(Render sets this automatically, but good to have)*
   - *(Optional)* `GEMINI_API_KEY`: *(paste your Google Gemini API key here if you want live cloud LLM extraction)*

5. Click **"Create Web Service"**.

---

## 🌐 What Render Will Provide

Once the build finishes (typically ~1.5 - 2 minutes):
- **Live HTTPS URL**: e.g., `https://pragati-ai.onrender.com`
- **Health Check**: `https://pragati-ai.onrender.com/health`
- **Interactive Swagger Docs**: `https://pragati-ai.onrender.com/docs`
- **Planner Dashboard**: `https://pragati-ai.onrender.com/`

---

## 📱 Mobile Friendly & Judge Inspection Ready

The deployed web app is fully responsive:
- **Laptops / Desktops**: Full multi-column view with live schedule Gantt/activity browser, AI extraction inspector, side-by-side evidence diffs, and audit logs.
- **Tablets & Mobile Phones**: High-contrast touch-friendly cards, stacked DPR upload & match review cards, and direct 1-tap buttons for SIH judges to test on their smartphones.
