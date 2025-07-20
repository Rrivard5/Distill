import streamlit as st
import fitz  # PyMuPDF
import anthropic
import textwrap
import os

PROMPT_TEMPLATE = """Please analyze the uploaded course evaluation PDF and extract feedback in the following format:
[...insert your prompt here...]
PDF Text:
"""

st.set_page_config(page_title="Course Evaluation Analyzer", layout="wide")
st.title("📋 Course Evaluation Analyzer with Claude")

api_key = os.getenv("ANTHROPIC_API_KEY") or st.text_input("Enter your Claude API key", type="password")
uploaded_file = st.file_uploader("Upload a Course Evaluation PDF", type="pdf")

if uploaded_file and api_key:
    st.info("Processing PDF...")

    try:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()

        st.subheader("📝 Preview of Extracted Text")
        st.text_area("First 3000 characters:", full_text[:3000])

        if not full_text.strip():
            st.error("❌ Could not extract any text from the PDF. It may be a scanned image. Please upload a PDF with typed (not scanned) text.")
        else:
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
