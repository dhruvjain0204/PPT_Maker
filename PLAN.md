# PPT Question Automation - Master Plan

This document contains the overall plan and status of the PPT Question Automation project. It's updated whenever code or plans change.

## Project Overview

Automate the creation of practice question PowerPoint presentations from PDF sources. The system extracts questions from PDFs using LLM, applies template styling, and generates formatted PPTX files.

**Quick Start:**
```bash
python generate_ppt_from_pdf.py "Your-PDF-File.pdf"
```

This single command runs all three steps automatically and outputs to `PPTs/{PDF-name}.pptx`

## Development Approach

We're building this **step-by-step**, testing each part before moving to the next:
1. Each step runs independently
2. Saves output for review
3. Shows what was extracted/processed
4. Waits for verification before next step

This ensures we catch issues early and fix them before moving forward.

---

## Step 1: PDF Content Extraction ✅ COMPLETE

**File:** `step1_pdf_extraction.py`

**Status:** ✅ Working - Uses Claude API to extract text from PDF

**What it does:**
- Extracts text content from PDF using Claude API (similar to Perplexity workflow)
- Supports both text-based and image-based PDFs (no OCR setup needed)
- Saves extracted text for manual review
- Analyzes content quality (questions, answers, options)
- Verifies extraction completeness

**How it works:**
1. Accepts PDF filename as command line argument (or uses default)
2. Extracts PDF name (without extension) for naming outputs
3. Loads PDF file and converts to base64
4. Sends PDF to Claude API with extraction prompt
5. Receives extracted text content
6. Analyzes content for quality indicators
7. Saves to `output/extracted_pdf_content_{pdf_name}.txt`
8. Saves PDF name to `output/current_pdf_name.txt` for next steps

**Dependencies:**
- `anthropic` - Claude API client
- `pyyaml` - Config file parsing
- `base64` - PDF encoding (built-in)

**To run:**
```bash
python step1_pdf_extraction.py "Adobe-Scan-03-Nov-2025.pdf"
# Or without argument (uses default PDF)
python step1_pdf_extraction.py
```

**Output:**
- `output/extracted_pdf_content_{pdf_name}.txt` - Full extracted text for review
- `output/current_pdf_name.txt` - PDF name for next steps

**Verification checklist:**
- [ ] Is the text readable and complete?
- [ ] Are questions properly extracted?
- [ ] Are options/answers included (if applicable)?
- [ ] Are tables/diagrams mentioned or described?
- [ ] Is the content in the correct order?
- [ ] Is the extraction accurate (no missing or incorrect content)?

**Next:** Once verified, proceed to Step 2: Question Parsing

---

## Step 2: Question Parsing & Slide Structuring ✅ COMPLETE

**File:** `step2_question_parsing.py`

**Status:** ✅ Working - Parses extracted content into structured slide-ready objects

**What it does:**
- Parses extracted PDF content into structured question objects
- Extracts individual questions, options, answers, tables, diagrams
- Numbers questions sequentially (Q1, Q2, Q3...) ignoring PDF numbers
- Handles multi-part questions (keeps all parts together)
- Detects passage-based questions (passage on separate slide)
- Structures tables with headers and rows
- Flags diagrams with [description] for manual addition later
- Organizes content into slide-ready format

**How it works:**
1. Reads PDF name from Step 1 (`output/current_pdf_name.txt`)
2. Loads extracted content from Step 1 (`output/extracted_pdf_content_{pdf_name}.txt`)
3. Sends to Claude API with structured parsing instructions
4. Receives JSON with question objects
5. Validates structure and counts statistics
6. Saves to `output/parsed_questions_{pdf_name}.json`
7. Creates human-readable preview

**Dependencies:**
- `anthropic` - Claude API client
- `pyyaml` - Config file parsing
- `json` - JSON parsing (built-in)

**To run:**
```bash
python step2_question_parsing.py
```

