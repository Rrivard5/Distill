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

# Page config
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
        # First try text-based extraction with PyMuPDF
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()

        # If PyMuPDF fails, fallback to OCR
        if not full_text.strip():
            st.warning("⚠️ No text extracted with PyMuPDF. Trying OCR (image-based PDF).")
            uploaded_file.seek(0)
            full_text = ocr_from_pdf(uploaded_file.read())

        # Show preview
        st.subheader("📝 Preview of Extracted Text")
        st.text_area("First 3000 characters:", full_text[:3000])

        if not full_text.strip():
            st.error("❌ Still couldn't extract text. PDF might be too low resolution for OCR.")
        else:
            # Chunk and send to Claude
            chunk_size = 12000
            chunks = textwrap.wrap(full_text, chunk_size)
            client = anthropic.Anthropic(api_key=api_key)
            results = []

            for i, chunk in enumerate(chunks):
                st.write(f"⏳ Sending chunk {i+1} of {len(chunks)} to Claude...")

                try:
                    message = client.messages.create(
                        model="claude-3-opus-20240229",
                        max_tokens=2048,
                        temperature=0.3,
                        messages=[{"role": "user", "content": PROMPT_TEMPLATE + chunk}]
                    )

                    result_text = message.content[0].text.strip()
                    st.subheader(f"🧠 Claude Output for Chunk {i+1}")
                    st.markdown(result_text)
                    results.append(result_text)

                except Exception as e:
                    st.error(f"Claude API error: {e}")
                    break

            st.success("✅ All chunks processed!")

    except Exception as e:
        st.error(f"Error during processing: {e}")
