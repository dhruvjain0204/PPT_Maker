"""
Integrated Script: Generate PPTX from PDF
Combines all three steps into a single script:
1. PDF Content Extraction (Step 1)
2. Question Parsing & Slide Structuring (Step 2)
3. PPTX Generation (Step 3)

Usage:
    python generate_ppt_from_pdf.py "input.pdf"
    python generate_ppt_from_pdf.py "Adobe-Scan-03-Nov-2025.pdf"
"""
import sys
from pathlib import Path
from step1_pdf_extraction import (
    get_api_key as get_api_key_step1,
    extract_with_llm,
    analyze_content,
    save_extracted_text
)
from step2_question_parsing import (
    get_api_key as get_api_key_step2,
    load_extracted_content,
    parse_questions_with_llm,
    validate_questions,
    save_parsed_questions,
    create_preview
)
from step3_pptx_new import PPTXGenerator, load_parsed_questions
from pptx import Presentation


def run_step1(pdf_path: str) -> tuple:
    """
    Run Step 1: PDF Content Extraction
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Tuple of (success: bool, pdf_name: str, extracted_text: str)
    """
    print("\n" + "=" * 60)
    print("STEP 1: PDF CONTENT EXTRACTION")
    print("=" * 60)
    print()
    
    # Extract PDF name
    pdf_name = Path(pdf_path).stem
    print(f"[INFO] Processing PDF: {pdf_path}")
    print(f"[INFO] PDF name: {pdf_name}")
    print()
    
    # Check if PDF exists
    if not Path(pdf_path).exists():
        print(f"[ERROR] PDF file not found: {pdf_path}")
        return False, pdf_name, None
    
    # Get API key
    api_key = get_api_key_step1()
    if not api_key:
        print("[ERROR] API key not found!")
        print("\nPlease provide API key in config.yaml")
        return False, pdf_name, None
    
    # Extract text
    print("[INFO] Sending PDF to Claude API for extraction...")
    print("[INFO] This may take 30-60 seconds...")
    extracted_text = extract_with_llm(pdf_path, api_key)
    
    if not extracted_text:
        print("[ERROR] Failed to extract content from PDF")
        return False, pdf_name, None
    
    # Analyze content
    issues, good_signs = analyze_content(extracted_text)
    
    # Save extracted text
    output_file = f"output/extracted_pdf_content_{pdf_name}.txt"
    save_extracted_text(extracted_text, output_file)
    
    # Save PDF name for next steps
    pdf_name_file = Path("output/current_pdf_name.txt")
    pdf_name_file.parent.mkdir(parents=True, exist_ok=True)
    with open(pdf_name_file, 'w', encoding='utf-8') as f:
        f.write(pdf_name)
    
    print(f"[OK] Step 1 complete: {len(extracted_text):,} characters extracted")
    return True, pdf_name, extracted_text


def run_step2(pdf_name: str) -> tuple:
    """
    Run Step 2: Question Parsing & Slide Structuring
    
    Args:
        pdf_name: PDF name (without extension)
        
    Returns:
        Tuple of (success: bool, questions: list)
    """
    print("\n" + "=" * 60)
    print("STEP 2: QUESTION PARSING & SLIDE STRUCTURING")
    print("=" * 60)
    print()
    
    # Input file from Step 1
    input_file = f"output/extracted_pdf_content_{pdf_name}.txt"
    
    if not Path(input_file).exists():
        print(f"[ERROR] Input file not found: {input_file}")
        print("[INFO] Please run Step 1 first")
        return False, None
    
    # Get API key
    api_key = get_api_key_step2()
    if not api_key:
        print("[ERROR] API key not found!")
        return False, None
    
    # Load extracted content
    print(f"[INFO] Loading extracted content from: {input_file}")
    content = load_extracted_content(input_file)
    
    if not content:
        print("[ERROR] Failed to load extracted content")
        return False, None
    
    print(f"[OK] Loaded {len(content):,} characters of content")
    
    # Parse questions
    print("[INFO] Sending content to Claude API for parsing...")
    print("[INFO] This may take 30-60 seconds...")
    questions = parse_questions_with_llm(content, api_key)
    
    if not questions:
        print("[ERROR] Failed to parse questions")
        return False, None
    
    # Validate questions
    print("\n[INFO] Validating parsed questions...")
    is_valid, issues, stats = validate_questions(questions)
    
    if issues:
        print(f"[WARNING] Found {len(issues)} validation issues:")
        for issue in issues[:5]:
            print(f"  - {issue}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")
    else:
        print("[OK] All questions validated successfully")
    
    # Save parsed questions
    output_file = f"output/parsed_questions_{pdf_name}.json"
    save_parsed_questions(questions, output_file)
    
    # Create preview
    preview_file = f"output/parsed_questions_{pdf_name}_preview.txt"
    create_preview(questions, preview_file)
    
    print(f"[OK] Step 2 complete: {stats['total_questions']} questions, {stats['total_slides']} slides")
    return True, questions


