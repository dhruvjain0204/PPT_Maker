"""
Streamlit Web Application for PPT Generator
User-friendly web interface for generating PowerPoint presentations from PDF files.
"""
import streamlit as st
from pathlib import Path
import tempfile
import os
import time
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
    save_parsed_questions
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


def process_pdf(pdf_path: str, include_answers: bool = True, progress_container=None):
    """
    Process PDF through all three steps and generate PPTX.
    
    Args:
        pdf_path: Path to PDF file
        include_answers: Whether to include answer slides
        progress_container: Streamlit container for progress updates
        
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
    
    extracted_text = extract_with_llm(pdf_path, api_key)
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
    
    questions = parse_questions_with_llm(content, api_key)
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
    generator.generate(questions, str(output_pptx), include_answers=include_answers)
    
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
        
        if file_size_mb > 10:
            st.warning("⚠️ Large file detected. Processing may take longer.")
    
    # Options section
    st.header("⚙️ Options")
    include_answers = st.checkbox(
        "Include answer slides",
        value=True,
        help="If checked, answer slides will be included in the presentation. Uncheck to generate only question slides."
    )
    
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
                
                # Create progress container
                progress_container = st.container()
                
                # Process PDF
                success, output_file, stats = process_pdf(
                    pdf_path,
                    include_answers=include_answers,
                    progress_container=progress_container
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

