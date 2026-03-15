"""
Step 1: PDF Content Extraction using LLM
Extract text content from PDF using Claude API (similar to Perplexity workflow).

This step helps us verify:
1. Can we read the PDF with LLM?
2. Is the content extraction working correctly?
3. Are questions visible and properly extracted?
"""
from anthropic import Anthropic  # Import Anthropic SDK for Claude API
from pathlib import Path  # For file path operations
import sys  # For system operations and exit
import base64  # For encoding PDF to base64


def load_pdf_as_base64(pdf_path: str) -> str:
    """
    Load PDF file and convert to base64 for API transmission.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Base64-encoded string of PDF content, or None if error
    """
    try:
        # Open PDF file in binary read mode
        with open(pdf_path, 'rb') as f:
            # Read all bytes from the PDF file
            pdf_bytes = f.read()
            # Encode PDF bytes to base64 string for API transmission
            return base64.b64encode(pdf_bytes).decode('utf-8')
    except Exception as e:
        # Print error if file reading fails
        print(f"[ERROR] Failed to read PDF: {e}")
        return None


def extract_with_llm(pdf_path: str, api_key: str, extract_year: bool = False) -> str:
    """
    Extract text content from PDF using Claude API.
    This is the main extraction function that sends PDF to Claude and gets text back.
    
    Args:
        pdf_path: Path to PDF file
        api_key: Anthropic API key for authentication
        extract_year: Whether to extract exam information from previous year question papers (default: False)
        
    Returns:
        Extracted text content as string, or None if extraction fails
    """
    # Load PDF and convert to base64 for API
    print("[INFO] Loading PDF file...")
    pdf_base64 = load_pdf_as_base64(pdf_path)
    
    # Check if PDF was loaded successfully
    if not pdf_base64:
        return None
    
    # Inform user that we're sending to API (may take time)
    print("[INFO] Sending PDF to Claude API for extraction...")
    print("[INFO] This may take 30-60 seconds...")
    
    try:
        # Initialize Anthropic client with API key
        client = Anthropic(api_key=api_key)
        
        # Read PDF as binary (needed for document attachment)
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        # Build extraction prompt
        extraction_prompt = """Extract all text content from this PDF. 

Please extract:
1. All questions (ignore question numbers in PDF, just extract the question text)
2. All options (if multiple choice)
3. Any tables or diagrams mentioned
4. Answers if provided"""
        
        # Add year extraction instruction if enabled
        if extract_year:
            extraction_prompt += """
5. Exam information: If this is a previous year question paper, extract the full exam information (e.g., "[CBSE 2023 (57/1/1)]", "[CBSE Delhi 2015 [HOTS]]", "[CBSE Sample Question Paper 2024]"). Include this at the beginning of the extracted content in the format: "EXAM_INFO: [full exam information]" if found."""
        
        extraction_prompt += """

Return the extracted content in a clear, structured format. Maintain the order of questions as they appear in the PDF.

Extract all content accurately and completely."""
        
        # Create API request to Claude
        # We send both a text prompt and the PDF document
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",  # Claude model version
            max_tokens=16000,  # Maximum response length
            messages=[{
                "role": "user",  # User message
                "content": [
                    {
                        "type": "text",  # Text instruction
                        "text": extraction_prompt
                    },
                    {
                        "type": "document",  # PDF document attachment
                        "source": {
                            "type": "base64",  # Base64 encoding
                            "media_type": "application/pdf",  # PDF MIME type
                            "data": pdf_base64  # Base64-encoded PDF data
                        }
                    }
                ]
            }]
        )
        
        # Combine all content blocks (in case there are multiple)
        extracted_text = ""
        for content_block in response.content:
            if hasattr(content_block, 'text'):
                extracted_text += content_block.text
        
        # Check stop reason first - handle refusal specifically
        if hasattr(response, 'stop_reason'):
            if response.stop_reason == "refusal":
                print("[WARNING] Claude API refused to process the PDF document attachment.")
                print("[INFO] This may be due to PDF format or content policy restrictions.")
                print("[INFO] Automatically trying alternative method: converting PDF to images...")
                # Try image-based extraction as fallback
                return extract_with_llm_images(pdf_path, api_key)
            elif response.stop_reason == "max_tokens":
                print("[WARNING] Response was truncated due to max_tokens limit!")
                print("[WARNING] Some content may be missing. Consider increasing max_tokens or splitting the PDF.")
            elif response.stop_reason:
                print(f"[INFO] Response stop reason: {response.stop_reason}")
        
        # Validate we got content
        if not extracted_text or len(extracted_text.strip()) < 100:
            print("[ERROR] Extracted text is too short or empty. Response may have failed.")
            print(f"[DEBUG] Response content blocks: {len(response.content)}")
            if hasattr(response, 'stop_reason'):
                print(f"[DEBUG] Stop reason: {response.stop_reason}")
                if response.stop_reason == "refusal":
                    print("[INFO] Trying alternative method: converting PDF to images...")
                    return extract_with_llm_images(pdf_path, api_key, extract_year)
            # Show actual response content for debugging
            if extracted_text:
                print(f"[DEBUG] Response content preview: {extracted_text[:200]}")
            return None
        
        print(f"[OK] Content extracted successfully: {len(extracted_text):,} characters")
        return extracted_text
        
    except Exception as e:
        # Handle API errors
        print(f"[ERROR] LLM extraction failed: {e}")
        if "api_key" in str(e).lower() or "authentication" in str(e).lower():
            # API key issue
            print("\n[ERROR] API key issue. Please check your API key in config.")
        elif "file" in str(e).lower() or "attachment" in str(e).lower():
            # PDF attachment format issue - try alternative method
            print("\n[INFO] Claude API may not support direct PDF attachments in this format.")
            print("[INFO] Trying alternative method: converting PDF to images first...")
            return extract_with_llm_images(pdf_path, api_key, extract_year)
        return None


