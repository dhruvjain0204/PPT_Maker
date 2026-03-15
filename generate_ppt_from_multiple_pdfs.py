"""
Integrated Script: Generate PPTX from Multiple PDFs
Combines all three steps into a single script with support for multiple PDFs:
1. PDF Content Extraction (Step 1) - processes each PDF sequentially
2. Question Parsing & Slide Structuring (Step 2) - processes each PDF's content sequentially with continuous numbering
3. PPTX Generation (Step 3)

Usage:
    python generate_ppt_from_multiple_pdfs.py "pdf1.pdf" "pdf2.pdf" "pdf3.pdf"
    python generate_ppt_from_multiple_pdfs.py "pdf1.pdf,pdf2.pdf,pdf3.pdf"
    python generate_ppt_from_multiple_pdfs.py "pdf1.pdf"  # Single PDF also works
"""
import sys
from pathlib import Path
from step1_pdf_extraction import (
    get_api_key as get_api_key_step1,
    extract_multiple_pdfs,
    analyze_content,
    save_extracted_text
)
from step2_question_parsing import (
    get_api_key as get_api_key_step2,
    parse_multiple_pdfs_content,
    validate_questions,
    save_parsed_questions,
    create_preview
)
from step3_pptx_new import PPTXGenerator, load_parsed_questions
from pptx import Presentation


def parse_pdf_arguments(args: list[str]) -> list[str]:
    """
    Parse command line arguments to extract PDF file paths.
    Supports both separate arguments and comma-separated strings.
    
    Args:
        args: Command line arguments (excluding script name)
        
    Returns:
        List of PDF file paths
    """
    pdf_paths = []
    
    for arg in args:
        # Skip flags
        if arg.startswith('--'):
            continue
        
        # Check if comma-separated
        if ',' in arg:
            # Split by comma and add each path
            paths = [p.strip() for p in arg.split(',')]
            pdf_paths.extend(paths)
        else:
            # Single path
            pdf_paths.append(arg)
    
    return pdf_paths


def run_step1_multiple(pdf_paths: list[str], extract_year: bool = False) -> tuple:
    """
    Run Step 1: PDF Content Extraction for multiple PDFs
    
    Args:
        pdf_paths: List of paths to PDF files
        extract_year: Whether to extract exam information (default: False)
        
    Returns:
        Tuple of (success: bool, first_pdf_name: str, combined_text: str, pdf_contents: list)
        where pdf_contents is list of (pdf_name, extracted_text) tuples
    """
    print("\n" + "=" * 60)
    print("STEP 1: PDF CONTENT EXTRACTION (MULTIPLE PDFS)")
    print("=" * 60)
    print()
    
    # Validate all PDFs exist
    validated_paths = []
    for pdf_path in pdf_paths:
        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            # Try in current directory
            pdf_in_current = Path(".") / pdf_path
            if pdf_in_current.exists():
                validated_paths.append(str(pdf_in_current))
            else:
                print(f"[ERROR] PDF file not found: {pdf_path}")
                return False, None, None, None
        else:
            validated_paths.append(pdf_path)
    
    # Get first PDF name for output naming
    first_pdf_name = Path(validated_paths[0]).stem
    print(f"[INFO] Processing {len(validated_paths)} PDF(s)")
    for i, path in enumerate(validated_paths, 1):
        print(f"  {i}. {Path(path).name}")
    if extract_year:
        print(f"[INFO] Exam information extraction enabled")
    print()
    
    # Get API key
    api_key = get_api_key_step1()
    if not api_key:
        print("[ERROR] API key not found!")
        print("\nPlease provide API key in config.yaml")
        return False, first_pdf_name, None, None
    
    # Extract text from all PDFs
    try:
        combined_text, pdf_contents = extract_multiple_pdfs(validated_paths, api_key, extract_year)
    except Exception as e:
        print(f"[ERROR] Step 1 failed: {e}")
        return False, first_pdf_name, None, None
    
    # Analyze combined content
    issues, good_signs = analyze_content(combined_text)
    
    # Save combined extracted text
    output_file = f"output/extracted_pdf_content_{first_pdf_name}.txt"
    save_extracted_text(combined_text, output_file)
    
    print(f"[OK] Step 1 complete: {len(combined_text):,} characters extracted from {len(pdf_paths)} PDF(s)")
    return True, first_pdf_name, combined_text, pdf_contents


def run_step2_multiple(pdf_contents: list[tuple[str, str]], start_question_number: int = 1, extract_year: bool = False) -> tuple:
    """
    Run Step 2: Question Parsing & Slide Structuring for multiple PDF contents
    
    Args:
        pdf_contents: List of (pdf_name, content) tuples from Step 1
        start_question_number: Starting question number for the first PDF (default: 1)
        extract_year: Whether to extract exam information (default: False)
        
    Returns:
        Tuple of (success: bool, questions: list)
    """
    print("\n" + "=" * 60)
    print("STEP 2: QUESTION PARSING & SLIDE STRUCTURING (MULTIPLE PDFS)")
    print("=" * 60)
    print()
    
    # Get API key
    api_key = get_api_key_step2()
    if not api_key:
        print("[ERROR] API key not found!")
        return False, None
    
    # Parse questions from all PDFs with sequential numbering
    try:
        questions = parse_multiple_pdfs_content(pdf_contents, api_key, start_question_number, extract_year)
    except Exception as e:
        print(f"[ERROR] Step 2 failed: {e}")
        return False, None
    
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


