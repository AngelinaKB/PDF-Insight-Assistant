import streamlit as st
from summarizer import extract_text, summarize_text
from interactive_agent import (
    load_chunks,
    create_qa_chain,
    ask_question_with_justification,
    generate_questions,
    evaluate_user_answer
)

# App configuration and title
st.set_page_config(page_title="PDF Companion", layout="centered")
st.title("📘 PDF Summarizer + QA Assistant")

# Upload PDF input
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file:
    # Save and process uploaded PDF
    with st.spinner("🔍 Processing PDF..."):
        with open("session_doc.pdf", "wb") as f:
            f.write(uploaded_file.read())

        # Generate and display summary
        st.subheader("📝 Summary (≤150 words)")
        full_text = extract_text(open("session_doc.pdf", "rb"))
        summary = summarize_text(full_text)
        st.info(summary)

        # Load PDF into retriever chain
        chunks = load_chunks("session_doc.pdf")
        qa_chain = create_qa_chain(chunks)

        # Mode selection
        st.header("🧠 Interact with Your Document")
        mode = st.radio("Choose a Mode:", ["Ask Anything", "Challenge Me"])

        # Freeform Q&A mode
        if mode == "Ask Anything":
            query = st.text_input("Ask a question about the document:")
            if query:
                with st.spinner("Answering..."):
                    response = ask_question_with_justification(query, qa_chain)

                    st.markdown("### 💬 Response")
                    if isinstance(response, dict):
                        question = response.get("query", "")
                        answer = response.get("result", "")
                        st.markdown(f"**🧾 Question:** {question}")
                        st.markdown(f"**📘 Answer:**\n\n{answer}")
                    else:
                        st.markdown(response)

        # Quiz-style challenge mode
        elif mode == "Challenge Me":
            if "questions" not in st.session_state:
                st.session_state.questions = generate_questions(chunks[0].page_content, qa_chain)
                st.session_state.responses = []
                st.session_state.index = 0
                st.session_state.feedback = {}

            qlist = st.session_state.questions
            idx = st.session_state.index

            if idx < len(qlist):
                st.markdown(f"**❓ Question {idx + 1}:** {qlist[idx]}")
                user_ans = st.text_input("Your Answer:", key=f"ans_{idx}")

                col1, col2 = st.columns(2)

                # Evaluate answer
                with col1:
                    if st.button("✅ Review My Answer"):
                        if user_ans.strip():
                            with st.spinner("Evaluating..."):
                                feedback = evaluate_user_answer(qlist[idx], user_ans, qa_chain)
                                st.session_state.feedback[idx] = feedback
                        else:
                            st.warning("Please enter your answer before reviewing.")

                # Display feedback
                if idx in st.session_state.feedback:
                    st.markdown("#### 📋 Feedback:")
                    fb = st.session_state.feedback[idx]
                    st.info(fb.get("result", "") if isinstance(fb, dict) else fb)

                # Proceed to next question
                with col2:
                    if st.button("➡️ Next Question"):
                        if user_ans.strip():
                            st.session_state.responses.append(
                                (qlist[idx], user_ans, st.session_state.feedback.get(idx, "No feedback"))
                            )
                            st.session_state.index += 1
                            st.rerun()
                        else:
                            st.warning("Please enter your answer before proceeding.")

            # If all questions completed
            else:
                st.success("✔️ You've completed the challenge!")
                for i, (q, ans, fb) in enumerate(st.session_state.responses):
                    with st.expander(f"📘 Q{i+1}: {q}"):
                        st.markdown(f"**Your Answer:** {ans}")
                        st.markdown(f"**Feedback:** {fb.get('result', '') if isinstance(fb, dict) else fb}")

        # Option to reset state
        st.markdown("---")
        if st.button("🔄 Reset Challenge"):
            for key in ["questions", "responses", "index", "feedback"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()