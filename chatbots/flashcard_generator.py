"""
Flashcard Generator
-------------------
Generate spaced-repetition flashcards from any topic, text, or PDF.
Students can study with an interactive flip-card interface.
"""

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader
import tempfile
import os
import json
import re
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'providers'))
from llm_provider import get_llm


def parse_flashcards(raw_text):
    """Parse LLM output into structured flashcard data."""
    cards = []
    # Try JSON parsing first
    try:
        json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            for item in parsed:
                if isinstance(item, dict) and "front" in item and "back" in item:
                    cards.append({"front": item["front"], "back": item["back"]})
            if cards:
                return cards
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback: parse Q:/A: or Front:/Back: format
    pairs = re.findall(
        r'(?:Q|Front|Question|Term)[:\s]*(.+?)[\n\r]+(?:A|Back|Answer|Definition)[:\s]*(.+?)(?=\n(?:Q|Front|Question|Term)[:\s]|\Z)',
        raw_text,
        re.DOTALL | re.IGNORECASE,
    )
    for front, back in pairs:
        cards.append({"front": front.strip(), "back": back.strip()})

    return cards


def run_flashcard_generator():
    st.title("🧠 Flashcard Generator")
    st.markdown("Generate study flashcards from any topic or PDF — perfect for spaced repetition!")

    llm = get_llm()

    # Session state
    if "flashcards" not in st.session_state:
        st.session_state.flashcards = []
    if "fc_current_index" not in st.session_state:
        st.session_state.fc_current_index = 0
    if "fc_show_answer" not in st.session_state:
        st.session_state.fc_show_answer = False

    # Input tabs
    tab_topic, tab_pdf = st.tabs(["📝 From Topic", "📄 From PDF"])

    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
         "You are a flashcard creation expert. Generate exactly {num_cards} flashcards for studying. "
         "Return them as a JSON array with 'front' (question/term) and 'back' (answer/definition) keys. "
         "Make the questions clear and the answers concise but complete. "
         "Example format: [{{\"front\": \"What is X?\", \"back\": \"X is ...\"}}]" ),
        ("human", "Generate flashcards for: {content}"),
    ])

    chain = prompt_template | llm | StrOutputParser()

    with tab_topic:
        topic = st.text_input("Enter a topic:", placeholder="e.g., Photosynthesis, Python Data Structures, French Revolution...")
        num_cards = st.slider("Number of flashcards:", min_value=3, max_value=20, value=10, key="fc_topic_count")
        if st.button("🧠 Generate Flashcards", key="gen_topic_fc", use_container_width=True):
            if not topic:
                st.warning("Please enter a topic.")
                return
            with st.spinner("🧠 Creating flashcards..."):
                try:
                    response = chain.invoke({"content": topic, "num_cards": str(num_cards)})
                    cards = parse_flashcards(response)
                    if cards:
                        st.session_state.flashcards = cards
                        st.session_state.fc_current_index = 0
                        st.session_state.fc_show_answer = False
                        st.success(f"✅ Generated {len(cards)} flashcards!")
                    else:
                        st.error("Could not parse flashcards. Showing raw output:")
                        st.markdown(response)
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")

    with tab_pdf:
        uploaded_file = st.file_uploader("Upload a PDF:", type="pdf", key="fc_pdf_upload")
        num_cards_pdf = st.slider("Number of flashcards:", min_value=3, max_value=20, value=10, key="fc_pdf_count")
        if st.button("🧠 Generate from PDF", key="gen_pdf_fc", use_container_width=True):
            if not uploaded_file:
                st.warning("Please upload a PDF.")
                return
            with st.spinner("📖 Reading PDF and creating flashcards..."):
                try:
                    tmp_path = None
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        loader = PyPDFLoader(tmp_path)
                        docs = loader.load()
                        content = "\n".join([doc.page_content for doc in docs[:10]])  # Limit to first 10 pages
                    finally:
                        if tmp_path and os.path.exists(tmp_path):
                            os.unlink(tmp_path)

                    response = chain.invoke({"content": content[:8000], "num_cards": str(num_cards_pdf)})
                    cards = parse_flashcards(response)
                    if cards:
                        st.session_state.flashcards = cards
                        st.session_state.fc_current_index = 0
                        st.session_state.fc_show_answer = False
                        st.success(f"✅ Generated {len(cards)} flashcards from PDF!")
                    else:
                        st.error("Could not parse flashcards. Showing raw output:")
                        st.markdown(response)
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")

    # ---------------------------------------------------------------------------
    # Flashcard Study Interface
    # ---------------------------------------------------------------------------
    if st.session_state.flashcards:
        st.markdown("---")
        st.subheader("📇 Study Your Flashcards")

        cards = st.session_state.flashcards
        idx = st.session_state.fc_current_index
        total = len(cards)

        # Progress
        st.progress((idx + 1) / total, text=f"Card {idx + 1} of {total}")

        # Card display
        card = cards[idx]
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem 0;
            min-height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        ">
            <div style="color: white; font-size: 1.3rem; font-weight: 500;">
                {card['front']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show/hide answer
        if st.button("🔄 Flip Card", key="flip_card", use_container_width=True):
            st.session_state.fc_show_answer = not st.session_state.fc_show_answer

        if st.session_state.fc_show_answer:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #2ed573 0%, #1abc9c 100%);
                border-radius: 16px;
                padding: 2rem;
                margin: 0.5rem 0;
                min-height: 100px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
            ">
                <div style="color: white; font-size: 1.2rem;">
                    {card['back']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Navigation
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ Previous", key="fc_prev", use_container_width=True, disabled=(idx == 0)):
                st.session_state.fc_current_index -= 1
                st.session_state.fc_show_answer = False
                st.rerun()
        with col_next:
            if st.button("➡️ Next", key="fc_next", use_container_width=True, disabled=(idx >= total - 1)):
                st.session_state.fc_current_index += 1
                st.session_state.fc_show_answer = False
                st.rerun()

        # Export flashcards
        st.markdown("---")
        export_data = "\n\n".join([f"Q: {c['front']}\nA: {c['back']}" for c in cards])
        st.download_button(
            "⬇️ Download Flashcards",
            data=export_data,
            file_name="flashcards.md",
            mime="text/markdown",
        )
