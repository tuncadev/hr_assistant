import streamlit as st
import time

questions = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Arcu non sodales neque sodales ut etiam. Eget arcu dictum varius duis at consectetur. ",
    "Eget nunc lobortis mattis aliquam faucibus purus in massa. Consequat ac felis donec et odio pellentesque diam.",
    "question 3",
    "question 4",
    "question 5",
    "Eget nunc lobortis mattis aliquam faucibus purus in massa. Consequat ac felis donec et odio pellentesque diam.",
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Arcu non sodales neque sodales ut etiam. ",
    "question 8",
    "question 9",
    "question 10",
]
st.set_page_config(
    page_title="Ex-stream-ly Cool App",
    page_icon="🧊",

    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)
num_questions = len(questions)
current_step = st.session_state.get('current_step', 1)
responses = st.session_state.get('answers', [''] * num_questions)

if num_questions > 5:
    if current_step == 1:
        for i, question in enumerate(questions[:5]):
            responses[i] = st.text_input(f"{i+1}. {question}", value=responses[i], key=f"q_{i}")

        col1, col2 = st.columns([12, 3])
        col1.button("Previous", disabled=True, key='previous', help='Go to previous page',
                    on_click=lambda: st.session_state.update({'current_step': 1}))
        if col2.button("Next Questions"):
            if all(responses[:5]):
                st.session_state['responses'] = responses
                st.session_state['current_step'] = 2
                st.rerun()
            else:
                st.warning("Please answer all questions before proceeding.")

    elif current_step == 2:
        for i, question in enumerate(questions[5:]):
            responses[i + 5] = st.text_input(f"{i+6}. {question}", value=responses[i + 5], key=f"q_{i+5}")
        col1, col2 = st.columns([11, 2])
        if col1.button("Previous"):
            st.session_state['responses'] = responses
            st.session_state['current_step'] = 1
            st.rerun()
        elif col2.button("Continue"):
            if all(responses[5:]):
                st.session_state['responses'] = responses
                st.session_state['current_step'] = 3
                st.rerun()
            else:
                st.warning("Please answer all questions before proceeding.")

    elif current_step == 3:
        answers = ""
        for i, (question, response) in enumerate(zip(questions, responses)):
            answers += f"Question: {question} ( Answer: {response}  )\n"
        st.write(answers)