"""
Step 2: Question Parsing & Slide Structuring
Parse extracted PDF content into structured question objects for PowerPoint slides.

This step:
1. Reads extracted content from Step 1
2. Uses LLM to parse and structure questions
3. Creates slide-ready objects with proper organization
4. Handles multi-part questions, passage-based questions, tables, and diagrams
"""
from anthropic import Anthropic  # Import Anthropic SDK for Claude API
from pathlib import Path  # For file path operations
import json  # For JSON parsing and saving
import sys  # For system operations
import yaml  # For reading config file
import re  # For regular expressions (exam info extraction)


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


def load_extracted_content(content_file: str) -> str:
    """
    Load extracted PDF content from Step 1 output file.
    
    Args:
        content_file: Path to extracted content file
        
    Returns:
        Content as string, or None if file not found
    """
    try:
        # Read the extracted content file
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove the header lines (=== separator and title)
        # Find where actual content starts (after "EXTRACTED PDF CONTENT (via LLM)")
        lines = content.split('\n')
        # Skip header lines until we find the actual content
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('='):
                start_idx = i
                break
        
        # Return content starting from actual text
        return '\n'.join(lines[start_idx:])
    
    except FileNotFoundError:
        print(f"[ERROR] File not found: {content_file}")
        print("[INFO] Please run Step 1 first to extract PDF content")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to read content file: {e}")
        return None


def extract_exam_info_from_content(content: str) -> str:
    """
    Extract exam information from content if present.
    
    Args:
        content: Extracted PDF content text
        
    Returns:
        Exam info string (e.g., "[CBSE 2023 (57/1/1)]") or empty string if not found
    """
    # Look for "EXAM_INFO: [info]" pattern at the beginning
    lines = content.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        if line.strip().startswith('EXAM_INFO:'):
            exam_info = line.strip().replace('EXAM_INFO:', '').strip()
            # Validate it looks like exam info (contains brackets or exam name)
            if exam_info and (exam_info.startswith('[') or 'CBSE' in exam_info.upper() or 'exam' in exam_info.lower() or 'sample' in exam_info.lower()):
                return exam_info
    
    # Also check for exam info patterns in content (e.g., "[CBSE 2023 (57/1/1)]")
    # Look for patterns like [CBSE ...], [Exam ...], etc.
    exam_pattern = r'\[(?:CBSE|Exam|Sample|Question Paper|Delhi).*?\]'
    matches = re.findall(exam_pattern, content[:500], re.IGNORECASE)  # Check first 500 chars
    if matches:
        # Return the first match found
        return matches[0] if matches[0].startswith('[') else f"[{matches[0]}]"
    
    # Also check for patterns without brackets
    exam_pattern_no_brackets = r'(?:CBSE|Exam|Sample|Question Paper).*?(?:20\d{2}|19\d{2}).*?(?:\(.*?\)|\[.*?\])?'
    matches_no_brackets = re.findall(exam_pattern_no_brackets, content[:500], re.IGNORECASE)
    if matches_no_brackets:
        exam_text = matches_no_brackets[0].strip()
        if not exam_text.startswith('['):
            return f"[{exam_text}]"
        return exam_text
    
    return ""


