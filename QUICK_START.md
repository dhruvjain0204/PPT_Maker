# Quick Start Guide

## Transferring to Another Laptop

### Option 1: USB Drive / External Storage

1. Copy the entire `PPT Maker` folder to your USB drive
2. Transfer to the new laptop
3. Follow the setup steps below

### Option 2: Cloud Storage (Google Drive, Dropbox, OneDrive)

1. Upload the `PPT Maker` folder to your cloud storage
2. Download on the new laptop
3. Follow the setup steps below

### Option 3: Network Share

1. Share the folder over your local network
2. Copy to the new laptop
3. Follow the setup steps below

## Setup on New Laptop (5 Minutes)

### Windows:

1. **Double-click `setup.bat`**
   - This will install dependencies and create config.yaml

2. **Edit `config.yaml`** (opens automatically)
   - Replace `YOUR_ANTHROPIC_API_KEY_HERE` with your actual API key
   - Replace `YOUR_PRESENTON_API_KEY_HERE` with your actual API key

3. **Run the script:**
   ```bash
   python generate_ppt_from_pdf.py "path\to\your\file.pdf"
   ```

### Mac/Linux:

1. **Open Terminal in the project folder**

2. **Make setup script executable and run:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Edit `config.yaml`** (opens automatically)
   - Replace `YOUR_ANTHROPIC_API_KEY_HERE` with your actual API key
   - Replace `YOUR_PRESENTON_API_KEY_HERE` with your actual API key

4. **Run the script:**
   ```bash
   python3 generate_ppt_from_pdf.py "path/to/your/file.pdf"
   ```

## Manual Setup (If Scripts Don't Work)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create config.yaml:**
   ```bash
   copy config.yaml.example config.yaml    # Windows
   cp config.yaml.example config.yaml      # Mac/Linux
   ```

3. **Edit config.yaml** and add your API keys

4. **Run:**
   ```bash
   python generate_ppt_from_pdf.py "your_file.pdf"
   ```

## What Files to Transfer

**Required Files:**
- `generate_ppt_from_pdf.py`
- `step1_pdf_extraction.py`
- `step2_question_parsing.py`
- `step3_pptx_new.py`
- `config.yaml.example`
- `requirements.txt`
- `README.md`
- `setup.bat` (Windows) or `setup.sh` (Mac/Linux)

**Optional Files:**
- `PLAN.md` (project documentation)
- `.gitignore` (if using version control)

**Don't Transfer:**
- `config.yaml` (contains your API keys - create fresh on new laptop)
- `output/` folder (intermediate files)
- `PPTs/` folder (generated presentations)
- `__pycache__/` folder (Python cache)

## Getting API Keys

### Anthropic API Key:
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste into `config.yaml`

### Presenton API Key:
- Contact your Presenton service provider or check your account dashboard

## Testing

After setup, test with a sample PDF:

```bash
python generate_ppt_from_pdf.py "test.pdf"
```

If successful, you should see:
- `[OK] Step 1 complete`
- `[OK] Step 2 complete`
- `[OK] Step 3 complete`
- `[SUCCESS] Presentation generated successfully!`

## Troubleshooting

**"python is not recognized"**
- Install Python from https://www.python.org/
- Make sure "Add Python to PATH" is checked during installation

**"pip is not recognized"**
- Python might not be installed correctly
- Try `python -m pip install -r requirements.txt`

**"ModuleNotFoundError"**
- Run `pip install -r requirements.txt` again
- Make sure you're in the correct directory

**"API key not found"**
- Make sure `config.yaml` exists (not just `config.yaml.example`)
- Check that API keys are correctly formatted (no extra spaces)