def extract_with_llm_images(pdf_path: str, api_key: str, extract_year: bool = False) -> str:
    """
    Alternative extraction method: Convert PDF to images and send to Claude Vision API.
    This is a fallback if direct PDF attachment doesn't work.
    
    Args:
        pdf_path: Path to PDF file
        api_key: Anthropic API key
        extract_year: Whether to extract exam information from previous year question papers (default: False)
        
    Returns:
        Extracted text from all pages, or None if fails
    """
    # Try importing required libraries
    try:
        from pdf2image import convert_from_path  # Convert PDF pages to images
        from PIL import Image  # Image processing
        import io  # For in-memory image buffer
    except ImportError:
        # Libraries not installed
        print("[ERROR] pdf2image not installed. Install with: pip install pdf2image")
        print("[INFO] Or use Poppler + pdf2image for this method")
        return None
    
    # Convert PDF pages to images
    print("[INFO] Converting PDF to images...")
    try:
        # Convert each PDF page to a PIL Image object
        # Specify Poppler path explicitly
        poppler_path = r'C:\Poppler\poppler-25.12.0\Library\bin'
        images = convert_from_path(pdf_path, poppler_path=poppler_path)
        print(f"[OK] Converted {len(images)} pages to images")
    except Exception as e:
        # Conversion failed (usually Poppler not installed or wrong path)
        print(f"[ERROR] Failed to convert PDF to images: {e}")
        print(f"[INFO] Checked Poppler path: {poppler_path}")
        print("[INFO] Make sure Poppler is installed and the path is correct.")
        return None
    
    # Initialize Claude client with longer timeout for large PDFs
    print("[INFO] Sending pages to Claude Vision API...")
    client = Anthropic(
        api_key=api_key,
        timeout=300.0  # 5 minutes timeout for large PDFs
    )
    all_text = []  # Store text from each page
    
    # Process each page image
    for i, image in enumerate(images, 1):
        # Show progress
        print(f"  Processing page {i}/{len(images)}...", end='\r')
        
        # Convert PIL image to base64
        buffer = io.BytesIO()  # Create in-memory buffer
        image.save(buffer, format='PNG')  # Save image as PNG to buffer
        image_bytes = buffer.getvalue()  # Get bytes from buffer
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')  # Encode to base64
        
        try:
            # Send image to Claude Vision API
            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",  # Claude model
                max_tokens=4000,  # Max tokens per page
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Extract all text content from this page (page {i}). Include questions, options, tables, and any other text. Maintain formatting where possible." + (
                                " If this is page 1 and contains exam information (e.g., '[CBSE 2023 (57/1/1)]', '[CBSE Delhi 2015 [HOTS]]'), include it at the beginning in format: 'EXAM_INFO: [full exam information]'." if extract_year and i == 1 else ""
                            )
                        },
                        {
                            "type": "image",  # Image attachment
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",  # PNG format
                                "data": image_base64  # Base64 image data
                            }
                        }
                    ]
                }]
            )
            
            # Combine all content blocks (in case there are multiple)
            page_text = ""
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    page_text += content_block.text
            
            # Check if response was truncated
            if hasattr(response, 'stop_reason') and response.stop_reason == "max_tokens":
                print(f"\n[WARNING] Page {i} response was truncated due to max_tokens limit!")
            
            # Store page text with page number marker
            all_text.append(f"\n--- PAGE {i} ---\n{page_text}\n")
            
        except Exception as e:
            # Error processing this page
            print(f"\n[ERROR] Failed to process page {i}: {e}")
            all_text.append(f"\n--- PAGE {i} ---\n[ERROR: Could not extract]\n")
    
    # Combine all page texts
    print(f"\n[OK] Extracted text from {len(images)} pages")
    return "\n".join(all_text)