def parse_questions_with_llm(content: str, api_key: str, extract_year: bool = False) -> list:
    """
    Parse extracted content into structured question objects using Claude API.
    
    Args:
        content: Extracted PDF content text
        api_key: Anthropic API key
        extract_year: Whether to extract and include exam information (default: False)
        
    Returns:
        List of question dictionaries, or None if parsing fails
    """
    print("[INFO] Sending content to Claude API for parsing...")
    print("[INFO] This may take 30-60 seconds...")
    
    # Extract exam info if enabled
    exam_info = ""
    if extract_year:
        exam_info = extract_exam_info_from_content(content)
        if exam_info:
            print(f"[INFO] Extracted exam info: {exam_info}")
    
    try:
        # Initialize Anthropic client
        client = Anthropic(api_key=api_key)
        
        # Build parsing prompt
        prompt = """Parse the following extracted PDF content and structure it for PowerPoint slides.

Rules:
1. Ignore question numbers from PDF - number sequentially as Q1, Q2, Q3... based on order they appear
2. Maintain the exact order as questions appear in PDF
3. For each question, create slide objects:
   - Question slide: Contains question text (all parts if multi-part), options (if any), structured table data (if any), diagram description in brackets [description] (if any)
   - Answer slide: Contains answer (if provided) - comes AFTER question slide
4. Passage-based questions: 
   - Passage gets its own slide BEFORE questions
   - Then question slide(s) follow
   - Then answer slide(s) follow
5. Multi-part questions: Keep all parts (i), (ii), etc. together on same question slide
6. Tables: Parse into structured format with "headers" array and "rows" array (each row is an array)
7. Diagrams: Extract description and wrap in brackets [description] for manual addition later
8. Multiple choice options: Keep as array of strings like ["a) option1", "b) option2", ...]"""
        
        # Add exam info to JSON structure if enabled
        if extract_year and exam_info:
            prompt += f"""
9. Exam information: If exam info "{exam_info}" was found in the content, include it in the "exam_info" field for all questions."""
        
        prompt += """

Return ONLY valid JSON array with this structure:"""
        
        # Build JSON structure
        json_structure = """[
  {
    "question_number": "Q1",
    "question_type": "regular" | "multi_part" | "multiple_choice" | "passage_based","""
        
        if extract_year and exam_info:
            json_structure += f'''
    "exam_info": "{exam_info}",'''
        
        json_structure += """
    "slides": [
      {
        "slide_type": "question" | "answer" | "passage",
        "content": {
          "question_text": "...",
          "options": ["a) ...", "b) ..."] or [],
          "table": {"headers": [...], "rows": [[...], [...]]} or null,
          "diagram_description": "[description]" or null,
          "passage": "..." or null
        }
      },
      {
        "slide_type": "answer",
        "content": {
          "answer_text": "..."
        }
      }
    ]
  }
]"""
        
        prompt += json_structure + """

Extracted Content:
""" + content
        
        # Call Claude API with streaming for long requests
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",  # Claude model version
            max_tokens=32000,  # Maximum response length (increased for larger PDFs)
            messages=[{
                "role": "user",  # User message
                "content": prompt  # Parsing instructions + content
            }],
            stream=True  # Enable streaming for long requests
        )
        
        # Collect streaming response
        response_text = ""
        for event in response:
            if event.type == "content_block_delta":
                if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                    response_text += event.delta.text
        
        # Try to extract JSON from response (might have markdown code blocks)
        json_text = response_text
        
        # Remove markdown code blocks if present
        if "```json" in json_text:
            # Extract JSON from markdown code block
            start = json_text.find("```json") + 7
            end = json_text.find("```", start)
            json_text = json_text[start:end].strip()
        elif "```" in json_text:
            # Extract JSON from generic code block
            start = json_text.find("```") + 3
            end = json_text.find("```", start)
            json_text = json_text[start:end].strip()
        
        # Parse JSON
        questions = json.loads(json_text)
        
        # Add exam_info to all questions if extracted and not already present
        if extract_year and exam_info:
            for q in questions:
                if 'exam_info' not in q:
                    q['exam_info'] = exam_info
        
        print("[OK] Questions parsed successfully")
        if extract_year and exam_info:
            print(f"[INFO] Exam info {exam_info} included in all questions")
        return questions
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON response: {e}")
        print("[INFO] Response preview:")
        print(response_text[:500])
        return None
    except Exception as e:
        print(f"[ERROR] LLM parsing failed: {e}")
        return None


def validate_questions(questions: list) -> tuple:
    """
    Validate parsed questions structure.
    
    Args:
        questions: List of question dictionaries
        
    Returns:
        Tuple of (is_valid: bool, issues: list, stats: dict)
    """
    issues = []  # List to store validation issues
    stats = {  # Statistics dictionary
        'total_questions': len(questions),
        'total_slides': 0,
        'questions_with_answers': 0,
        'questions_with_options': 0,
        'questions_with_tables': 0,
        'questions_with_diagrams': 0,
        'passage_based': 0
    }
    
    # Validate each question
    for i, q in enumerate(questions):
        # Check required fields
        if 'question_number' not in q:
            issues.append(f"Question {i+1}: Missing question_number")
        if 'question_type' not in q:
            issues.append(f"Question {i+1}: Missing question_type")
        if 'slides' not in q:
            issues.append(f"Question {i+1}: Missing slides")
            continue
        
        # Count slides for this question
        stats['total_slides'] += len(q['slides'])
        
        # Check slide structure
        has_answer = False
        has_options = False
        has_table = False
        has_diagram = False
        
        for slide in q['slides']:
            if slide.get('slide_type') == 'answer':
                has_answer = True
                stats['questions_with_answers'] += 1
            
            content = slide.get('content', {})
            
            # Check for options
            if content.get('options') and len(content['options']) > 0:
                has_options = True
            
            # Check for table
            if content.get('table') and content['table'] is not None:
                has_table = True
            
            # Check for diagram
            if content.get('diagram_description') and content['diagram_description']:
                has_diagram = True
        
        if has_options:
            stats['questions_with_options'] += 1
        if has_table:
            stats['questions_with_tables'] += 1
        if has_diagram:
            stats['questions_with_diagrams'] += 1
        if q.get('question_type') == 'passage_based':
            stats['passage_based'] += 1
    
    is_valid = len(issues) == 0
    return is_valid, issues, stats


