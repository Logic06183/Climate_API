# 🚀 Streamlit Community Cloud Deployment Guide

## Complete FREE Deployment in 10 Minutes

This guide will walk you through deploying your Climate-Health Analysis Platform to Streamlit Community Cloud for **FREE**!

---

## 📋 Prerequisites

- [x] GitHub account
- [x] Google account (for GEE)
- [ ] Google Earth Engine project
- [ ] GEE Service Account credentials

---

## Step 1: Get Google Earth Engine Credentials (5 minutes)

### 1.1 Sign Up for Google Earth Engine

1. Go to https://earthengine.google.com
2. Click "Sign Up"
3. Fill out the form (select "Research" or "Education")
4. Wait for approval (usually instant for `.edu` emails, or within 24 hours)

### 1.2 Create a GEE Project

1. Go to https://console.cloud.google.com
2. Click "Select a project" → "New Project"
3. Give it a name: `climate-health-research`
4. Click "Create"
5. **Note your Project ID** (e.g., `climate-health-research-12345`)

### 1.3 Enable Earth Engine API

1. In Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Earth Engine API"
3. Click "Enable"

### 1.4 Create Service Account

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **"+ Create Service Account"**
3. Fill in:
   - **Name**: `climate-health-app`
   - **Description**: `Service account for Climate Health Analysis app`
4. Click "Create and Continue"
5. Grant role: **"Earth Engine Resource Admin"**
6. Click "Continue" → "Done"

### 1.5 Create Service Account Key

1. Find your new service account in the list
2. Click on it
3. Go to **"Keys"** tab
4. Click **"Add Key"** → **"Create new key"**
5. Select **JSON**
6. Click **"Create"**
7. **SAVE THE DOWNLOADED JSON FILE** - you'll need it!

The JSON file looks like:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "climate-health-app@your-project.iam.gserviceaccount.com",
  ...
}
```

---

## Step 2: Deploy to Streamlit Cloud (3 minutes)

### 2.1 Push to GitHub (Already Done! ✅)

Your code is already on GitHub at:
```
https://github.com/Logic06183/Climate_API
```

### 2.2 Sign Up for Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "Sign in"
3. Choose "Sign in with GitHub"
4. Authorize Streamlit Cloud

### 2.3 Deploy Your App

1. Click **"New app"**
2. Fill in the deployment settings:
   ```
   Repository: Logic06183/Climate_API
   Branch: refactor/modernize-architecture
   Main file path: app/climate_health_app.py
   ```
3. Click **"Advanced settings"**
4. Set Python version: `3.11`
5. **Don't click Deploy yet!** - We need to add secrets first

### 2.4 Add Secrets

1. In the "Secrets" section, paste your service account JSON:
   ```toml
   [gee_service_account]
   type = "service_account"
   project_id = "your-gee-project-id"
   private_key_id = "abc123def456..."
   private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n"
   client_email = "climate-health-app@your-project.iam.gserviceaccount.com"
   client_id = "123456789"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/climate-health-app%40your-project.iam.gserviceaccount.com"
   ```

   **IMPORTANT**:
   - Copy from your downloaded JSON file
   - Keep the TOML format (with quotes and proper escaping)
   - The `private_key` must include `\n` for newlines

2. Click **"Save"**

### 2.5 Deploy!

1. Click **"Deploy"**
2. Wait 2-3 minutes for deployment
3. Your app will be live at: `https://your-app-name.streamlit.app`

---

## Step 3: Test Your Deployed App (2 minutes)

1. Open your app URL
2. In the sidebar, select **"Streamlit Secrets"** as authentication method
3. Enter your GEE Project ID
4. Click **"Test GEE Authentication"**
   - Should show: ✅ Authenticated with Streamlit secrets
5. Upload test health data
6. Click **"Extract Climate Data"**
7. Should work! 🎉

---

## 🔐 Security Best Practices

### ✅ What's Safe

- Your code is public on GitHub ✓
- Service account JSON is in Streamlit Secrets (encrypted) ✓
- Each user can bring their own credentials ✓

### ❌ Never Do This

- **NEVER** commit service account JSON to Git
- **NEVER** hardcode credentials in code
- **NEVER** share your private key publicly

### 🛡️ How Secrets Are Protected

- Secrets are encrypted at rest
- Only accessible to your app at runtime
- Not visible in logs or to users
- Can be updated anytime

---

## 🎛️ Alternative: Let Users Bring Their Own Credentials

Your app supports **three authentication methods**:

### Option 1: Streamlit Secrets (You as App Owner)
- Best for: Single-user or small team
- You provide credentials in Streamlit Cloud
- Users just use the app

### Option 2: Service Account Upload (Users Bring Own)
- Best for: Public apps, multiple organizations
- Each user uploads their own JSON file
- More secure (users control their own credentials)
- To use:
  1. Users create their own GEE service account
  2. Download JSON key
  3. Upload in the app's sidebar

### Option 3: Local Authentication (Development Only)
- Only works when running locally
- Not available in cloud deployment
- For development/testing

**For public deployment, recommend Option 2!**

---

## 📊 Usage & Costs

### Streamlit Community Cloud (FREE)

