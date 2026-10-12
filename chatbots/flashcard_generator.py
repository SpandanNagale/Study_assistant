"""
Flashcard Generator
-------------------
Generate flashcards from any topic, text, or PDF, save them to persistent decks,
and review them with real spaced repetition (SM-2 scheduling).
"""

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader
import html
import tempfile
import json
import re
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'providers'))
from llm_provider import get_llm
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils import srs


CARD_STYLE = """
<div style="
    background: {bg};
    border-radius: 16px;
    padding: 2rem;
    margin: {margin};
    min-height: {height};
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
">
    <div style="color: white; font-size: {size}; font-weight: 500; white-space: pre-wrap;">{text}</div>
</div>
"""

FRONT_BG = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
BACK_BG = "linear-gradient(135deg, #2ed573 0%, #1abc9c 100%)"


def render_card(text, back=False):
    """Render one side of a card. Text is escaped since it comes from the LLM."""
    st.markdown(
        CARD_STYLE.format(
            bg=BACK_BG if back else FRONT_BG,
            margin="0.5rem 0" if back else "1rem 0",
            height="100px" if back else "150px",
            size="1.2rem" if back else "1.3rem",
            text=html.escape(str(text)),
        ),
        unsafe_allow_html=True,
    )


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


def _set_generated(cards, source):
    st.session_state.flashcards = cards
    st.session_state.fc_source = source
    st.session_state.fc_current_index = 0
    st.session_state.fc_show_answer = False


def run_flashcard_generator():
    st.title("🧠 Flashcard Generator")
    st.markdown(
        "Generate flashcards from any topic or PDF, save them to decks, "
        "and review with **spaced repetition** — cards come back right before you'd forget them."
    )

    # Session state
    st.session_state.setdefault("flashcards", [])
    st.session_state.setdefault("fc_source", "")
    st.session_state.setdefault("fc_current_index", 0)
    st.session_state.setdefault("fc_show_answer", False)
    st.session_state.setdefault("fc_review_show", False)

    due_total = sum(d["due"] for d in srs.list_decks())
    tab_topic, tab_pdf, tab_review, tab_decks = st.tabs([
        "📝 From Topic",
        "📄 From PDF",
        f"🔁 Review ({due_total} due)",
        "📚 My Decks",
    ])

    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
         "You are a flashcard creation expert. Generate exactly {num_cards} flashcards for studying. "
         "Return them as a JSON array with 'front' (question/term) and 'back' (answer/definition) keys. "
         "Make the questions clear and the answers concise but complete. "
         "Example format: [{{\"front\": \"What is X?\", \"back\": \"X is ...\"}}]" ),
        ("human", "Generate flashcards for: {content}"),
    ])

    with tab_topic:
        topic = st.text_input("Enter a topic:", placeholder="e.g., Photosynthesis, Python Data Structures, French Revolution...")
        num_cards = st.slider("Number of flashcards:", min_value=3, max_value=20, value=10, key="fc_topic_count")
        if st.button("🧠 Generate Flashcards", key="gen_topic_fc", use_container_width=True):
            if not topic:
                st.warning("Please enter a topic.")
            else:
                with st.spinner("🧠 Creating flashcards..."):
                    try:
                        chain = prompt_template | get_llm() | StrOutputParser()
                        response = chain.invoke({"content": topic, "num_cards": str(num_cards)})
                        cards = parse_flashcards(response)
                        if cards:
                            _set_generated(cards, topic)
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
            else:
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

                        chain = prompt_template | get_llm() | StrOutputParser()
                        response = chain.invoke({"content": content[:8000], "num_cards": str(num_cards_pdf)})
                        cards = parse_flashcards(response)
                        if cards:
                            _set_generated(cards, os.path.splitext(uploaded_file.name)[0])
                            st.success(f"✅ Generated {len(cards)} flashcards from PDF!")
                        else:
                            st.error("Could not parse flashcards. Showing raw output:")
                            st.markdown(response)
                    except Exception as e:
                        st.error(f"⚠️ Error: {str(e)}")

    with tab_review:
        render_review()

    with tab_decks:
        render_decks()

    # ---------------------------------------------------------------------------
    # Preview + save freshly generated cards
    # ---------------------------------------------------------------------------
    if st.session_state.flashcards:
        render_generated_preview()