def get_api_key() -> str:
    """
    Get API key from Streamlit secrets, config file, or environment variable.
    Tries multiple sources in order of preference.
    
    Returns:
        API key string, or empty string if not found
    """
    # Try Streamlit secrets first (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'anthropic' in st.secrets:
            api_key = st.secrets['anthropic']['api_key']
            if api_key:
                return api_key
    except:
        # Streamlit not available or secrets not configured, continue to next method
        pass
    
    # Try config file
    try:
        import yaml  # YAML parser for config file
        config_path = Path("config.yaml")  # Config file path
        if config_path.exists():  # Check if config file exists
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)  # Load YAML config
                # Get API key from nested structure: llm -> api_key
                return config.get('llm', {}).get('api_key', '')
    except:
        # Config file read failed, continue to next method
        pass
    
    # Try environment variable as fallback
    import os
    return os.getenv('ANTHROPIC_API_KEY', '')  # Get from environment or return empty


def analyze_content(text: str):
    """
    Analyze extracted content for quality and completeness.
    Checks for question indicators, answers, options, and text quality.
    
    Args:
        text: Extracted text content
        
    Returns:
        Tuple of (issues list, good_signs list)
    """
    text_lower = text.lower()  # Convert to lowercase for case-insensitive search
    
    issues = []  # List to store problems found
    good_signs = []  # List to store positive indicators
    
    # Check for question indicators (Q1, Q2, question, ?, answer, option)
    question_indicators = ['q1', 'q2', 'question', '?', 'ans.', 'answer', 'option']
    found_questions = [ind for ind in question_indicators if ind in text_lower]
    if found_questions:
        # Found question indicators - good sign
        good_signs.append(f"Found question indicators: {', '.join(found_questions[:3])}")
    else:
        # No question indicators found - potential issue
        issues.append("No question indicators found")
    
    # Count questions using regex pattern
    import re
    # Pattern matches: Q1, Q2, Question 1, etc. at start of line
    question_count = len(re.findall(r'(?:^|\n)\s*(?:q\d+|question\s+\d+)', text_lower, re.MULTILINE))
    if question_count > 0:
        # Found questions - good sign
        good_signs.append(f"Found approximately {question_count} questions")
    
    # Check for answer sections
    if 'answer' in text_lower or 'ans.' in text_lower:
        good_signs.append("Found answer sections")
    
    # Check for multiple choice options (a), b), etc.)
    if 'option' in text_lower or 'a)' in text_lower or 'b)' in text_lower:
        good_signs.append("Found multiple choice options")
    
    # Check text quality - length check
    if len(text.strip()) < 500:
        # Text too short - may be incomplete
        issues.append("Extracted text seems too short - may be incomplete")
    elif len(text.strip()) > 1000:
        # Substantial content - good sign
        good_signs.append("Substantial content extracted")
    
    # Check for truncation indicators (many ellipses)
    if text.count('...') > 10:
        # Many ellipses suggest truncation
        issues.append("Many ellipses found - content may be truncated")
    
    return issues, good_signs


def save_extracted_text(text: str, output_file: str):
    """
    Save extracted text to a file for manual review.
    
    Args:
        text: Extracted text content
        output_file: Path to output file
    """
    # Create output directory if it doesn't exist
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Write text to file with header
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")  # Header separator
        f.write("EXTRACTED PDF CONTENT (via LLM)\n")  # Header text
        f.write("=" * 60 + "\n\n")  # Header separator
        f.write(text)  # Write extracted content
    
    print(f"[OK] Extracted text saved to: {output_file}")