def run_step3_multiple(pdf_name: str, questions: list, include_answers: bool = True) -> str:
    """
    Run Step 3: PPTX Generation from combined questions
    
    Args:
        pdf_name: PDF name (without extension) for output naming
        questions: Combined list of questions from all PDFs
        include_answers: Whether to include answer slides (default: True)
        
    Returns:
        Output file path, or None if failed
    """
    print("\n" + "=" * 60)
    print("STEP 3: PPTX GENERATION")
    print("=" * 60)
    print()
    
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
        print("Usage: python generate_ppt_from_multiple_pdfs.py <pdf_file1> [pdf_file2] [pdf_file3] ... [--no-answers] [--start-from N] [--extract-exam-info]")
        print("   or: python generate_ppt_from_multiple_pdfs.py \"pdf1.pdf,pdf2.pdf,pdf3.pdf\" [--no-answers] [--start-from N] [--extract-exam-info]")
        print("\nExamples:")
        print("  python generate_ppt_from_multiple_pdfs.py \"pdf1.pdf\" \"pdf2.pdf\" \"pdf3.pdf\"")
        print("  python generate_ppt_from_multiple_pdfs.py \"pdf1.pdf,pdf2.pdf,pdf3.pdf\"")
        print("  python generate_ppt_from_multiple_pdfs.py \"pdf1.pdf\"  # Single PDF also works")
        print("  python generate_ppt_from_multiple_pdfs.py \"pdf1.pdf\" \"pdf2.pdf\" --start-from 20")
        print("  python generate_ppt_from_multiple_pdfs.py \"previous_year.pdf\" --extract-exam-info")
        print("  python generate_ppt_from_multiple_pdfs.py \"pdf1.pdf\" \"pdf2.pdf\" --no-answers --start-from 50 --extract-exam-info")
        print("\nOptions:")
        print("  --no-answers          Exclude answer slides from the presentation")
        print("  --start-from N        Start question numbering from QN (e.g., --start-from 20 starts from Q20)")
        print("  --extract-exam-info   Extract and display exam information from previous year question papers")
        print("                        (e.g., [CBSE 2023 (57/1/1)], [CBSE Delhi 2015 [HOTS]])")
        print("\nNote: PDF files can be in current directory or provide full/relative paths")
        sys.exit(1)
    
    # Parse flags FIRST to identify flag values that should be skipped
    include_answers = True
    start_question_number = 1
    extract_year = False
    skip_indices = set()  # Track indices to skip when parsing PDFs (1-based, excluding script name)
    
    # Check for --no-answers flag
    if '--no-answers' in sys.argv:
        idx = sys.argv.index('--no-answers')
        skip_indices.add(idx)  # Skip the flag itself
        include_answers = False
        print("[INFO] Answer slides will be excluded from the presentation")
    
    # Check for --extract-exam-info flag
    if '--extract-exam-info' in sys.argv:
        idx = sys.argv.index('--extract-exam-info')
        skip_indices.add(idx)  # Skip the flag itself
        extract_year = True
        print("[INFO] Exam information extraction enabled")
    
    # Check for --start-from flag
    if '--start-from' in sys.argv:
        try:
            idx = sys.argv.index('--start-from')
            skip_indices.add(idx)  # Skip the flag itself
            if idx + 1 < len(sys.argv):
                start_question_number = int(sys.argv[idx + 1])
                skip_indices.add(idx + 1)  # Skip the value too
                if start_question_number < 1:
                    print("[ERROR] Starting question number must be 1 or greater")
                    sys.exit(1)
                print(f"[INFO] Questions will start numbering from Q{start_question_number}")
            else:
                print("[ERROR] --start-from requires a number argument")
                sys.exit(1)
        except (ValueError, IndexError):
            print("[ERROR] Invalid --start-from argument. Please provide a number.")
            sys.exit(1)
    
    # Now parse PDF arguments, skipping flag indices (sys.argv indices are 0-based, we want to skip script name + flag indices)
    filtered_args = [arg for i, arg in enumerate(sys.argv[1:], 1) if i not in skip_indices]
    pdf_paths = parse_pdf_arguments(filtered_args)
    
    if not pdf_paths:
        print("[ERROR] No PDF files provided")
        sys.exit(1)
    
    print("=" * 60)
    print("INTEGRATED PPT GENERATION FROM MULTIPLE PDFS")
    print("=" * 60)
    print(f"Input PDFs: {len(pdf_paths)} file(s)")
    for i, path in enumerate(pdf_paths, 1):
        print(f"  {i}. {path}")
    print(f"Working directory: {Path.cwd()}")
    print()
    
    # Step 1: Extract PDF content from all PDFs
    success, first_pdf_name, combined_text, pdf_contents = run_step1_multiple(pdf_paths, extract_year)
    if not success:
        print("\n[ERROR] Step 1 failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Parse questions from all PDFs with sequential numbering
    success, questions = run_step2_multiple(pdf_contents, start_question_number, extract_year)
    if not success:
        print("\n[ERROR] Step 2 failed. Exiting.")
        sys.exit(1)
    
    # Save parsed questions and create preview
    questions_file = f"output/parsed_questions_{first_pdf_name}.json"
    save_parsed_questions(questions, questions_file)
    
    preview_file = f"output/parsed_questions_{first_pdf_name}_preview.txt"
    create_preview(questions, preview_file)
    
    # Step 3: Generate PPTX
    output_file = run_step3_multiple(first_pdf_name, questions, include_answers=include_answers)
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
    print(f"Input PDFs: {len(pdf_paths)} file(s)")
    for i, path in enumerate(pdf_paths, 1):
        print(f"  {i}. {Path(path).name}")
    print(f"Output PPTX: {output_file}")
    print(f"Total questions: {len(questions)}")
    print(f"Total slides: {total_slides}")
    if not include_answers:
        print(f"Note: Answer slides were excluded")
    print(f"\n[SUCCESS] Presentation generated successfully!")
    print(f"[INFO] Open {output_file} to review the results")


if __name__ == '__main__':
    main()