**Output:**
- `output/parsed_questions_{pdf_name}.json` - Structured JSON with all questions
- `output/parsed_questions_{pdf_name}_preview.txt` - Human-readable preview

**Slide Organization Rules:**
- Regular question: Question slide → Answer slide (if answer exists)
- Multi-part question: All parts on one question slide → Answer slide
- Multiple choice: Question + options → Answer slide
- Passage-based: Passage slide → Question slide(s) → Answer slide(s)
- Tables: Structured data with headers and rows
- Diagrams: Flagged as [description] for manual addition

**Verification checklist:**
- [ ] Are all questions properly parsed?
- [ ] Are multi-part questions kept together?
- [ ] Are passage-based questions detected correctly?
- [ ] Are tables structured correctly?
- [ ] Are diagram descriptions in brackets [description]?
- [ ] Are answers on separate slides after questions?

**Next:** Once verified, proceed to Step 3: Template Analysis

---

## Step 3: PPTX Generation (New Implementation) ✅ COMPLETE & REFINED

**File:** `step3_pptx_new.py`

**Status:** ✅ Complete - Generates PPTX optimized for Canva import with proper formatting

**What it does:**
- Reads parsed questions from Step 2
- Creates PowerPoint slides with professional formatting
- Uses Frankfurter Medium font (as per requirements)
- Positions text boxes to match Canva template dimensions exactly
- Renders tables intelligently (detects if table is just options, shows only options as text)
- Formats question/answer numbers with single dot (Q1., Ans1.)
- Shows simplified diagram notes as [Diagram]
- Handles multiple choice options without bullets

**How it works:**
1. Reads PDF name from Step 1 (`output/current_pdf_name.txt`)
2. Loads parsed questions JSON from Step 2 (`output/parsed_questions_{pdf_name}.json`)
3. Creates blank PowerPoint presentation with widescreen dimensions (13.333" × 7.5")
4. For each slide:
   - Question slides: Q1. [question] + options (no bullets) + table (if not options) + [Diagram]
   - Answer slides: Ans1. [answer]
   - Passage slides: [passage text]
5. Applies unified formatting (25pt font = 38pt in Canva, Frankfurter Medium, left-aligned)
6. Saves PPTX file to `PPTs/{pdf_name}.pptx` (with auto-numbering if file exists)

**Dependencies:**
- `python-pptx` - PowerPoint generation
- `json` - JSON parsing (built-in)

**To run:**
```bash
# With answer slides (default)
python step3_pptx_new.py

# Without answer slides
python step3_pptx_new.py --no-answers
```

**Output:**
- `PPTs/{pdf_name}.pptx` - PPTX file ready to import into Canva
- If file exists, automatically creates `PPTs/{pdf_name}_1.pptx`, `PPTs/{pdf_name}_2.pptx`, etc.

**Font & Formatting:**
- Font: **Frankfurter Medium** (as per requirements)
- Font size: **25pt** in PowerPoint (results in **38pt** in Canva for all slides)
- Font size: **18pt for tables** (increased for better readability)
- Alignment: Left-aligned
- Question/Answer numbers: Bold with single dot (Q1., Ans1., etc.)

**Text Box Positioning (Canva-Optimized):**
- Dimensions matched to Canva template exactly
- Position: X=73.6px, Y=162.3px (in Canva)
- Size: Width=1773.3px, Height=510.7px (in Canva)
- Uses correction factors to account for PowerPoint-to-Canva conversion differences

**Slide Dimensions:**
- Standard PowerPoint widescreen: 13.333" × 7.5" (16:9 aspect ratio)

**Smart Features:**
- **Options Table Detection**: If a table represents multiple choice options, shows only options as text (no duplicate table)
- **Diagram Simplification**: Shows only "[Diagram]" instead of full description to save space
- **No Bullets for Options**: Multiple choice options displayed without bullets
- **Single Dot Formatting**: Question/answer numbers have exactly one dot (Q1., not Q1..)
- **Optional Answer Slides**: Use `--no-answers` flag to exclude answer slides from the presentation

