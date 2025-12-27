# PPT Generator from PDF

Automated PowerPoint presentation generator that extracts questions from PDF files and creates structured slide presentations.

## Features

- **PDF Content Extraction**: Uses Claude API to extract text content from PDF files
- **Question Parsing**: Intelligently identifies and structures questions from extracted content
- **PPTX Generation**: Automatically creates PowerPoint presentations with formatted slides

## Prerequisites

- Python 3.8 or higher
- Anthropic API key (for Claude API)
- Presenton API key (optional, for enhanced features)

## Installation

### Step 1: Clone or Copy the Project

Copy the entire `PPT Maker` folder to your new laptop.

### Step 2: Install Python Dependencies

Open a terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

Or on Windows, you can double-click `setup.bat` (see below).

### Step 3: Configure API Keys

1. Copy `config.yaml.example` to `config.yaml`:
   ```bash
   copy config.yaml.example config.yaml
   ```
   (On Linux/Mac: `cp config.yaml.example config.yaml`)

2. Open `config.yaml` in a text editor and replace the placeholder API keys:
   - `YOUR_ANTHROPIC_API_KEY_HERE` - Get your API key from [Anthropic Console](https://console.anthropic.com/)
   - `YOUR_PRESENTON_API_KEY_HERE` - Your Presenton API key (if applicable)

### Step 4: Verify Installation

Run a test command to ensure everything is set up correctly:

```bash
python generate_ppt_from_pdf.py --help
```

## Usage

### Basic Usage

```bash
python generate_ppt_from_pdf.py "path/to/your/file.pdf"
```

### Examples

**Windows:**
```bash
python generate_ppt_from_pdf.py "C:\Users\YourName\Downloads\document.pdf"
```

**Linux/Mac:**
```bash
python generate_ppt_from_pdf.py "/home/username/Downloads/document.pdf"
```

**Relative path:**
```bash
python generate_ppt_from_pdf.py "document.pdf"
```

## Web Application (Streamlit)

A user-friendly web interface is available for non-technical users!

### Local Development

1. **Install dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API key** (choose one method):
   - **Option A:** Create `.streamlit/secrets.toml`:
     ```toml
     [anthropic]
     api_key = "your-api-key-here"
     ```
   - **Option B:** Use existing `config.yaml` (will work as fallback)

3. **Run the webapp**:
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Access the app**: Open your browser to `http://localhost:8501`

### Streamlit Cloud Deployment

1. **Push code to GitHub** (make sure `.streamlit/secrets.toml` is in `.gitignore`)

2. **Connect to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository and set main file to `streamlit_app.py`

3. **Add secrets**:
   - In Streamlit Cloud dashboard, go to Settings → Secrets
   - Add your API key:
     ```toml
     [anthropic]
     api_key = "your-api-key-here"
     ```

4. **Deploy**: Click "Deploy" and share the URL with your friends!

### Webapp Features

- Simple file upload interface
- Option to include/exclude answer slides
- Real-time progress indicators
- One-click download of generated PPT
- No technical knowledge required!

## Output

The script generates:

1. **Extracted Text**: `output/extracted_pdf_content_[filename].txt`
2. **Parsed Questions**: `output/parsed_questions_[filename].json`
3. **Preview**: `output/parsed_questions_[filename]_preview.txt`
4. **PowerPoint**: `PPTs/[filename].pptx`

## Project Structure

```
PPT Maker/
├── streamlit_app.py             # Web application (NEW)
├── generate_ppt_from_pdf.py    # Main script (command-line)
├── step1_pdf_extraction.py     # PDF extraction module
├── step2_question_parsing.py    # Question parsing module
├── step3_pptx_new.py           # PPTX generation module
├── config.yaml                 # Configuration (create from example)
├── config.yaml.example         # Configuration template
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── setup.bat                   # Windows setup script
├── .streamlit/                 # Streamlit configuration
│   ├── config.toml              # Streamlit settings
│   └── secrets.toml.example    # Secrets template
├── output/                     # Generated intermediate files
└── PPTs/                       # Generated PowerPoint files
```

## Troubleshooting

### API Key Issues

If you see `[ERROR] API key not found!`:
- Make sure `config.yaml` exists (copy from `config.yaml.example`)
- Verify your API keys are correctly set in `config.yaml`
- Check that there are no extra spaces or quotes around the API keys

### PDF Not Found

If you see `[ERROR] PDF file not found`:
- Use the full path to the PDF file
- Or copy the PDF to the project directory and use just the filename
- Make sure the path is in quotes if it contains spaces

### Python Not Found

If you see `'python' is not recognized`:
- Make sure Python is installed and added to PATH
- Try using `python3` instead of `python`
- On Windows, you may need to install Python from [python.org](https://www.python.org/)

### Module Not Found

If you see `ModuleNotFoundError`:
- Run `pip install -r requirements.txt` to install dependencies
- Make sure you're using the correct Python environment

## Quick Setup Script (Windows)

Double-click `setup.bat` to automatically:
1. Install Python dependencies
2. Create `config.yaml` from template
3. Open `config.yaml` for editing

## Notes

- The script processes PDFs in three steps (extraction, parsing, generation)
- Each step may take 30-60 seconds depending on PDF size
- Generated PPTX files are saved in the `PPTs` folder
- If a file with the same name exists, a number suffix will be added automatically

## Support

For issues or questions, check:
1. All dependencies are installed (`pip list`)
2. `config.yaml` is properly configured
3. PDF file path is correct and accessible