def extract_with_llm_no_fallback(pdf_path: str, api_key: str, extract_year: bool = False) -> str:
    """
    Extract text content from PDF using Claude API (without image fallback).
    This is the same as extract_with_llm() but returns None on error instead of
    calling the image OCR fallback.
    
    Args:
        pdf_path: Path to PDF file
        api_key: Anthropic API key for authentication
        extract_year: Whether to extract exam information from previous year question papers (default: False)
        
    Returns:
        Extracted text content as string, or None if extraction fails
    """
    # Load PDF and convert to base64 for API
    print("[INFO] Loading PDF file...")
    pdf_base64 = load_pdf_as_base64(pdf_path)
    
    # Check if PDF was loaded successfully
    if not pdf_base64:
        return None
    
    # Inform user that we're sending to API (may take time)
    print("[INFO] Sending PDF to Claude API for extraction...")
    print("[INFO] This may take 30-60 seconds...")
    
    try:
        # Initialize Anthropic client with API key
        client = Anthropic(api_key=api_key)
        
        # Read PDF as binary (needed for document attachment)
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        # Build extraction prompt
        extraction_prompt = """Extract all text content from this PDF. 

Please extract:
1. All questions (ignore question numbers in PDF, just extract the question text)
2. All options (if multiple choice)
3. Any tables or diagrams mentioned
4. Answers if provided"""
        
        # Add year extraction instruction if enabled
        if extract_year:
            extraction_prompt += """
5. Exam information: If this is a previous year question paper, extract the full exam information (e.g., "[CBSE 2023 (57/1/1)]", "[CBSE Delhi 2015 [HOTS]]", "[CBSE Sample Question Paper 2024]"). Include this at the beginning of the extracted content in the format: "EXAM_INFO: [full exam information]" if found."""
        
        extraction_prompt += """

Return the extracted content in a clear, structured format. Maintain the order of questions as they appear in the PDF.

Extract all content accurately and completely."""
        
        # Create API request to Claude
        # We send both a text prompt and the PDF document
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",  # Claude model version
            max_tokens=16000,  # Maximum response length
            messages=[{
                "role": "user",  # User message
                "content": [
                    {
                        "type": "text",  # Text instruction
                        "text": extraction_prompt
                    },
                    {
                        "type": "document",  # PDF document attachment
                        "source": {
                            "type": "base64",  # Base64 encoding
                            "media_type": "application/pdf",  # PDF MIME type
                            "data": pdf_base64  # Base64-encoded PDF data
                        }
                    }
                ]
            }]
        )
        
        # Combine all content blocks (in case there are multiple)
        extracted_text = ""
        for content_block in response.content:
            if hasattr(content_block, 'text'):
                extracted_text += content_block.text
        
        # Check stop reason first - handle refusal specifically
        if hasattr(response, 'stop_reason'):
            if response.stop_reason == "refusal":
                print("[WARNING] Claude API refused to process the PDF document attachment.")
                print("[INFO] This may be due to PDF format or content policy restrictions.")
                print("[ERROR] Cannot use image fallback in no-fallback mode. Please use extract_with_llm() instead.")
                return None
            elif response.stop_reason == "max_tokens":
                print("[WARNING] Response was truncated due to max_tokens limit!")
                print("[WARNING] Some content may be missing. Consider increasing max_tokens or splitting the PDF.")
            elif response.stop_reason:
                print(f"[INFO] Response stop reason: {response.stop_reason}")
        
        # Validate we got content
        if not extracted_text or len(extracted_text.strip()) < 100:
            print("[ERROR] Extracted text is too short or empty. Response may have failed.")
            print(f"[DEBUG] Response content blocks: {len(response.content)}")
            if hasattr(response, 'stop_reason'):
                print(f"[DEBUG] Stop reason: {response.stop_reason}")
            # Show actual response content for debugging
            if extracted_text:
                print(f"[DEBUG] Response content preview: {extracted_text[:200]}")
            return None
        
        print(f"[OK] Content extracted successfully: {len(extracted_text):,} characters")
        return extracted_text
        
    except Exception as e:
        # Handle API errors (no fallback to image extraction)
        print(f"[ERROR] LLM extraction failed: {e}")
        if "api_key" in str(e).lower() or "authentication" in str(e).lower():
            # API key issue
            print("\n[ERROR] API key issue. Please check your API key in config.")
        return None


