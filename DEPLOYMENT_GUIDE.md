# Deployment Guide: Taking Your PPT Generator Online

This guide will walk you through deploying your Streamlit app to Streamlit Cloud (free hosting).

## Prerequisites

- A GitHub account (free - sign up at [github.com](https://github.com))
- Your code ready in the PPT Maker folder
- Your Anthropic API key

---

## Step 1: Create a GitHub Account (if you don't have one)

1. Go to [github.com](https://github.com)
2. Click "Sign up" in the top right
3. Follow the registration process
4. Verify your email address

---

## Step 2: Install Git (if not already installed)

### Check if Git is installed:
Open PowerShell or Command Prompt and type:
```bash
git --version
```

### If Git is NOT installed:
1. Download Git from: [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Run the installer (use default settings)
3. Restart your terminal after installation

---

## Step 3: Prepare Your Code for GitHub

### 3.1. Initialize Git Repository

1. Open PowerShell or Command Prompt
2. Navigate to your PPT Maker folder:
   ```bash
   cd "E:\Cursor Files\PPT Maker"
   ```

3. Initialize Git:
   ```bash
   git init
   ```

### 3.2. Create .gitignore (if not already exists)

Make sure `.gitignore` includes these important files:
- `config.yaml` (contains your API key - should NOT be uploaded)
- `.streamlit/secrets.toml` (contains API key - should NOT be uploaded)
- `output/` folder (temporary files)
- `PPTs/` folder (generated files)
- `__pycache__/` (Python cache)

The `.gitignore` file should already exist and be configured correctly.

### 3.3. Add All Files to Git

```bash
git add .
```

### 3.4. Create Your First Commit

```bash
git commit -m "Initial commit: PPT Generator with Streamlit webapp"
```

---

## Step 4: Create GitHub Repository

### 4.1. Create New Repository on GitHub

1. Go to [github.com](https://github.com) and sign in
2. Click the **"+"** icon in the top right corner
3. Select **"New repository"**

### 4.2. Repository Settings

Fill in the form:
- **Repository name:** `ppt-generator` (or any name you like)
- **Description:** "Automated PowerPoint generator from PDF files"
- **Visibility:** Choose **Public** (required for free Streamlit Cloud) or **Private** (if you have GitHub Pro)
- **DO NOT** check "Initialize with README" (we already have files)
- Click **"Create repository"**

### 4.3. Copy Repository URL

After creating, GitHub will show you a page with commands. **Copy the repository URL** - it will look like:
```
https://github.com/yourusername/ppt-generator.git
```

---

## Step 5: Push Code to GitHub

### 5.1. Connect Local Repository to GitHub

In your terminal (still in the PPT Maker folder), run:

```bash
git remote add origin https://github.com/yourusername/ppt-generator.git
```

**Replace `yourusername/ppt-generator` with your actual repository URL!**

### 5.2. Push Your Code

```bash
git branch -M main
git push -u origin main
```

**Note:** If this is your first time using Git, you may be asked to:
- Enter your GitHub username
- Enter your password (or use a Personal Access Token)

### 5.3. If Authentication Fails

If you get authentication errors, you may need to use a Personal Access Token:

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name like "Streamlit Deployment"
4. Check the `repo` scope
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)
7. Use this token as your password when pushing

---

## Step 6: Deploy to Streamlit Cloud

### 6.1. Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign up"** or **"Get started"**
3. Click **"Continue with GitHub"**
4. Authorize Streamlit Cloud to access your GitHub account

### 6.2. Create New App

1. Once logged in, click **"New app"** button
2. You'll see a form to configure your app

### 6.3. Configure Your App

Fill in the form:
- **Repository:** Select your `ppt-generator` repository from the dropdown
- **Branch:** Select `main` (or `master` if that's your branch)
- **Main file path:** Enter `streamlit_app.py`
- **App URL:** This will be auto-generated (you can customize it)
- Click **"Deploy"**

### 6.4. Wait for Initial Deployment

Streamlit will:
- Install dependencies from `requirements.txt`
- Start your app
- This takes 1-2 minutes

---

## Step 7: Add Your API Key (IMPORTANT!)

### 7.1. Access App Settings

1. In Streamlit Cloud, go to your app dashboard
2. Click on your app name
3. Click the **"⋮"** (three dots) menu in the top right
4. Select **"Settings"**

### 7.2. Add Secrets

1. In Settings, find the **"Secrets"** section
2. Click to expand it
3. You'll see a text box

### 7.3. Enter Your API Key

Paste this into the secrets box:

```toml
[anthropic]
api_key = "your-actual-api-key-here"
```

**Replace `your-actual-api-key-here` with your actual Anthropic API key from `config.yaml`**

### 7.4. Save Secrets

1. Click **"Save"**
2. Your app will automatically restart with the new secrets

---

## Step 8: Test Your Deployed App

1. Go back to your app (click the app name or URL)
2. Your app should now be live!
3. Test by uploading a PDF file
4. If it works, you're done! 🎉

---

## Step 9: Share Your App

### Get Your App URL

1. In Streamlit Cloud dashboard, click on your app
2. Copy the URL from the address bar
3. It will look like: `https://your-app-name.streamlit.app`

### Share with Friends

Simply send them the URL! They can:
- Open it in any web browser
- Upload PDFs
- Download generated PowerPoints
- No installation or setup required!

---

## Troubleshooting

### App Won't Start

**Check:**
- Did you add the API key in Secrets?
- Are all dependencies in `requirements.txt`?
- Check the logs in Streamlit Cloud (click "Manage app" → "Logs")

### "Module not found" Error

**Solution:**
- Make sure all packages are in `requirements.txt`
- The app will reinstall dependencies automatically

### API Key Not Working

**Check:**
- Is the API key correct in Secrets?
- Format should be exactly:
  ```toml
  [anthropic]
  api_key = "sk-ant-..."
  ```
- Make sure there are no extra spaces or quotes

### App is Slow

**Normal:** Processing takes 30-60 seconds per step. This is expected!

---

## Updating Your App

If you make changes to your code:

1. Make your changes locally
2. Commit changes:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push
   ```
3. Streamlit Cloud will automatically detect changes and redeploy (takes 1-2 minutes)

---

## Security Notes

- ✅ Your API key is stored securely in Streamlit Cloud secrets
- ✅ `config.yaml` is NOT uploaded to GitHub (in `.gitignore`)
- ✅ Secrets file is NOT uploaded to GitHub (in `.gitignore`)
- ✅ Only your code is public (if repository is public)

---

## Next Steps

- Customize your app URL in Streamlit Cloud settings
- Add a custom domain (if you have one)
- Monitor usage in Streamlit Cloud dashboard
- Share the link with your friends!

---

## Quick Reference Commands

```bash
# Navigate to project
cd "E:\Cursor Files\PPT Maker"

# Check Git status
git status

# Add all changes
git add .

# Commit changes
git commit -m "Your message here"

# Push to GitHub
git push

# View app logs (in Streamlit Cloud dashboard)
# Go to: Manage app → Logs
```

---

**Congratulations!** Your app is now live on the internet! 🚀