def save_parsed_questions(questions: list, output_file: str):
    """
    Save parsed questions to JSON file.
    
    Args:
        questions: List of question dictionaries
        output_file: Path to output JSON file
    """
    # Create output directory if it doesn't exist
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Save as formatted JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Parsed questions saved to: {output_file}")


def create_preview(questions: list, preview_file: str):
    """
    Create human-readable preview of parsed questions.
    
    Args:
        questions: List of question dictionaries
        preview_file: Path to preview text file
    """
    # Create output directory if it doesn't exist
    Path(preview_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("PARSED QUESTIONS PREVIEW\n")
        f.write("=" * 60 + "\n\n")
        
        # Write each question
        for q in questions:
            q_num = q.get('question_number', 'Unknown')
            q_type = q.get('question_type', 'unknown')
            exam_info = q.get('exam_info', '')
            
            exam_str = f"\n  Exam: {exam_info}" if exam_info else ""
            f.write(f"\n{q_num} ({q_type.upper()}){exam_str}\n")
            f.write("-" * 60 + "\n")
            
            # Write slides
            for slide_idx, slide in enumerate(q.get('slides', []), 1):
                slide_type = slide.get('slide_type', 'unknown')
                f.write(f"\n  Slide {slide_idx}: {slide_type.upper()}\n")
                
                content = slide.get('content', {})
                
                if slide_type == 'passage':
                    # Write passage
                    passage = content.get('passage', '')
                    f.write(f"    Passage: {passage[:200]}...\n" if len(passage) > 200 else f"    Passage: {passage}\n")
                
                elif slide_type == 'question':
                    # Write question text
                    q_text = content.get('question_text', '')
                    f.write(f"    Question: {q_text[:150]}...\n" if len(q_text) > 150 else f"    Question: {q_text}\n")
                    
                    # Write options if present
                    options = content.get('options', [])
                    if options:
                        f.write(f"    Options: {len(options)} options\n")
                        for opt in options[:2]:  # Show first 2
                            f.write(f"      - {opt[:80]}...\n" if len(opt) > 80 else f"      - {opt}\n")
                    
                    # Write table info if present
                    table = content.get('table')
                    if table:
                        headers = table.get('headers', [])
                        rows = table.get('rows', [])
                        f.write(f"    Table: {len(headers)} columns, {len(rows)} rows\n")
                    
                    # Write diagram info if present
                    diagram = content.get('diagram_description')
                    if diagram:
                        f.write(f"    Diagram: {diagram[:100]}...\n" if len(diagram) > 100 else f"    Diagram: {diagram}\n")
                
                elif slide_type == 'answer':
                    # Write answer
                    answer = content.get('answer_text', '')
                    f.write(f"    Answer: {answer[:150]}...\n" if len(answer) > 150 else f"    Answer: {answer}\n")
            
            f.write("\n")
    
    print(f"[OK] Preview saved to: {preview_file}")


def parse_questions_with_llm_offset(content: str, api_key: str, start_question_number: int = 1, extract_year: bool = False) -> list:
    """
    Parse extracted content into structured question objects using Claude API
    with offset question numbering.
    
    Args:
        content: Extracted PDF content text
        api_key: Anthropic API key
        start_question_number: Starting question number (default: 1)
        extract_year: Whether to extract and include exam information (default: False)
        
    Returns:
        List of question dictionaries, or None if parsing fails
    """
    print(f"[INFO] Sending content to Claude API for parsing (starting from Q{start_question_number})...")
    print("[INFO] This may take 30-60 seconds...")
    
    # Extract exam info if enabled
    exam_info = ""
    if extract_year:
        exam_info = extract_exam_info_from_content(content)
        if exam_info:
            print(f"[INFO] Extracted exam info: {exam_info}")
    
    try:
        # Initialize Anthropic client
        client = Anthropic(api_key=api_key)
        
        # Build parsing prompt
        prompt = f"""Parse the following extracted PDF content and structure it for PowerPoint slides.

Rules:
1. Number questions sequentially starting from Q{start_question_number} (Q{start_question_number}, Q{start_question_number + 1}, Q{start_question_number + 2}...)
2. Ignore question numbers from PDF - use the sequential numbering starting from Q{start_question_number}
3. Maintain the exact order as questions appear in PDF
4. For each question, create slide objects:
   - Question slide: Contains question text (all parts if multi-part), options (if any), structured table data (if any), diagram description in brackets [description] (if any)
   - Answer slide: Contains answer (if provided) - comes AFTER question slide
5. Passage-based questions: 
   - Passage gets its own slide BEFORE questions
   - Then question slide(s) follow
   - Then answer slide(s) follow
6. Multi-part questions: Keep all parts (i), (ii), etc. together on same question slide
7. Tables: Parse into structured format with "headers" array and "rows" array (each row is an array)
8. Diagrams: Extract description and wrap in brackets [description] for manual addition later
9. Multiple choice options: Keep as array of strings like ["a) option1", "b) option2", ...]"""
        
        # Add exam info instruction if enabled
        if extract_year and exam_info:
            prompt += f"""
10. Exam information: If exam info "{exam_info}" was found in the content, include it in the "exam_info" field for all questions."""
        
        prompt += f"""

Return ONLY valid JSON array with this structure:
[
  {{
    "question_number": "Q{start_question_number}",
    "question_type": "regular" | "multi_part" | "multiple_choice" | "passage_based","""
        
        if extract_year and exam_info:
            prompt += f'''
    "exam_info": "{exam_info}",'''
        
        prompt += """
    "slides": [
      {{
        "slide_type": "question" | "answer" | "passage",
        "content": {{
          "question_text": "...",
          "options": ["a) ...", "b) ..."] or [],
          "table": {{"headers": [...], "rows": [[...], [...]]}} or null,
          "diagram_description": "[description]" or null,
          "passage": "..." or null
        }}
      }},
      {{
        "slide_type": "answer",
        "content": {{
          "answer_text": "..."
        }}
      }}
    ]
  }}
]

Extracted Content:
""" + content
        
        # Call Claude API with streaming for long requests
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",  # Claude model version
            max_tokens=32000,  # Maximum response length (increased for larger PDFs)
            messages=[{
                "role": "user",  # User message
                "content": prompt  # Parsing instructions + content
            }],
            stream=True  # Enable streaming for long requests
        )
        
        # Collect streaming response
        response_text = ""
        for event in response:
            if event.type == "content_block_delta":
                if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                    response_text += event.delta.text
        
        # Try to extract JSON from response (might have markdown code blocks)
        json_text = response_text
        
        # Remove markdown code blocks if present
        if "```json" in json_text:
            # Extract JSON from markdown code block
            start = json_text.find("```json") + 7
            end = json_text.find("```", start)
            json_text = json_text[start:end].strip()
        elif "```" in json_text:
            # Extract JSON from generic code block
            start = json_text.find("```") + 3
            end = json_text.find("```", start)
            json_text = json_text[start:end].strip()
        
        # Parse JSON
        questions = json.loads(json_text)
        
        # Add exam_info to all questions if extracted and not already present
        if extract_year and exam_info:
            for q in questions:
                if 'exam_info' not in q:
                    q['exam_info'] = exam_info
        
        print(f"[OK] Questions parsed successfully (starting from Q{start_question_number})")
        if extract_year and exam_info:
            print(f"[INFO] Exam info {exam_info} included in all questions")
        return questions
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON response: {e}")
        print("[INFO] Response preview:")
        print(response_text[:500])
        return None
    except Exception as e:
        print(f"[ERROR] LLM parsing failed: {e}")
        return None