def extract_multiple_pdfs(pdf_paths: list[str], api_key: str, extract_year: bool = False) -> tuple[str, list[tuple[str, str]]]:
    """
    Extract text content from multiple PDFs sequentially.
    
    Args:
        pdf_paths: List of paths to PDF files
        api_key: Anthropic API key for authentication
        extract_year: Whether to extract exam information from previous year question papers (default: False)
        
    Returns:
        Tuple of (combined_text: str, pdf_contents: list[tuple[str, str]])
        where pdf_contents is list of (pdf_name, extracted_text) tuples
    """
    pdf_contents = []  # List of (pdf_name, extracted_text) tuples
    combined_parts = []  # List of text parts to combine
    
    print(f"[INFO] Processing {len(pdf_paths)} PDF(s) sequentially...")
    print()
    
    for i, pdf_path in enumerate(pdf_paths, 1):
        pdf_path_obj = Path(pdf_path)
        pdf_name = pdf_path_obj.stem
        
        print(f"[INFO] Processing PDF {i}/{len(pdf_paths)}: {pdf_name}")
        
        # Check if PDF exists
        if not pdf_path_obj.exists():
            print(f"[ERROR] PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Extract text using LLM (no fallback)
        extracted_text = extract_with_llm_no_fallback(pdf_path, api_key, extract_year)
        
        if not extracted_text:
            print(f"[ERROR] Failed to extract content from PDF: {pdf_path}")
            raise RuntimeError(f"Failed to extract content from PDF: {pdf_path}")
        
        # Store PDF content
        pdf_contents.append((pdf_name, extracted_text))
        
        # Add to combined text with separator
        combined_parts.append(f"\n\n=== PDF: {pdf_name} ===\n\n{extracted_text}")
        
        print(f"[OK] Extracted {len(extracted_text):,} characters from {pdf_name}")
        print()
    
    # Combine all texts
    combined_text = "\n".join(combined_parts)
    
    print(f"[OK] Successfully extracted content from {len(pdf_paths)} PDF(s)")
    print(f"[INFO] Total combined text length: {len(combined_text):,} characters")
    
    return combined_text, pdf_contents


if __name__ == '__main__':
    """
    Main execution block - runs when script is executed directly.
    """
    # Accept PDF filename as command line argument or use default
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default to the new PDF file
        pdf_path = "Adobe-Scan-03-Nov-2025.pdf"
    
    # Extract base name without extension for naming outputs
    pdf_name = Path(pdf_path).stem  # e.g., "Adobe-Scan-03-Nov-2025"
    
    # Print header
    print("=" * 60)
    print("STEP 1: PDF CONTENT EXTRACTION (using LLM)")
    print("=" * 60)
    print()
    print(f"[INFO] Processing PDF: {pdf_path}")
    print(f"[INFO] PDF name: {pdf_name}")
    print()
    
    # Check if PDF file exists
    if not Path(pdf_path).exists():
        print(f"[ERROR] PDF file not found: {pdf_path}")
        sys.exit(1)  # Exit with error code
    
    # Get API key from config or environment
    api_key = get_api_key()
    if not api_key:
        # No API key found - prompt user
        print("[ERROR] API key not found!")
        print("\nPlease provide API key:")
        print("  1. Create config.yaml with:")
        print("     llm:")
        print("       api_key: 'your-api-key-here'")
        print("  2. Or set environment variable: ANTHROPIC_API_KEY")
        print("  3. Or enter it when prompted")
        
        # Prompt for API key
        api_key = input("\nEnter Anthropic API key (or press Enter to exit): ").strip()
        if not api_key:
            sys.exit(1)  # Exit if no key provided
    
    # Extract text using LLM
    extracted_text = extract_with_llm(pdf_path, api_key)
    
    if extracted_text:
        # Analyze extracted content for quality
        issues, good_signs = analyze_content(extracted_text)
        
        # Save to file for review (named after PDF)
        output_file = f"output/extracted_pdf_content_{pdf_name}.txt"
        save_extracted_text(extracted_text, output_file)
        
        # Save PDF name for next steps
        pdf_name_file = Path("output/current_pdf_name.txt")
        pdf_name_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pdf_name_file, 'w', encoding='utf-8') as f:
            f.write(pdf_name)
        print(f"[INFO] Saved PDF name for next steps: {pdf_name}")
        
        # Print summary
        print(f"\n[SUMMARY]")
        print(f"Extracted text length: {len(extracted_text):,} characters")
        
        # Print good signs if any
        if good_signs:
            print(f"\n[GOOD SIGNS]")
            for sign in good_signs:
                print(f"  [OK] {sign}")
        
        # Print issues if any
        if issues:
            print(f"\n[ISSUES FOUND]")
            for issue in issues:
                print(f"  [WARNING] {issue}")
        
        # Show sample of extracted content
        print(f"\n[SAMPLE CONTENT]")
        print("-" * 60)
        print(extracted_text[:800])  # First 800 characters
        if len(extracted_text) > 800:
            print("...")  # Indicate more content
        print("-" * 60)
        
        # Print review checklist
        print(f"\n[REVIEW CHECKLIST]")
        print(f"Please review: {output_file}")
        print("  [ ] Is the text readable and complete?")
        print("  [ ] Are questions properly extracted?")
        print("  [ ] Are options/answers included (if applicable)?")
        print("  [ ] Are tables/diagrams mentioned or described?")
        print("  [ ] Is the content in the correct order?")
        print("  [ ] Is the extraction accurate (no missing or incorrect content)?")
        print("\nOnce verified, we can proceed to Step 2: Question Parsing")
    else:
        # Extraction failed
        print("\n[ERROR] Failed to extract content from PDF")
        print("\nPossible issues:")
        print("  1. API key invalid or expired")
        print("  2. PDF file is corrupted")
        print("  3. API rate limits or connection issues")