**Included:**
- Unlimited public apps
- 1 GB RAM per app
- Automatic SSL (HTTPS)
- Auto-deploy from GitHub
- Community support

**Limitations:**
- Apps sleep after 7 days of inactivity (wake in 30 seconds)
- Public apps only (anyone can access)
- Resource limits (1 GB RAM, shared CPU)

### Google Earth Engine (FREE for Research)

**Included:**
- All Earth Engine datasets
- Unlimited API calls
- Global coverage
- Free for research/education

**Quotas:**
- Concurrent requests: Generous
- Storage: Check your project quota
- Commercial use: Requires paid tier

---

## 🔧 Troubleshooting

### "Authentication failed"

**Check:**
1. Is service account JSON valid?
2. Did you enable Earth Engine API?
3. Is the service account granted "Earth Engine Resource Admin"?
4. Are newlines properly escaped in private_key? (`\n`)

**Fix:**
```toml
# Make sure private_key has \n for newlines:
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQ...\n-----END PRIVATE KEY-----\n"
```

### "Module not found" Error

**Fix:** Update `requirements.txt`:
```txt
streamlit>=1.30.0
earthengine-api>=0.1.350
pandas>=2.0.0
...
```

### App is Slow

**Causes:**
- Cold start (app was sleeping)
- Large data extraction
- Many concurrent users

**Solutions:**
- Use caching (`@st.cache_data`)
- Extract smaller date ranges
- Consider upgrading to Streamlit Pro

### Climate Extraction Times Out

**Solutions:**
1. Reduce date range (try 3 months instead of 1 year)
2. Use caching for repeated extractions
3. Extract data offline and upload instead

---

## 🎨 Customization

### Change App Title/Icon

Edit `app/climate_health_app.py`:
```python
st.set_page_config(
    page_title="Your Custom Title",
    page_icon="🌡️",  # or "🏥", "🌍", etc.
    layout="wide"
)
```

### Custom URL

1. Go to Streamlit Cloud dashboard
2. Click your app → Settings
3. Click "Edit" next to the URL
4. Choose custom subdomain: `your-name.streamlit.app`

### Custom Domain

Requires Streamlit Pro ($20/month):
- Use your own domain (e.g., `app.yourlab.edu`)
- Private apps
- Better performance
- Priority support

---

## 📈 Monitoring

### View App Logs

1. Go to https://share.streamlit.io
2. Click on your app
3. Click "Manage app" → "Logs"
4. See real-time logs

### Analytics

Streamlit Cloud provides:
- Viewer count
- Session duration
- Error rates
- Resource usage

---

## 🔄 Updating Your App

### Automatic Deployment

Every time you push to GitHub:
```bash
git add .
git commit -m "Update analysis features"
git push origin refactor/modernize-architecture
```

Streamlit Cloud automatically:
1. Detects the push
2. Rebuilds the app
3. Deploys the new version
4. Usually takes 2-3 minutes

### Manual Reboot

If needed:
1. Go to Streamlit Cloud dashboard
2. Click your app
3. Click "Reboot app"

---

## 🎉 Success Checklist

- [ ] GEE account approved
- [ ] GEE project created
- [ ] Service account created
- [ ] Service account JSON downloaded
- [ ] App deployed to Streamlit Cloud
- [ ] Secrets configured
- [ ] Authentication tested
- [ ] Climate extraction works
- [ ] Analysis produces results
- [ ] Shared URL with colleagues

---

## 🤝 Share Your App

Your app is now live! Share it:

```
🏥 Climate-Health Analysis Platform
https://your-app.streamlit.app

Analyze climate-health relationships with:
✅ Real GEE climate data
✅ Statistical analysis
✅ Publication outputs
✅ No coding required
```

**For users:**
1. Go to the URL
2. Upload their health data CSV
3. Upload their GEE service account JSON (or use yours if configured)
4. Click "Extract Climate"
5. Click "Run Analysis"
6. Download results!

---

## 📞 Support

**Streamlit:**
- Docs: https://docs.streamlit.io
- Forum: https://discuss.streamlit.io
- GitHub: https://github.com/streamlit/streamlit

**Google Earth Engine:**
- Docs: https://developers.google.com/earth-engine
- Forum: https://groups.google.com/g/google-earth-engine-developers
- Code Editor: https://code.earthengine.google.com

**This App:**
- GitHub Issues: https://github.com/Logic06183/Climate_API/issues

---

## 🎯 Next Steps

### For Research Use
1. Test with your real health data
2. Extract climate for your study location
3. Run analyses
4. Download publication tables
5. Write papers! 📝

### For Collaboration
1. Share app URL with co-authors
2. Each uses their own GEE credentials
3. Compare results across cities
4. Standardized methodology

### For Publication
Your deployed app can be cited:
```
[Your Name]. (2026). Climate-Health Analysis Platform.
Streamlit Community Cloud. https://your-app.streamlit.app
```

---

**🎊 Congratulations! Your app is live and FREE forever!**

**App URL**: `https://your-app-name.streamlit.app`

Users worldwide can now analyze climate-health relationships with professional research tools - no coding required!