def renumber_questions_sequential(questions: list, start_num: int) -> list:
    """
    Renumber questions sequentially starting from the given number.
    
    Args:
        questions: List of question dictionaries
        start_num: Starting question number (e.g., 1 for Q1, 21 for Q21)
        
    Returns:
        List of questions with updated question_number fields
    """
    for i, q in enumerate(questions):
        q['question_number'] = f"Q{start_num + i}"
    return questions


def parse_multiple_pdfs_content(pdf_contents: list[tuple[str, str]], api_key: str, start_question_number: int = 1, extract_year: bool = False) -> list:
    """
    Parse multiple PDF contents sequentially with continuous question numbering.
    
    Args:
        pdf_contents: List of (pdf_name, content) tuples
        api_key: Anthropic API key
        start_question_number: Starting question number for the first PDF (default: 1)
        extract_year: Whether to extract and include exam information (default: False)
        
    Returns:
        Combined list of all questions from all PDFs with sequential numbering
    """
    all_questions = []
    current_question_number = start_question_number
    
    print(f"[INFO] Processing {len(pdf_contents)} PDF content(s) sequentially...")
    print(f"[INFO] Questions will start from Q{start_question_number}")
    if extract_year:
        print(f"[INFO] Exam information extraction enabled")
    print()
    
    for i, (pdf_name, content) in enumerate(pdf_contents, 1):
        print(f"[INFO] Parsing PDF {i}/{len(pdf_contents)}: {pdf_name}")
        print(f"[INFO] Questions will start from Q{current_question_number}")
        
        # Parse questions with offset numbering
        questions = parse_questions_with_llm_offset(content, api_key, current_question_number, extract_year)
        
        if not questions:
            print(f"[ERROR] Failed to parse questions from PDF: {pdf_name}")
            raise RuntimeError(f"Failed to parse questions from PDF: {pdf_name}")
        
        # Add to combined list
        all_questions.extend(questions)
        
        # Update current question number for next PDF
        current_question_number += len(questions)
        
        print(f"[OK] Parsed {len(questions)} questions from {pdf_name} (Q{current_question_number - len(questions)} to Q{current_question_number - 1})")
        print()
    
    # Safety check: ensure numbering is sequential from the start number
    all_questions = renumber_questions_sequential(all_questions, start_question_number)
    
    print(f"[OK] Successfully parsed {len(all_questions)} questions from {len(pdf_contents)} PDF(s)")
    print(f"[INFO] Questions numbered from Q{start_question_number} to Q{start_question_number + len(all_questions) - 1}")
    
    return all_questions