def split_pdf_at_pages(pdf_path: str, split_pages: list[int]) -> list[str]:
    """
    Split PDF at specified page numbers (no overlap).
    
    Args:
        pdf_path: Path to PDF file
        split_pages: List of page numbers (1-indexed) where to split
        
    Returns:
        List of paths to split PDF files
    """
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except ImportError:
        print("[ERROR] PyPDF2 not installed. Install with: pip install PyPDF2")
        return []
    
    from pathlib import Path
    
    pdf_path_obj = Path(pdf_path)
    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    
    # Create output directory
    output_dir = pdf_path_obj.parent / f"{pdf_path_obj.stem}_split"
    output_dir.mkdir(exist_ok=True)
    
    chunk_files = []
    start_page = 0  # 0-indexed
    
    # Sort split pages and ensure they're within valid range
    split_pages = sorted([p for p in split_pages if 1 <= p <= total_pages])
    
    if not split_pages:
        print("[WARNING] No valid split pages provided. Returning original PDF.")
        return [pdf_path]
    
    print(f"[INFO] Splitting PDF at pages: {split_pages}")
    print(f"[INFO] Total pages: {total_pages}")
    
    for i, split_page in enumerate(split_pages):
        # Convert 1-indexed to 0-indexed (split_page is the first page of next chunk)
        end_page = min(split_page - 1, total_pages - 1)  # Last page of current chunk
        
        # Create writer for this chunk
        writer = PdfWriter()
        
        # Add pages from start to end
        for page_num in range(start_page, end_page + 1):
            writer.add_page(reader.pages[page_num])
        
        # Save chunk
        chunk_filename = f"{pdf_path_obj.stem}_part{i+1}_{start_page+1}-{end_page+1}.pdf"
        chunk_path = output_dir / chunk_filename
        
        with open(chunk_path, 'wb') as output_file:
            writer.write(output_file)
        
        chunk_files.append(str(chunk_path))
        print(f"[OK] Created chunk {i+1}: {chunk_filename} (pages {start_page+1}-{end_page+1})")
        
        # Start next chunk from the split page
        start_page = split_page
    
    # Handle remaining pages after last split
    if start_page < total_pages:
        writer = PdfWriter()
        for page_num in range(start_page, total_pages):
            writer.add_page(reader.pages[page_num])
        
        chunk_filename = f"{pdf_path_obj.stem}_part{len(split_pages)+1}_{start_page+1}-{total_pages}.pdf"
        chunk_path = output_dir / chunk_filename
        
        with open(chunk_path, 'wb') as output_file:
            writer.write(output_file)
        
        chunk_files.append(str(chunk_path))
        print(f"[OK] Created final chunk: {chunk_filename} (pages {start_page+1}-{total_pages})")
    
    print(f"\n[SUCCESS] Split PDF into {len(chunk_files)} chunks")
    print(f"[INFO] Chunk files saved in: {output_dir}")
    
    return chunk_files