**Verification checklist:**
- [x] All questions present
- [x] Font is Frankfurter Medium
- [x] Font size is 38pt in Canva (25pt in PowerPoint)
- [x] Table font size is 18pt (increased for better readability)
- [x] Text box dimensions match Canva template
- [x] Tables render correctly (or skipped if they're options)
- [x] Answer slides numbered correctly (Ans1, Ans2...)
- [x] Options don't have bullets
- [x] Diagram shows as [Diagram] only
- [x] Single dot after Q/Ans numbers
- [x] Can import into Canva successfully
- [x] Optional answer slides feature works with --no-answers flag

**Next:** Import PPTX into Canva - dimensions and formatting are already optimized!

---

## Integrated Script: One-Command Generation 🚀 RECOMMENDED

**File:** `generate_ppt_from_pdf.py`

**Status:** ✅ Complete - Combines all three steps into a single command

**What it does:**
- Takes PDF file as input
- Automatically runs Step 1 (PDF extraction), Step 2 (Question parsing), and Step 3 (PPTX generation)
- Handles all intermediate file naming based on PDF name
- Saves final output to `PPTs/{pdf_name}.pptx`
- Automatically handles file conflicts (adds number suffix if file exists)

**How it works:**
1. Accepts PDF filename as command line argument
2. Runs Step 1: Extracts content from PDF
3. Runs Step 2: Parses questions into structured format
4. Runs Step 3: Generates PPTX file
5. Shows summary of results

**Dependencies:**
- All dependencies from Step 1, 2, and 3
- Imports functions from `step1_pdf_extraction.py`, `step2_question_parsing.py`, and `step3_pptx_new.py`

**To run:**
```bash
# PDF in current directory (with answers - default)
python generate_ppt_from_pdf.py "Adobe-Scan-03-Nov-2025.pdf"

# PDF without answer slides
python generate_ppt_from_pdf.py "Adobe-Scan-03-Nov-2025.pdf" --no-answers

# PDF in subfolder
python generate_ppt_from_pdf.py "PDFs/MyFile.pdf"

# PDF with full path
python generate_ppt_from_pdf.py "E:\Documents\MyFile.pdf"
```

**Output:**
- Intermediate files: `output/extracted_pdf_content_{pdf_name}.txt`, `output/parsed_questions_{pdf_name}.json`
- Final PPTX: `PPTs/{pdf_name}.pptx` (or `PPTs/{pdf_name}_1.pptx` if exists, etc.)

**Features:**
- ✅ Single command for entire workflow
- ✅ Automatic PDF name detection and file naming
- ✅ Handles existing files (auto-numbering)
- ✅ Progress updates for each step
- ✅ Error handling at each step
- ✅ Final summary with statistics
- ✅ Optional answer slides: Use `--no-answers` flag to exclude answer slides

**Example Output:**
```
============================================================
INTEGRATED PPT GENERATION FROM PDF
============================================================
Input PDF: Adobe-Scan-03-Nov-2025.pdf

[Step 1: PDF Content Extraction...]
[Step 2: Question Parsing...]
[Step 3: PPTX Generation...]

============================================================
GENERATION COMPLETE!
============================================================
Input PDF: Adobe-Scan-03-Nov-2025.pdf
Output PPTX: PPTs/Adobe-Scan-03-Nov-2025.pptx
Total questions: 29
Total slides: 52
```

**This is the recommended way to use the system!**

---

## Multi-PDF Processing Script 🆕 NEW

**File:** `generate_ppt_from_multiple_pdfs.py`

**Status:** ✅ Complete - Process multiple PDFs sequentially with continuous question numbering

**What it does:**
- Processes multiple PDF files sequentially to avoid overwhelming the LLM
- Maintains continuous question numbering across all PDFs (Q1, Q2... Q20 from PDF1, then Q21, Q22... from PDF2)
- Supports custom starting question numbers (e.g., start from Q50)
- Processes each PDF separately in Step 1 and Step 2 for better quality
- Combines all questions into a single PowerPoint presentation

**Why use this:**
- Better quality for large PDFs (>100 pages) - splits into smaller chunks
- Avoids API page limits (Claude API has 100-page limit per request)
- Processes PDFs one by one to prevent overwhelming the LLM
- Maintains sequential numbering automatically

**How it works:**
1. Accepts multiple PDF filenames as command line arguments
2. Processes each PDF sequentially in Step 1 (extraction)
3. Processes each PDF's content sequentially in Step 2 (parsing) with offset numbering
4. Combines all questions with continuous numbering
5. Generates single PPTX file with all questions from all PDFs

**Dependencies:**
- All dependencies from Step 1, 2, and 3
- Uses new functions: `extract_multiple_pdfs()`, `parse_multiple_pdfs_content()`, etc.

**To run:**
```bash
# Multiple PDFs (separate arguments)
python generate_ppt_from_multiple_pdfs.py "pdf1.pdf" "pdf2.pdf" "pdf3.pdf"

# Multiple PDFs (comma-separated)
python generate_ppt_from_multiple_pdfs.py "pdf1.pdf,pdf2.pdf,pdf3.pdf"

# Starting from Q20
python generate_ppt_from_multiple_pdfs.py "pdf1.pdf" "pdf2.pdf" --start-from 20

# Without answer slides
python generate_ppt_from_multiple_pdfs.py "pdf1.pdf" "pdf2.pdf" --no-answers

# Starting from Q50 without answers
python generate_ppt_from_multiple_pdfs.py "pdf1.pdf" "pdf2.pdf" --no-answers --start-from 50

# Single PDF also works
python generate_ppt_from_multiple_pdfs.py "pdf1.pdf"
```

**Output:**
- Intermediate files: `output/extracted_pdf_content_{first_pdf_name}.txt`, `output/parsed_questions_{first_pdf_name}.json`
- Final PPTX: `PPTs/{first_pdf_name}.pptx` (or `PPTs/{first_pdf_name}_1.pptx` if exists, etc.)

**Features:**
- ✅ Process multiple PDFs sequentially
- ✅ Continuous question numbering across PDFs
- ✅ Custom starting question number (`--start-from N`)
- ✅ Optional answer slides (`--no-answers` flag)
- ✅ Supports both separate arguments and comma-separated format
- ✅ Uses first PDF name for output file naming
- ✅ No image OCR fallback (uses direct PDF extraction only)

**Question Numbering:**
- Default: Starts from Q1, continues sequentially
- With `--start-from 20`: First PDF starts at Q20, subsequent PDFs continue from where previous ended
- Example: If PDF1 has 10 questions starting from Q20 → Q29, PDF2 starts from Q30

**Example Output:**
```
============================================================
INTEGRATED PPT GENERATION FROM MULTIPLE PDFS
============================================================
Input PDFs: 3 file(s)
  1. pdf1.pdf
  2. pdf2.pdf
  3. pdf3.pdf

[Step 1: PDF Content Extraction (MULTIPLE PDFS)...]
[INFO] Processing 3 PDF(s) sequentially...
[OK] Extracted 21,563 characters from pdf1
[OK] Extracted 14,304 characters from pdf2
[OK] Extracted 15,052 characters from pdf3

[Step 2: QUESTION PARSING & SLIDE STRUCTURING (MULTIPLE PDFS)...]
[INFO] Questions will start from Q125
[OK] Parsed 55 questions from pdf1 (Q125 to Q179)
[OK] Parsed 37 questions from pdf2 (Q180 to Q216)
[OK] Parsed 30 questions from pdf3 (Q217 to Q246)
[INFO] Questions numbered from Q125 to Q246

[Step 3: PPTX GENERATION...]

============================================================
GENERATION COMPLETE!
============================================================
Total questions: 122
Total slides: 166
Output PPTX: PPTs/pdf1.pptx
```

**Use this when:**
- You have multiple PDF files to combine into one presentation
- Your PDF is too large (>100 pages) - split it and process separately
- You want continuous question numbering across multiple PDFs
- You need to start numbering from a specific number (e.g., continuing from a previous batch)

---

## Web Application: Streamlit Interface 🌐 NEW

**File:** `streamlit_app.py`

**Status:** ✅ Complete - User-friendly web interface for non-technical users

**What it does:**
- Provides a simple web interface for uploading PDFs and downloading PPTX files
- No command-line knowledge required
- Real-time progress tracking
- Option to include/exclude answer slides
- One-click download of generated presentations

**How it works:**
1. User uploads PDF file through web interface
2. User selects options (include/exclude answer slides)
3. App processes PDF through all three steps automatically
4. Shows progress for each step
5. Provides download button for generated PPTX

**Features:**
- ✅ File upload widget (PDF only)
- ✅ Checkbox for answer slides option
- ✅ Progress indicators for each step
- ✅ Error handling with user-friendly messages
- ✅ Download button for generated PPT
- ✅ Session state management
- ✅ Temporary file cleanup

**Dependencies:**
- `streamlit>=1.28.0` - Web framework
- All dependencies from Steps 1, 2, and 3

**To run locally:**
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key (choose one):
# Option 1: Create .streamlit/secrets.toml
# Option 2: Use existing config.yaml

# Run the app
streamlit run streamlit_app.py
```

**Streamlit Cloud Deployment:**
1. Push code to GitHub repository
2. Connect to [Streamlit Cloud](https://share.streamlit.io)
3. Add secrets in dashboard (Settings → Secrets):
   ```toml
   [anthropic]
   api_key = "your-api-key-here"
   ```
4. Deploy and share URL

**API Key Management:**
- Checks Streamlit secrets first (for cloud deployment)
- Falls back to `config.yaml` (for local development)
- Falls back to environment variable `ANTHROPIC_API_KEY`

**User Experience:**
1. Visit webapp URL
2. Upload PDF file
3. (Optional) Uncheck "Include answer slides"
4. Click "Generate PPT"
5. Wait 1-2 minutes (see progress)
6. Download generated PPTX file

**No technical knowledge required!**

---

## Step 3 Alternative: PPTX Generation using Presenton API 🆕 NEW APPROACH

**File:** `step3_presenton_api.py`

**Status:** 🆕 Available - Uses Presenton API for automatic template styling and better layouts

**What it does:**
- Reads parsed questions from Step 2
- Transforms structured JSON into text content for Presenton API
- Calls Presenton API to generate presentation with automatic styling
- Downloads the generated PPTX file
- **Benefits:** Automatic template styling, better layouts, handles tables/diagrams automatically

**How it works:**
1. Loads parsed questions JSON from Step 2
2. Formats content into text format for Presenton API
3. Creates instructions for presentation structure
4. Calls Presenton API (`POST /api/v1/ppt/presentation/generate`)
5. Polls for completion if needed
6. Downloads generated PPTX file

**Dependencies:**
- `requests` - HTTP library for API calls
- `pyyaml` - Config file parsing
- `json` - JSON parsing (built-in)

**To run:**
```bash
python step3_presenton_api.py
```

**Output:**
- `output/questions_presenton.pptx` - PPTX file generated by Presenton API

**API Configuration:**
- Get API key from: https://presenton.ai (sign up and create API key in account settings)
- Add to `config.yaml` under `presenton.api_key`
- Or set environment variable `PRESENTON_API_KEY`

**Advantages over manual approach:**
- ✅ Automatic template styling (no manual Canva import needed)
- ✅ Better slide layouts and formatting
- ✅ Handles tables, diagrams, and complex content automatically
- ✅ Professional presentation quality
- ✅ No manual positioning or styling required

**Verification checklist:**
- [ ] Is Presenton API key configured?
- [ ] Are all questions present in the generated PPTX?
- [ ] Is formatting professional and readable?
- [ ] Are tables rendered correctly?
- [ ] Are answer slides properly formatted?
- [ ] Does the presentation look good overall?

**Next:** Review generated PPTX and use directly (no Canva import needed!)

**Note:** This is an alternative to `step3_pptx_generation.py`. Choose based on your needs:
- Use `step3_presenton_api.py` if you want automatic styling and professional output
- Use `step3_pptx_generation.py` if you prefer manual control and want to import into Canva

---

## Configuration

**File:** `config.yaml`

```yaml
llm:
  provider: "anthropic"
  api_key: "your-api-key-here"
  model: "claude-sonnet-4-5-20250929"

presenton:
  api_key: "your-presenton-api-key-here"
  # Get API key from: https://presenton.ai (sign up and create API key in account settings)

output:
  directory: "./output"
```

**API Key Setup:**

**For Claude API (Step 1 & 2):**
- Option 1: Add to `config.yaml` under `llm.api_key` (recommended)
- Option 2: Set environment variable `ANTHROPIC_API_KEY`
- Option 3: Enter when prompted by script

**For Presenton API (Step 3 Alternative):**
- Option 1: Add to `config.yaml` under `presenton.api_key` (recommended)
- Option 2: Set environment variable `PRESENTON_API_KEY`
- Get API key: Sign up at https://presenton.ai and create API key in account settings

---

## File Structure

```
PPT Maker/
├── generate_ppt_from_pdf.py           # 🚀 Single PDF script (RECOMMENDED)
├── generate_ppt_from_multiple_pdfs.py # 🆕 Multi-PDF script (for large PDFs)
├── step1_pdf_extraction.py            # Step 1: PDF extraction (✅ Complete)
├── step2_question_parsing.py          # Step 2: Question parsing (✅ Complete)
├── step3_pptx_generation.py           # Step 3: PPTX generation (legacy/old version)
├── step3_pptx_new.py                  # Step 3: PPTX generation (✅ Current/Refined)
├── step3_presenton_api.py             # Step 3 Alternative: PPTX via Presenton API (🆕 Available)
├── config.yaml                        # Configuration file
├── PLAN.md                            # This file - master plan
├── output/                            # Intermediate output directory
│   ├── extracted_pdf_content_{pdf_name}.txt
│   ├── parsed_questions_{pdf_name}.json
│   ├── parsed_questions_{pdf_name}_preview.txt
│   └── current_pdf_name.txt           # PDF name tracker
├── PPTs/                              # Final PPTX output directory
│   └── {pdf_name}.pptx                # Generated presentations
├── Adobe-Scan-12-Dec-2025.pdf         # Input PDF (example)
├── Adobe-Scan-03-Nov-2025.pdf         # Input PDF (example)
└── _ch- 7 spp.jpg                     # Template slide image
```

---

## Code Documentation Approach

**Inline Comments:** All code files have detailed inline comments explaining what each line/block does. This makes the code self-documenting and easier to maintain.

**No separate documentation files:** Instead of separate MD files explaining code, we use inline comments directly in the code files.

---

## Updates Log

- **2025-12-13**: Created Step 1 with LLM-based PDF extraction
- **2025-12-13**: Removed topic verification (biology vs physics) - focus on extraction quality only
- **2025-12-13**: Added detailed inline comments to all code
- **2025-12-13**: Consolidated README and STEP1_INSTRUCTIONS into single PLAN.md
- **2025-12-13**: Completed Step 2 - Question parsing with slide structuring
- **2025-12-13**: Completed Step 3 - PPTX generation (content only, ready for Canva)
- **2025-12-13**: Created Step 3 Alternative - Presenton API integration
- **2025-12-13**: Created new Step 3 implementation (`step3_pptx_new.py`) using python-pptx best practices
- **2025-12-13**: Updated slide dimensions to standard widescreen (13.333" × 7.5")
- **2025-12-13**: Adjusted text box dimensions to match Canva template exactly
- **2025-12-13**: Changed font to Frankfurter Medium
- **2025-12-13**: Unified font size to 25pt (results in 38pt in Canva)
- **2025-12-13**: Fixed double dots issue (Q1., Ans1. now have single dot)
- **2025-12-13**: Simplified diagram descriptions to just [Diagram]
- **2025-12-13**: Added smart table detection (skips table if it's just options)
- **2025-12-13**: Removed bullets from multiple choice options
- **2025-12-13**: Updated all steps to use PDF-based file naming
- **2025-12-13**: Changed output location to `PPTs/` folder instead of `output/`
- **2025-12-13**: Created integrated script `generate_ppt_from_pdf.py` for one-command execution
- **2025-12-13**: Added automatic file conflict handling (auto-numbering for existing files)
- **2025-12-13**: Updated Step 1 to accept PDF as command line argument
- **2026-01-01**: Added multi-PDF processing script (`generate_ppt_from_multiple_pdfs.py`)
- **2026-01-01**: Added `extract_multiple_pdfs()` function to step1 for sequential PDF processing
- **2026-01-01**: Added `parse_multiple_pdfs_content()` and `parse_questions_with_llm_offset()` functions to step2
- **2026-01-01**: Added `extract_with_llm_no_fallback()` function (no image OCR fallback)
- **2026-01-01**: Added `--start-from N` flag for custom question numbering
- **2026-01-01**: Increased max_tokens to 32000 in parsing functions for larger PDFs

---

## Next Steps

1. ✅ **Step 1 Complete** - PDF extraction working (with PDF-based naming)
2. ✅ **Step 2 Complete** - Question parsing working (with PDF-based naming)
3. ✅ **Step 3 Complete** - PPTX generation refined and optimized for Canva
4. ✅ **Integrated Script Complete** - One-command execution available
5. 🆕 **Step 3 Alternative Available** - PPTX via Presenton API (automatic styling)

**Current Workflow (Recommended):**

**🚀 Primary Approaches:**

**Single PDF:**
```bash
python generate_ppt_from_pdf.py "Your-PDF-File.pdf"
```
- Single command runs all three steps automatically
- Output: `PPTs/{PDF-name}.pptx`
- Handles file conflicts automatically
- Shows progress for each step

**Multiple PDFs (Large PDFs or Combining PDFs):**
```bash
python generate_ppt_from_multiple_pdfs.py "pdf1.pdf" "pdf2.pdf" "pdf3.pdf"
```
- Processes multiple PDFs sequentially
- Maintains continuous question numbering
- Better quality for large PDFs (>100 pages)
- Supports `--start-from N` for custom numbering

**Alternative: Manual Step-by-Step Approach**
- Step 1: `python step1_pdf_extraction.py "PDF-File.pdf"`
- Step 2: `python step2_question_parsing.py`
- Step 3: `python step3_pptx_new.py`
- Output: `PPTs/{PDF-name}.pptx`

**Features:**
- ✅ PDF-based file naming (all outputs named after input PDF)
- ✅ Output saved to `PPTs/` folder
- ✅ Automatic conflict handling (adds number suffix if file exists)
- ✅ Font: Frankfurter Medium, 25pt (38pt in Canva)
- ✅ Text box dimensions match Canva template exactly
- ✅ Smart table/options handling
- ✅ Clean formatting optimized for Canva import

**Alternative Approaches:**

**Option A: Legacy Manual Approach**
- Uses `step3_pptx_generation.py` (older implementation)
- Basic formatting, requires more manual adjustment in Canva

**Option B: Presenton API Approach**
- Uses `step3_presenton_api.py`
- Automatic styling, but requires API credits
- Good for bulk generation if credits available

**Status:** ✅ **Project Complete** - All core features working and refined!

**🆕 Latest Addition: Multi-PDF Processing**
- Process multiple PDFs with continuous numbering
- Custom starting question numbers
- Better quality for large PDFs

