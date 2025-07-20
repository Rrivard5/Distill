import streamlit as st
import fitz  # PyMuPDF
import anthropic
import textwrap
import os

from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image

# Claude prompt
PROMPT_TEMPLATE = """Please analyze the uploaded course evaluation PDF and extract feedback in the following format:

Instructions:
Extract TWO types of feedback:

Constructive Suggestions - Rewrite harsh or mean comments into professional, actionable feedback. Focus on the underlying educational concern rather than personal attacks.
Supportive Comments - Include positive, encouraging, or particularly kind student comments as direct quotes.

What to INCLUDE:
- Specific suggestions for course improvement
- Comments about teaching methods, materials, or organization
- Constructive criticism about pacing, clarity, or structure
- Requests for additional resources or support
- Positive feedback that highlights what works well
- Comments that show genuine engagement with the learning process

What to EXCLUDE:
- Personal attacks on the instructor's character
- Complaints without constructive suggestions
- Comments that are purely emotional venting
- Inappropriate or unprofessional language
- Repetitive complaints already captured elsewhere

Output Format:
Constructive Suggestions for Improvement:

[Suggestion theme] (mentioned by X students) - [Professional rewrite of the core concern]
[Another theme] (mentioned by X students) - [Actionable feedback]
[Individual unique suggestion] (mentioned by 1 student) - [Specific concern]

Supportive Student Comments:

"[Direct quote from positive feedback]"

"[Another encouraging comment]"

"[Specific praise that could be meaningful to instructor]"

Summary:
Most Common Concerns: List the top 3-4 themes that appeared most frequently
Key Strengths Highlighted: Main positive themes from supportive comments
Unique Suggestions: Any one-off suggestions that might be worth considering

PDF Text:
"""

# App title
st.set_page_config(page_title="Course Evaluation Analyzer", layout="wide")
st.title("📋 Course Evaluation Analyzer with Claude")

# Claude API key
api_key = os.getenv("ANTHROPIC_API_KEY") or st.text_input("Enter your Claude API key", type="password")
uploaded_file = st.file_uploader("Upload a Course Evaluation PDF", type="pdf")

def ocr_from_pdf(file_bytes):
    images = convert_from_bytes(file_bytes)
    text = ""
    for i, img in enumerate(images):
        st.write(f"🔍 Running OCR on page {i+1}")
        text += pytesseract.image_to_string(img)
    return text

if uploaded_file and api_key:
    st.info("Processing PDF...")

    try:
        # Try extracting text with PyMuPDF
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()

        if not full_text.strip():
            st.warning("⚠️ No text extracted with PyMuPDF. Trying OCR (image-based PDF).")
            uploaded_file.seek(0)
            full_text = ocr_from_pdf(uploaded_file.read())

        # Show preview
        st.subheader("📝 Preview of Extracted Text")
        st.text_area("First 3000 characters:", full_text[:3000])

        if not full_text.strip():
            st.error("❌ Still couldn't extract text. PD
