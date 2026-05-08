"""
Quiz Generator
--------------
Auto-generate MCQ quizzes from any topic, text, or PDF.
Interactive quiz-taking interface with scoring.
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


def parse_quiz(raw_text):
    """Parse LLM output into structured quiz data."""
    questions = []

    # Try JSON parsing first
    try:
        json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            for item in parsed:
                if isinstance(item, dict) and all(k in item for k in ["question", "options", "correct"]):
                    questions.append({
                        "question": item["question"],
                        "options": item["options"],
                        "correct": item["correct"],
                        "explanation": item.get("explanation", ""),
                    })
            if questions:
                return questions
    except (json.JSONDecodeError, AttributeError):
        pass

    return questions


def run_quiz_generator():
    st.title("❓ Quiz Generator")
    st.markdown("Auto-generate MCQ quizzes from any topic or PDF — test your knowledge!")

    llm = get_llm()

    # Session state
    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = []
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    # Input tabs
    tab_topic, tab_pdf = st.tabs(["📝 From Topic", "📄 From PDF"])

    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
         "You are a quiz creation expert. Generate exactly {num_questions} multiple-choice questions. "
         "Return them as a JSON array. Each question object must have:\n"
         "- 'question': the question text\n"
         "- 'options': an array of exactly 4 options (strings)\n"
         "- 'correct': the index (0-3) of the correct option\n"
         "- 'explanation': brief explanation of why the answer is correct\n"
         "Make questions that truly test understanding, not just memorization.\n"
         "Example: [{{\"question\": \"What is...?\", \"options\": [\"A\", \"B\", \"C\", \"D\"], \"correct\": 0, \"explanation\": \"Because...\"}}]" ),
        ("human", "Generate a quiz about: {content}"),
    ])

    chain = prompt_template | llm | StrOutputParser()

    with tab_topic:
        topic = st.text_input("Enter a topic:", placeholder="e.g., Machine Learning Basics, World War II, Organic Chemistry...")
        difficulty = st.select_slider("Difficulty:", options=["Easy", "Medium", "Hard"], value="Medium", key="quiz_diff")
        num_q = st.slider("Number of questions:", min_value=3, max_value=15, value=5, key="quiz_topic_count")
        if st.button("❓ Generate Quiz", key="gen_topic_quiz", use_container_width=True):
            if not topic:
                st.warning("Please enter a topic.")
                return
            with st.spinner("❓ Generating quiz..."):
                try:
                    content = f"{topic} (Difficulty: {difficulty})"
                    response = chain.invoke({"content": content, "num_questions": str(num_q)})
                    questions = parse_quiz(response)
                    if questions:
                        st.session_state.quiz_questions = questions
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        st.success(f"✅ Generated {len(questions)} questions!")
                        st.rerun()
                    else:
                        st.error("Could not parse quiz. Showing raw output:")
                        st.markdown(response)
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")

    with tab_pdf:
        uploaded_file = st.file_uploader("Upload a PDF:", type="pdf", key="quiz_pdf_upload")
        num_q_pdf = st.slider("Number of questions:", min_value=3, max_value=15, value=5, key="quiz_pdf_count")
        if st.button("❓ Generate from PDF", key="gen_pdf_quiz", use_container_width=True):
            if not uploaded_file:
                st.warning("Please upload a PDF.")
                return
            with st.spinner("📖 Reading PDF and generating quiz..."):
                try:
                    tmp_path = None
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        loader = PyPDFLoader(tmp_path)
                        docs = loader.load()
                        content = "\n".join([doc.page_content for doc in docs[:10]])
                    finally:
                        if tmp_path and os.path.exists(tmp_path):
                            os.unlink(tmp_path)

                    response = chain.invoke({"content": content[:8000], "num_questions": str(num_q_pdf)})
                    questions = parse_quiz(response)
                    if questions:
                        st.session_state.quiz_questions = questions
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        st.success(f"✅ Generated {len(questions)} questions from PDF!")
                        st.rerun()
                    else:
                        st.error("Could not parse quiz. Showing raw output:")
                        st.markdown(response)
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")

    # ---------------------------------------------------------------------------
    # Quiz Taking Interface
    # ---------------------------------------------------------------------------
    if st.session_state.quiz_questions:
        st.markdown("---")
        questions = st.session_state.quiz_questions
        total = len(questions)

        if not st.session_state.quiz_submitted:
            st.subheader(f"📝 Take the Quiz ({total} Questions)")

            for i, q in enumerate(questions):
                st.markdown(f"**Q{i + 1}.** {q['question']}")
                answer = st.radio(
                    f"Select your answer for Q{i + 1}:",
                    options=q["options"],
                    key=f"quiz_q_{i}",
                    label_visibility="collapsed",
                )
                if answer:
                    st.session_state.quiz_answers[i] = q["options"].index(answer)
                st.markdown("")

            if st.button("✅ Submit Quiz", use_container_width=True, type="primary"):
                if len(st.session_state.quiz_answers) < total:
                    st.warning(f"Please answer all {total} questions before submitting.")
                else:
                    st.session_state.quiz_submitted = True
                    st.rerun()

        else:
            # Show results
            correct = 0
            for i, q in enumerate(questions):
                user_answer = st.session_state.quiz_answers.get(i, -1)
                is_correct = user_answer == q["correct"]
                if is_correct:
                    correct += 1

                icon = "✅" if is_correct else "❌"
                st.markdown(f"**{icon} Q{i + 1}.** {q['question']}")
                st.markdown(f"Your answer: **{q['options'][user_answer]}**")
                if not is_correct:
                    st.markdown(f"Correct answer: **{q['options'][q['correct']]}**")
                if q.get("explanation"):
                    st.info(f"💡 {q['explanation']}")
                st.markdown("")

            # Score
            percentage = (correct / total) * 100
            if percentage >= 80:
                color = "#2ed573"
                emoji = "🎉"
                msg = "Excellent!"
            elif percentage >= 60:
                color = "#ffa502"
                emoji = "👍"
                msg = "Good job!"
            else:
                color = "#ff4757"
                emoji = "📚"
                msg = "Keep studying!"

            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color}22, {color}11);
                border: 2px solid {color};
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                margin: 1rem 0;
            ">
                <div style="font-size: 3rem;">{emoji}</div>
                <div style="font-size: 2rem; font-weight: 700; color: {color};">
                    {correct}/{total} ({percentage:.0f}%)
                </div>
                <div style="font-size: 1.2rem; color: {color};">{msg}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🔄 Retake Quiz", use_container_width=True):
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()

            if st.button("🆕 New Quiz", use_container_width=True):
                st.session_state.quiz_questions = []
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()
