# 🔒 Security & Deployment Guide

## ✅ GOOD NEWS: Your GEE Credentials Are Safe!

Your Google Earth Engine authentication is **NOT exposed** by this code and is safe to share on GitHub.

---

## 🔐 How GEE Authentication Works

### What's Stored Where

**Your Local Machine** (PRIVATE - not in repo):
```
~/.config/earthengine/credentials
```
- OAuth2 access tokens
- Refresh tokens
- **NEVER committed to Git**
- Created by running: `earthengine authenticate`

**In Your Code** (PUBLIC - safe to share):
```python
gee_project = st.sidebar.text_input(
    "Google Earth Engine Project ID",
    value="joburg-hvi"
)
```
- Only the **project ID** (e.g., "joburg-hvi")
- Project IDs are not secret
- They're like usernames, not passwords

### Authentication Flow

1. **You authenticate locally**:
   ```bash
   earthengine authenticate
   ```
   - Opens browser for Google login
   - Saves credentials to `~/.config/earthengine/credentials`
   - This file is NEVER in your Git repo

2. **App uses your credentials**:
   ```python
   ee.Initialize(project="joburg-hvi")
   ```
   - Reads from `~/.config/earthengine/credentials`
   - No API keys in code
   - No secrets exposed

3. **Others using your app**:
   - Must run `earthengine authenticate` themselves
   - Use their own GEE accounts
   - Use their own project IDs

---

## 📦 What's Safe to Share on GitHub

### ✅ Safe to Commit

All your code is safe:
- ✅ `app/climate_health_app.py` - App code
- ✅ `src/climate_toolkit/` - Package code
- ✅ `examples/` - Example scripts
- ✅ `tests/` - Test files
- ✅ `docs/` - Documentation
- ✅ `pyproject.toml` - Dependencies
- ✅ `README.md` - Instructions

### ❌ Should NOT Commit (Add to .gitignore)

```gitignore
# Credentials
.config/
credentials.json
*.pem

# GEE authentication
earthengine-credentials

# Environment variables
.env
.env.local

# Data files (optional)
*.csv
*.nc
*.tif
app/test_outputs/

# Cache
__pycache__/
.pytest_cache/
*.pyc

# User-specific
.vscode/
.idea/
.DS_Store
```

---

## 🌐 GitHub Pages Limitations

**IMPORTANT: Your current app CANNOT run on GitHub Pages**

### Why Not?

GitHub Pages only supports:
- ❌ Static HTML/CSS/JavaScript
- ❌ No Python execution
- ❌ No server-side processing
- ❌ No Streamlit apps

Your app needs:
- ✅ Python runtime
- ✅ Streamlit server
- ✅ GEE API calls
- ✅ Data processing

### What CAN GitHub Pages Host?

- Documentation websites
- HTML demos
- Static visualizations
- Project landing pages

---

## 🚀 Recommended Deployment Options

### Option 1: Streamlit Community Cloud (FREE & EASIEST)

**Best for**: Sharing with researchers, public demos

**Features**:
- ✅ Free hosting
- ✅ Automatic deployments from GitHub
- ✅ HTTPS by default
- ✅ Community support

**Steps**:
1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect your GitHub repo
4. Deploy with one click

**Secrets Management**:
- Use Streamlit Secrets for GEE credentials
- Each user authenticates with their own GEE account

**Limitations**:
- Public apps only (or private with paid plan)
- Resource limits (1 GB RAM per app)

---

### Option 2: Google Cloud Run (RECOMMENDED FOR RESEARCH)

**Best for**: Production research, institutional use

**Features**:
- ✅ Runs on Google Cloud (same as GEE)
- ✅ Automatic scaling
- ✅ Pay only for usage
- ✅ Private or public
- ✅ Custom authentication

**Steps**:
1. Create `Dockerfile`:
   ```dockerfile
   FROM python:3.11
   WORKDIR /app
   COPY . .
   RUN pip install -e .
   EXPOSE 8501
   CMD ["streamlit", "run", "app/climate_health_app.py"]
   ```

2. Deploy:
   ```bash
   gcloud run deploy climate-health-app \
     --source . \
     --region us-central1 \
     --allow-unauthenticated
   ```

**Cost**: ~$0-5/month for light use

---

### Option 3: Institutional Server

**Best for**: University/hospital deployment

**Features**:
- ✅ Full control
- ✅ Institutional authentication
- ✅ HIPAA compliance possible
- ✅ No external dependencies

**Requirements**:
- Linux server with Python 3.9+
- Nginx reverse proxy
- SSL certificate

