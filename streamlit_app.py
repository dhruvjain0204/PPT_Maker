"""
Streamlit Web Application for PPT Generator
User-friendly web interface for generating PowerPoint presentations from PDF files.
"""
import streamlit as st
from pathlib import Path
import tempfile
import os
import time
from PyPDF2 import PdfReader
from step1_pdf_extraction import (
    get_api_key as get_api_key_step1,
    extract_with_llm,
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


# Page configuration
st.set_page_config(
    page_title="PPT Generator from PDF",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">📊 PPT Generator from PDF</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    **Convert PDF question papers into PowerPoint presentations automatically!**
    
    This tool:
    - Extracts questions from PDF files
    - Structures them into slides
    - Generates ready-to-use PPTX files
    
    **How it works:**
    1. Upload your PDF file
    2. Choose options (include/exclude answers)
    3. Wait for processing (1-2 minutes)
    4. Download your PowerPoint!
    """)
    
    st.markdown("---")
    st.markdown("**Note:** Processing may take 30-60 seconds per step. Please be patient!")


def get_api_key_from_secrets():
    """
    Get API key from Streamlit secrets or fallback to existing methods.
    
    Returns:
        API key string, or None if not found
    """
    try:
        # Try Streamlit secrets first (for Streamlit Cloud)
        if hasattr(st, 'secrets') and 'anthropic' in st.secrets:
            api_key = st.secrets['anthropic']['api_key']
            if api_key:
                return api_key
    except:
        pass
    
    # Fallback to existing methods (config.yaml or environment variable)
    api_key = get_api_key_step1()
    return api_key if api_key else None


def save_uploaded_file(uploaded_file, temp_dir):
    """
    Save uploaded PDF file to temporary directory.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        temp_dir: Temporary directory path
        
    Returns:
        Path to saved file, or None if error
    """
    try:
        file_path = Path(temp_dir) / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return str(file_path)
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None


def cleanup_temp_files(temp_dir):
    """
    Clean up temporary files and directory.
    
    Args:
        temp_dir: Temporary directory path
    """
    try:
        import shutil
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
    except Exception as e:
        st.warning(f"Could not clean up temporary files: {e}")


def process_multiple_pdfs_streamlit(pdf_paths: list[str], include_answers: bool = True, start_question_number: int = 1, extract_year: bool = False):
    """Process multiple PDFs in Streamlit with progress updates."""
    from generate_ppt_from_multiple_pdfs import (
        run_step1_multiple,
        run_step2_multiple,
        run_step3_multiple,
        save_parsed_questions,
        create_preview
    )
    
    progress_container = st.container()
    
    # Step 1
    with progress_container.status("📄 **Step 1: Extracting content from PDFs...**", state="running"):
        progress_container.write(f"Processing {len(pdf_paths)} PDF chunk(s)...")
        success, first_pdf_name, combined_text, pdf_contents = run_step1_multiple(pdf_paths, extract_year)
        if not success:
            progress_container.error("❌ Step 1 failed")
            return
        progress_container.success(f"✅ Step 1 complete: {len(combined_text):,} characters extracted")
    
    # Step 2
    with progress_container.status("🔍 **Step 2: Parsing questions...**", state="running"):
        success, questions = run_step2_multiple(pdf_contents, start_question_number, extract_year)
        if not success:
            progress_container.error("❌ Step 2 failed")
            return
        
        # Save parsed questions
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        questions_file = output_dir / f"parsed_questions_{first_pdf_name}.json"
        save_parsed_questions(questions, str(questions_file))
        
        preview_file = output_dir / f"parsed_questions_{first_pdf_name}_preview.txt"
        create_preview(questions, str(preview_file))
        
        progress_container.success(f"✅ Step 2 complete: {len(questions)} questions parsed")
    
    # Step 3
    with progress_container.status("📊 **Step 3: Generating PowerPoint...**", state="running"):
        output_file = run_step3_multiple(first_pdf_name, questions, include_answers=include_answers)
        if not output_file:
            progress_container.error("❌ Step 3 failed")
            return
        progress_container.success(f"✅ Step 3 complete")
    
    # Show results
    st.markdown("---")
    st.header("✅ Generation Complete!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Questions", len(questions))
    with col2:
        total_slides = sum(len(q.get('slides', [])) for q in questions) if include_answers else sum(
            1 for q in questions for slide in q.get('slides', []) if slide.get('slide_type') != 'answer'
        )
        st.metric("Slides", total_slides)
    with col3:
        answer_status = "Included" if include_answers else "Excluded"
        st.metric("Answer Slides", answer_status)
    
    # Download button
    with open(output_file, "rb") as f:
        pptx_bytes = f.read()
    
    st.download_button(
        label="📥 Download PowerPoint",
        data=pptx_bytes,
        file_name=Path(output_file).name,
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        type="primary",
        use_container_width=True
    )
    
    st.success(f"🎉 Your presentation is ready! Click the button above to download.")


def process_pdf(pdf_path: str, include_answers: bool = True, progress_container=None, start_question_number: int = 1, extract_year: bool = False):
    """
    Process PDF through all three steps and generate PPTX.
    
    Args:
        pdf_path: Path to PDF file
        include_answers: Whether to include answer slides
        progress_container: Streamlit container for progress updates
        start_question_number: Starting question number (default: 1)
        extract_year: Whether to extract exam information (default: False)
        
    Returns:
        Tuple of (success: bool, output_file: str, stats: dict)
    """
    stats = {
        'questions': 0,
        'slides': 0,
        'pdf_name': Path(pdf_path).stem
    }
    
    # Get API key
    api_key = get_api_key_from_secrets()
    if not api_key:
        if progress_container:
            progress_container.error("❌ API key not found! Please configure your API key in Streamlit secrets or config.yaml")
        return False, None, stats
    
    # Step 1: PDF Extraction
    if progress_container:
        with progress_container.status("📄 **Step 1: Extracting content from PDF...**", state="running"):
            progress_container.write("Sending PDF to Claude API... This may take 30-60 seconds.")
    
    extracted_text = extract_with_llm(pdf_path, api_key, extract_year)
    if not extracted_text:
        if progress_container:
            progress_container.error("❌ Failed to extract content from PDF")
        return False, None, stats
    
    # Save extracted text
    pdf_name = Path(pdf_path).stem
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"extracted_pdf_content_{pdf_name}.txt"
    save_extracted_text(extracted_text, str(output_file))
    
    # Save PDF name for next steps
    pdf_name_file = output_dir / "current_pdf_name.txt"
    with open(pdf_name_file, 'w', encoding='utf-8') as f:
        f.write(pdf_name)
    
    if progress_container:
        progress_container.success(f"✅ Step 1 complete: {len(extracted_text):,} characters extracted")
    
    # Step 2: Question Parsing
    if progress_container:
        with progress_container.status("🔍 **Step 2: Parsing questions...**", state="running"):
            progress_container.write("Analyzing content and structuring questions... This may take 30-60 seconds.")
    
    content = load_extracted_content(str(output_file))
    if not content:
        if progress_container:
            progress_container.error("❌ Failed to load extracted content")
        return False, None, stats
    
    questions = parse_questions_with_llm(content, api_key, extract_year)
    if not questions:
        if progress_container:
            progress_container.error("❌ Failed to parse questions")
        return False, None, stats
    
    # Validate questions
    is_valid, issues, validation_stats = validate_questions(questions)
    
    # Save parsed questions
    parsed_file = output_dir / f"parsed_questions_{pdf_name}.json"
    save_parsed_questions(questions, str(parsed_file))
    
    stats['questions'] = validation_stats['total_questions']
    stats['slides'] = validation_stats['total_slides'] if include_answers else sum(
        1 for q in questions for slide in q.get('slides', []) if slide.get('slide_type') != 'answer'
    )
    
    if progress_container:
        if issues:
            progress_container.warning(f"⚠️ Step 2 complete with {len(issues)} validation issues")
        else:
            progress_container.success(f"✅ Step 2 complete: {stats['questions']} questions, {stats['slides']} slides")
    
    # Step 3: PPTX Generation
    if progress_container:
        with progress_container.status("📊 **Step 3: Generating PowerPoint...**", state="running"):
            progress_container.write("Creating presentation slides...")
    
    # Get unique output filename
    ppt_dir = Path("PPTs")
    ppt_dir.mkdir(exist_ok=True)
    output_pptx = ppt_dir / f"{pdf_name}.pptx"
    
    # Handle existing files
    counter = 1
    while output_pptx.exists():
        output_pptx = ppt_dir / f"{pdf_name}_{counter}.pptx"
        counter += 1
    
    # Generate PPTX
    generator = PPTXGenerator()
    generator.generate(questions, str(output_pptx), include_answers=include_answers, start_question_number=start_question_number)
    
    # Verify output
    try:
        verify_prs = Presentation(str(output_pptx))
        num_slides = len(verify_prs.slides)
        stats['slides'] = num_slides
        
        if progress_container:
            progress_container.success(f"✅ Step 3 complete: {num_slides} slides generated")
        
        return True, str(output_pptx), stats
    except Exception as e:
        if progress_container:
            progress_container.warning(f"⚠️ Generated file but could not verify: {e}")
        return True, str(output_pptx), stats


# Main app
def main():
    # File upload section
    st.header("📁 Upload PDF File")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF file containing questions. The file will be processed to extract questions and generate a PowerPoint presentation."
    )
    
    if uploaded_file:
        # Show file info
        file_size_mb = len(uploaded_file.getbuffer()) / (1024 * 1024)
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**File:** {uploaded_file.name}")
        with col2:
            st.info(f"**Size:** {file_size_mb:.2f} MB")
        
        # Get page count
        total_pages = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_path = tmp_file.name
                reader = PdfReader(tmp_path)
                total_pages = len(reader.pages)
                os.unlink(tmp_path)
                
                st.info(f"**Pages:** {total_pages}")
                if total_pages > 50:
                    st.warning("⚠️ Large PDF detected. Consider using split feature for better results.")
        except Exception as e:
            st.warning(f"Could not read PDF page count: {e}")
            # Set total_pages to a default value so split input can still appear
            total_pages = 999  # Large default to allow any reasonable split
        
        if file_size_mb > 10:
            st.warning("⚠️ Large file detected. Processing may take longer.")
    
    # Options section
    st.header("⚙️ Options")
    
    col1, col2 = st.columns(2)
    with col1:
        include_answers = st.checkbox(
            "Include answer slides",
            value=True,
            help="If checked, answer slides will be included in the presentation."
        )
    
    with col2:
        start_number = st.number_input(
            "Start question number",
            min_value=1,
            value=1,
            help="Starting number for question numbering (e.g., 1 for Q1, 21 for Q21)"
        )
    
    col3, col4 = st.columns(2)
    with col3:
        extract_year = st.checkbox(
            "Extract exam information",
            value=False,
            help="Enable this to extract and display exam information from previous year question papers (e.g., [CBSE 2023 (57/1/1)], [CBSE Delhi 2015 [HOTS]])"
        )
    
    # PDF Splitting section
    st.header("✂️ PDF Splitting (for large files)")
    use_split = st.checkbox(
        "Split PDF into chunks",
        value=False,
        help="Enable this for large PDFs (>50 pages) to avoid connection timeouts. Specify page numbers where to split (comma-separated, e.g., 20,40,60)."
    )
    
    split_pages = None
    if use_split and uploaded_file:
        # Show input even if total_pages couldn't be determined
        if total_pages:
            st.info(f"💡 **Tip:** Split at page numbers where questions end (not in the middle of a question). PDF has {total_pages} pages.")
        else:
            st.info("💡 **Tip:** Split at page numbers where questions end (not in the middle of a question).")
        
        split_input = st.text_input(
            "Split at pages (comma-separated)",
            placeholder="e.g., 20, 40, 60",
            help="Enter page numbers where to split the PDF, separated by commas. You can specify multiple split points. Example: 20,40,60 will split at pages 20, 40, and 60."
        )
        
        if split_input:
            try:
                # Parse comma-separated page numbers
                split_pages = [int(x.strip()) for x in split_input.split(',') if x.strip()]
                
                if not split_pages:
                    st.error("❌ Please enter at least one page number.")
                    split_pages = None
                else:
                    # Validate page numbers only if total_pages is known
                    if total_pages and total_pages < 999:  # Only validate if we have real page count
                        invalid_pages = [p for p in split_pages if p < 1 or p > total_pages]
                        if invalid_pages:
                            st.error(f"❌ Invalid page numbers: {invalid_pages}. PDF has {total_pages} pages.")
                            split_pages = None
                        else:
                            st.success(f"✅ Will split at pages: {sorted(split_pages)}")
                    else:
                        # If total_pages unknown, just validate they're positive numbers
                        invalid_pages = [p for p in split_pages if p < 1]
                        if invalid_pages:
                            st.error(f"❌ Invalid page numbers: {invalid_pages}. Please enter positive numbers.")
                            split_pages = None
                        else:
                            st.success(f"✅ Will split at pages: {sorted(split_pages)}")
            except ValueError:
                st.error("❌ Please enter valid page numbers separated by commas (e.g., 20,40,60)")
                split_pages = None
    
    # Process button
    st.markdown("---")
    
    if uploaded_file:
        if st.button("🚀 Generate PPT", type="primary", use_container_width=True):
            # Create temporary directory for uploaded file
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save uploaded file
                pdf_path = save_uploaded_file(uploaded_file, temp_dir)
                if not pdf_path:
                    st.error("Failed to save uploaded file. Please try again.")
                    return
                
                # Handle PDF splitting if enabled
                if use_split and split_pages:
                    try:
                        from step1_pdf_extraction import split_pdf_at_pages
                        
                        with st.status("✂️ **Splitting PDF...**", state="running") as status:
                            status.write(f"Splitting PDF at pages: {split_pages}")
                            split_files = split_pdf_at_pages(pdf_path, split_pages)
                            
                            if not split_files or len(split_files) == 0:
                                st.error("❌ Failed to split PDF. Please check your split page numbers.")
                                return
                            
                            status.write(f"✅ Created {len(split_files)} chunks")
                            status.update(state="complete")
                        
                        # Process using multi-PDF workflow
                        process_multiple_pdfs_streamlit(
                            split_files,
                            include_answers=include_answers,
                            start_question_number=int(start_number),
                            extract_year=extract_year
                        )
                    except Exception as e:
                        st.error(f"❌ Error during PDF splitting: {e}")
                        st.exception(e)
                else:
                    # Normal single PDF processing
                    # Create progress container
                    progress_container = st.container()
                    
                    # Process PDF
                    success, output_file, stats = process_pdf(
                        pdf_path,
                        include_answers=include_answers,
                        progress_container=progress_container,
                        start_question_number=int(start_number),
                        extract_year=extract_year
                    )
                
                if success and output_file:
                    st.markdown("---")
                    st.header("✅ Generation Complete!")
                    
                    # Show summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Questions", stats['questions'])
                    with col2:
                        st.metric("Slides", stats['slides'])
                    with col3:
                        answer_status = "Included" if include_answers else "Excluded"
                        st.metric("Answer Slides", answer_status)
                    
                    # Download button
                    with open(output_file, "rb") as f:
                        pptx_bytes = f.read()
                    
                    st.download_button(
                        label="📥 Download PowerPoint",
                        data=pptx_bytes,
                        file_name=Path(output_file).name,
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        type="primary",
                        use_container_width=True
                    )
                    
                    st.success(f"🎉 Your presentation is ready! Click the button above to download.")
                else:
                    st.error("❌ Failed to generate presentation. Please check the error messages above and try again.")
    else:
        st.info("👆 Please upload a PDF file to get started.")


if __name__ == "__main__":
    main()