def get_unique_output_filename(base_name: str, folder: str = "PPTs") -> str:
    """
    Get a unique output filename by adding a number suffix if file exists.
    
    Args:
        base_name: Base filename (without extension)
        folder: Output folder name
        
    Returns:
        Unique filename path
    """
    folder_path = Path(folder)
    folder_path.mkdir(exist_ok=True)
    
    output_file = folder_path / f"{base_name}.pptx"
    
    # If file doesn't exist, return it
    if not output_file.exists():
        return str(output_file)
    
    # If file exists, add number suffix
    counter = 1
    while True:
        output_file = folder_path / f"{base_name}_{counter}.pptx"
        if not output_file.exists():
            print(f"[INFO] Output file already exists, using: {output_file.name}")
            return str(output_file)
        counter += 1


def run_step3(pdf_name: str, include_answers: bool = True) -> str:
    """
    Run Step 3: PPTX Generation
    
    Args:
        pdf_name: PDF name (without extension)
        include_answers: Whether to include answer slides (default: True)
        
    Returns:
        Output file path, or None if failed
    """
    print("\n" + "=" * 60)
    print("STEP 3: PPTX GENERATION")
    print("=" * 60)
    print()
    
    # Input file from Step 2
    input_file = f"output/parsed_questions_{pdf_name}.json"
    
    # Load parsed questions
    questions = load_parsed_questions(input_file)
    
    if not questions:
        print("[ERROR] Failed to load parsed questions")
        return None
    
    # Count slides (excluding answers if include_answers is False)
    if include_answers:
        total_slides = sum(len(q.get('slides', [])) for q in questions)
    else:
        # Count only non-answer slides
        total_slides = 0
        for q in questions:
            for slide in q.get('slides', []):
                if slide.get('slide_type') != 'answer':
                    total_slides += 1
    
    answer_status = "with answers" if include_answers else "without answers"
    print(f"[INFO] Will generate {total_slides} slides from {len(questions)} questions ({answer_status})")
    
    # Get unique output filename (handles existing files)
    output_file = get_unique_output_filename(pdf_name)
    
    # Generate PPTX
    generator = PPTXGenerator()
    
    print("[INFO] Creating PowerPoint presentation...")
    generator.generate(questions, output_file, include_answers=include_answers)
    
    # Verify output
    try:
        verify_prs = Presentation(output_file)
        num_slides = len(verify_prs.slides)
        print(f"[OK] Step 3 complete: {num_slides} slides generated")
        return output_file
    except Exception as e:
        print(f"[WARNING] Could not verify output file: {e}")
        return output_file


def main():
    """Main execution function."""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python generate_ppt_from_pdf.py <pdf_file> [--no-answers]")
        print("Example: python generate_ppt_from_pdf.py \"Adobe-Scan-03-Nov-2025.pdf\"")
        print("Example: python generate_ppt_from_pdf.py \"Adobe-Scan-03-Nov-2025.pdf\" --no-answers")
        print("\nOptions:")
        print("  --no-answers    Exclude answer slides from the presentation")
        print("\nNote: PDF file can be in current directory or provide full/relative path")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Check for --no-answers flag
    include_answers = True
    if len(sys.argv) > 2 and '--no-answers' in sys.argv:
        include_answers = False
        print("[INFO] Answer slides will be excluded from the presentation")
    
    # Check if PDF exists (try current directory first, then as-is)
    if not Path(pdf_path).exists():
        # Try in current directory
        pdf_in_current = Path(".") / pdf_path
        if pdf_in_current.exists():
            pdf_path = str(pdf_in_current)
        else:
            print(f"[ERROR] PDF file not found: {pdf_path}")
            print("[INFO] Make sure the PDF is in the current directory or provide full path")
            sys.exit(1)
    
    print("=" * 60)
    print("INTEGRATED PPT GENERATION FROM PDF")
    print("=" * 60)
    print(f"Input PDF: {pdf_path}")
    print(f"Working directory: {Path.cwd()}")
    print()
    
    # Step 1: Extract PDF content
    success, pdf_name, extracted_text = run_step1(pdf_path)
    if not success:
        print("\n[ERROR] Step 1 failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Parse questions
    success, questions = run_step2(pdf_name)
    if not success:
        print("\n[ERROR] Step 2 failed. Exiting.")
        sys.exit(1)
    
    # Step 3: Generate PPTX
    output_file = run_step3(pdf_name, include_answers=include_answers)
    if not output_file:
        print("\n[ERROR] Step 3 failed. Exiting.")
        sys.exit(1)
    
    # Count actual slides generated (excluding answers if needed)
    if include_answers:
        total_slides = sum(len(q.get('slides', [])) for q in questions)
    else:
        total_slides = 0
        for q in questions:
            for slide in q.get('slides', []):
                if slide.get('slide_type') != 'answer':
                    total_slides += 1
    
    # Final summary
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE!")
    print("=" * 60)
    print(f"Input PDF: {pdf_path}")
    print(f"Output PPTX: {output_file}")
    print(f"Total questions: {len(questions)}")
    print(f"Total slides: {total_slides}")
    if not include_answers:
        print(f"Note: Answer slides were excluded")
    print(f"\n[SUCCESS] Presentation generated successfully!")
    print(f"[INFO] Open {output_file} to review the results")


if __name__ == '__main__':
    main()