if __name__ == '__main__':
    """
    Main execution block - runs when script is executed directly.
    """
    # Read PDF name from Step 1
    pdf_name = "Adobe-Scan-12-Dec-2025"  # default fallback
    pdf_name_file = Path("output/current_pdf_name.txt")
    if pdf_name_file.exists():
        with open(pdf_name_file, 'r', encoding='utf-8') as f:
            pdf_name = f.read().strip()
        print(f"[INFO] Using PDF name from Step 1: {pdf_name}")
    else:
        print(f"[INFO] Using default PDF name: {pdf_name}")
    
    # Input file from Step 1 (named after PDF)
    input_file = f"output/extracted_pdf_content_{pdf_name}.txt"
    
    # Print header
    print("=" * 60)
    print("STEP 2: QUESTION PARSING & SLIDE STRUCTURING")
    print("=" * 60)
    print()
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"[ERROR] Input file not found: {input_file}")
        print("[INFO] Please run Step 1 first to extract PDF content")
        sys.exit(1)
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("[ERROR] API key not found!")
        print("\nPlease provide API key in config.yaml")
        sys.exit(1)
    
    # Load extracted content
    print(f"[INFO] Loading extracted content from: {input_file}")
    content = load_extracted_content(input_file)
    
    if not content:
        print("[ERROR] Failed to load extracted content")
        sys.exit(1)
    
    print(f"[OK] Loaded {len(content):,} characters of content")
    
    # Parse questions using LLM
    questions = parse_questions_with_llm(content, api_key)
    
    if not questions:
        print("[ERROR] Failed to parse questions")
        sys.exit(1)
    
    # Validate parsed questions
    print("\n[INFO] Validating parsed questions...")
    is_valid, issues, stats = validate_questions(questions)
    
    if issues:
        print(f"[WARNING] Found {len(issues)} validation issues:")
        for issue in issues[:5]:  # Show first 5 issues
            print(f"  - {issue}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")
    else:
        print("[OK] All questions validated successfully")
    
    # Save parsed questions (named after PDF)
    output_file = f"output/parsed_questions_{pdf_name}.json"
    save_parsed_questions(questions, output_file)
    
    # Create preview (named after PDF)
    preview_file = f"output/parsed_questions_{pdf_name}_preview.txt"
    create_preview(questions, preview_file)
    
    # Print summary
    print(f"\n[SUMMARY]")
    print(f"Total questions parsed: {stats['total_questions']}")
    print(f"Total slides to generate: {stats['total_slides']}")
    print(f"Questions with answers: {stats['questions_with_answers']}")
    print(f"Questions with options: {stats['questions_with_options']}")
    print(f"Questions with tables: {stats['questions_with_tables']}")
    print(f"Questions with diagrams: {stats['questions_with_diagrams']}")
    print(f"Passage-based questions: {stats['passage_based']}")
    
    print(f"\n[REVIEW CHECKLIST]")
    print(f"Please review: {preview_file}")
    print("  [ ] Are all questions properly parsed?")
    print("  [ ] Are multi-part questions kept together?")
    print("  [ ] Are passage-based questions detected correctly?")
    print("  [ ] Are tables structured correctly?")
    print("  [ ] Are diagram descriptions in brackets [description]?")
    print("  [ ] Are answers on separate slides after questions?")
    print("\nOnce verified, we can proceed to Step 3: Template Analysis")