**Setup**:
```bash
# On server
git clone your-repo
cd Climate_API
pip install -e .
streamlit run app/climate_health_app.py --server.port 8501
```

---

### Option 4: Share as Desktop App (EASIEST FOR COLLABORATORS)

**Best for**: Researchers without coding experience

**Distribute as**:
1. **Zip file with instructions**:
   ```
   Climate_API.zip
   └── README.txt: "Run RUN_APP.sh"
   ```

2. **Docker container**:
   ```bash
   docker build -t climate-health-app .
   docker run -p 8501:8501 climate-health-app
   ```

3. **PyInstaller executable** (advanced):
   - Package as standalone .exe/.app
   - No Python installation needed

---

## 🔒 Security Best Practices

### For GitHub Repository

1. **Create .gitignore**:
   ```bash
   echo ".config/" >> .gitignore
   echo "*.csv" >> .gitignore
   echo "__pycache__/" >> .gitignore
   echo ".env" >> .gitignore
   ```

2. **Check for secrets before committing**:
   ```bash
   git secrets --scan
   ```

3. **Use environment variables**:
   ```python
   # Instead of hardcoding
   gee_project = os.environ.get("GEE_PROJECT_ID", "joburg-hvi")
   ```

### For Production Deployment

1. **User authentication**:
   - Each user authenticates with their own GEE account
   - No shared credentials

2. **Rate limiting**:
   - Prevent API quota exhaustion
   - Cache results aggressively

3. **Data privacy**:
   - Don't store uploaded health data permanently
   - Use session-based temporary storage

4. **HTTPS only**:
   - Never deploy over HTTP
   - Use SSL certificates

---

## 📝 Preparing for GitHub

### Step 1: Create .gitignore

```bash
cd ~/Documents/Climate_API

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
*.egg-info/
dist/
build/

# Credentials & Secrets
.env
.env.local
credentials.json
*.pem
.config/
earthengine-credentials

# Data files (user data)
*.csv
*.nc
*.tif
*.geojson
app/test_outputs/
app/test_health_data.csv

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Streamlit
.streamlit/secrets.toml
EOF
```

### Step 2: Create README for GitHub

```markdown
# Climate-Health Analysis Platform

Research tool for analyzing climate-health relationships using Google Earth Engine.

## Features
- Upload health data (CSV)
- Extract climate data from GEE
- Statistical analysis with temporal lags
- Publication-ready outputs

## Installation

1. Clone repository
2. Install: `pip install -e .`
3. Authenticate GEE: `earthengine authenticate`
4. Run: `cd app && streamlit run climate_health_app.py`

## Requirements
- Python 3.9+
- Google Earth Engine account
- GEE project ID

## Documentation
See `docs/` folder for guides.
```

### Step 3: Initialize Git (if not already)

```bash
cd ~/Documents/Climate_API
git init
git add .
git commit -m "Initial commit: Climate-Health Analysis Platform"
```

### Step 4: Push to GitHub

```bash
# Create repo on GitHub first, then:
git remote add origin https://github.com/your-username/climate-health-platform.git
git branch -M main
git push -u origin main
```

---

## ✅ Security Checklist

Before pushing to GitHub:

- [ ] `.gitignore` created and committed
- [ ] No credentials in code
- [ ] No real health data in repo
- [ ] No API keys hardcoded
- [ ] Test data is synthetic only
- [ ] Environment variables used for secrets
- [ ] README explains authentication
- [ ] License file added (if needed)

---

## 🎯 Recommended Path for You

**For Sharing Your Research Tool**:

1. **GitHub** (code repository):
   - Push code (safe - no secrets)
   - Add documentation
   - Share with collaborators

2. **Streamlit Cloud** (live demo):
   - Free public deployment
   - Let others try it
   - No installation needed

3. **Docker** (for institutions):
   - Package for hospital deployment
   - Works offline after setup
   - Full control

**Your code is already safe to share!** The GEE authentication happens locally on each user's machine.

---

## 🆘 If You Accidentally Committed Secrets

If you ever commit credentials by mistake:

```bash
# Remove from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/secret" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all

# Rotate credentials immediately
# (Get new GEE tokens, API keys, etc.)
```

---

## Summary

✅ **Your GEE credentials are safe** - they're stored locally, not in code
✅ **Project ID is safe to share** - it's not a secret
❌ **GitHub Pages won't work** - need Python runtime
✅ **Use Streamlit Cloud instead** - free and easy
✅ **Code is ready for GitHub** - just add .gitignore

**You can safely share this project on GitHub right now!**