def render_generated_preview():
    st.markdown("---")
    st.subheader("📇 Preview Your New Flashcards")

    cards = st.session_state.flashcards
    total = len(cards)

    # Save to a persistent deck
    col_name, col_save = st.columns([3, 1])
    with col_name:
        deck_name = st.text_input(
            "Deck name:",
            value=st.session_state.fc_source or "My deck",
            key="fc_deck_name",
        )
    with col_save:
        st.write("")
        st.write("")
        if st.button("💾 Save to deck", key="fc_save_deck", type="primary", use_container_width=True):
            added = srs.add_cards(deck_name, cards)
            skipped = total - added
            st.success(
                f"✅ Saved {added} card(s) to **{deck_name}**"
                + (f" ({skipped} duplicate(s) skipped)" if skipped else "")
                + ". Review them in the 🔁 Review tab."
            )

    idx = min(st.session_state.fc_current_index, total - 1)
    st.progress((idx + 1) / total, text=f"Card {idx + 1} of {total}")
    card = cards[idx]
    render_card(card["front"])

    if st.button("🔄 Flip Card", key="flip_card", use_container_width=True):
        st.session_state.fc_show_answer = not st.session_state.fc_show_answer

    if st.session_state.fc_show_answer:
        render_card(card["back"], back=True)

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ Previous", key="fc_prev", use_container_width=True, disabled=(idx == 0)):
            st.session_state.fc_current_index = idx - 1
            st.session_state.fc_show_answer = False
            st.rerun()
    with col_next:
        if st.button("➡️ Next", key="fc_next", use_container_width=True, disabled=(idx >= total - 1)):
            st.session_state.fc_current_index = idx + 1
            st.session_state.fc_show_answer = False
            st.rerun()

    export_data = "\n\n".join([f"Q: {c['front']}\nA: {c['back']}" for c in cards])
    st.download_button(
        "⬇️ Download Flashcards",
        data=export_data,
        file_name="flashcards.md",
        mime="text/markdown",
    )


def render_review():
    """Spaced-repetition review session over all due cards (or one deck)."""
    decks = srs.list_decks()
    if not decks:
        st.info("No saved decks yet. Generate flashcards and click **💾 Save to deck** to start reviewing.")
        return

    options = {"All decks": None}
    options.update({f"{d['name']} ({d['due']} due)": d["id"] for d in decks})
    choice = st.selectbox("Review from:", list(options.keys()), key="fc_review_deck")

    queue = srs.due_cards(deck_id=options[choice], limit=1)
    if not queue:
        st.success("🎉 All caught up! No cards are due right now. Come back later.")
        return

    card = queue[0]
    st.caption(f"Deck: **{card['deck_name']}** · seen {card['reps']}× · lapses {card['lapses']}")
    render_card(card["front"])

    if not st.session_state.fc_review_show:
        if st.button("👀 Show Answer", key="fc_review_reveal", use_container_width=True, type="primary"):
            st.session_state.fc_review_show = True
            st.rerun()
        return

    render_card(card["back"], back=True)
    st.markdown("**How well did you remember it?**")
    cols = st.columns(4)
    for col, rating in zip(cols, (srs.AGAIN, srs.HARD, srs.GOOD, srs.EASY)):
        with col:
            label = f"{srs.RATING_LABELS[rating]} · {srs.describe_interval(card, rating)}"
            if st.button(label, key=f"fc_rate_{rating}", use_container_width=True):
                srs.review_card(card["id"], rating)
                st.session_state.fc_review_show = False
                st.rerun()


def render_decks():
    decks = srs.list_decks()
    if not decks:
        st.info("You haven't saved any decks yet.")
        return

    for deck in decks:
        with st.container(border=True):
            col_info, col_dl, col_del = st.columns([4, 1.3, 1])
            with col_info:
                st.markdown(f"**{deck['name']}**")
                st.caption(f"{deck['total']} cards · {deck['due']} due · {deck['new']} new")
            with col_dl:
                st.download_button(
                    "⬇️ CSV",
                    data=srs.export_deck_csv(deck["id"]),
                    file_name=f"{deck['name']}.csv",
                    mime="text/csv",
                    key=f"fc_dl_{deck['id']}",
                    help="Import into Anki or Quizlet",
                    use_container_width=True,
                )
            with col_del:
                if st.button("🗑️", key=f"fc_del_{deck['id']}", help="Delete deck", use_container_width=True):
                    srs.delete_deck(deck["id"])
                    st.rerun()
