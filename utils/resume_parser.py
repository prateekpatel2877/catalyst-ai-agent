import fitz  # PyMuPDF
from docx import Document
import os


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")
    return text.strip()


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        raise ValueError(f"Failed to read DOCX: {e}")
    return text.strip()


def parse_resume(uploaded_file) -> str:
    """
    Parse resume from Streamlit uploaded file object.
    Supports PDF and DOCX formats.
    """
    file_name = uploaded_file.name
    extension = os.path.splitext(file_name)[1].lower()

    # Save uploaded file temporarily
    temp_path = f"temp_resume{extension}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Extract text based on file type
    if extension == ".pdf":
        text = extract_text_from_pdf(temp_path)
    elif extension == ".docx":
        text = extract_text_from_docx(temp_path)
    else:
        os.remove(temp_path)
        raise ValueError("Unsupported file format. Please upload a PDF or DOCX file.")

    # Clean up temp file
    os.remove(temp_path)

    if not text:
        raise ValueError("Could not extract text from resume. File may be empty or image-based.")

    return text