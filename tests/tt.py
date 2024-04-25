import streamlit as st
import json
import os
import uuid
import streamlit as st

from hr_crew.crew import CVAnalystCrew
from tools.read_file import ReadFileContents


def get_temp_path():
    if 'temp_path' not in st.session_state:
        temp_name = str(uuid.uuid4())
        temp_path = f"temp/{temp_name}"
        os.makedirs(temp_path, exist_ok=True)
        st.session_state['temp_path'] = temp_path
    return st.session_state['temp_path']


def are_all_fields_filled(responses):
    for key, value in responses.items():
        if not value:
            return False
    return True

def check_uploaded_file(uploaded_file):
    file_name = uploaded_file.name
    file_content = uploaded_file.getvalue()
    readfile = ReadFileContents(file_name, file_content)
    if file_name.endswith('.doc'):
        cv_content = readfile.read_doc_file()
    elif file_name.endswith('.docx'):
        cv_content = readfile.read_docx_file()
    elif file_name.endswith('.txt'):
        cv_content = readfile.read_txt_file()
    elif file_name.endswith('.pdf'):
        cv_content = readfile.read_pdf_file()
    else:
        cv_content = "Unsupported file type"
    return cv_content

def query_init(selected_vacancy, cv_contents, vacancy_details):
    agent_analysis = "Agent analysis (%)"
    information_found = "why"
    requirement_match = []
    would_be_plus_match = []

    for requirement in selected_vacancy["vacancy_requirements"][0]["vacancy_requirements_description"]:
        requirement_match.append(f"Requirement: {requirement}\n "
                                 f"Agent analysis: {agent_analysis} \n"
                                 f"{information_found} \n\n")
    for would_be_plus in selected_vacancy["would_be_plus"][0]["would_be_plus_description"]:
        would_be_plus_match.append(f"Would be plus: {would_be_plus}\n"
                                   f"Agent analysis: {agent_analysis} \n"
                                   f"{information_found} \n\n")

    requirement_match = "\n".join(requirement_match)
    would_be_plus_match = "\n".join(would_be_plus_match)
    expected_output = (f"\nVacancy name: {selected_vacancy['vacancy_name']} \n"
                       f"Candidate Suitability Percentage: {agent_analysis}\n"
                       f"Candidate requirements match: \n\n "
                       f"{requirement_match}\n\n"
                       f"Candidate would-be-plus match: \n\n"
                       f"{would_be_plus_match}\n")
    inputs = {
        "vacancy": f"{vacancy_details}",
        "resume": f"{cv_contents}",
        "expected_output": f"{expected_output}"
    }
    return inputs

current_step = st.session_state.get('current_step', 1)
responses = st.session_state.get('responses', {})
selected_vacancy_value = responses.get("selected_vacancy", "")

# Step 1: Get available vacancy names  and  display form
if current_step == 1:
    # Open Vacancies JSON file get names
    with open('vacancies.json', 'r') as f:
        vacancies_data = json.load(f)
        vacancy_names = [vacancy['vacancy_name'] for vacancy in vacancies_data]
    index = None if not selected_vacancy_value or selected_vacancy_value not in vacancy_names else vacancy_names.index(
        selected_vacancy_value)
    # Display form
    responses["name"] = st.text_input("Name", value=responses.get("name", ""), key=f"name")
    responses["email"] = st.text_input("E-Mail", value=responses.get("email", ""), key=f"email")
    responses["selected_vacancy"] = st.selectbox('Select a vacancy', vacancy_names, index=index, key="selected_vacancy")
    uploaded_file = st.file_uploader("Choose a file")
    # Next button
    col1, col2 = st.columns([8, 1])
    # If clicked
    if col2.button("Next"):
        # Check if all fields are filled
        if are_all_fields_filled(responses) and uploaded_file:
            # Save all responses to session for future use
            st.session_state['responses'] = responses
            # Display loading and check file and create a temp file with Resume Contents
            with st.spinner("The assistant is analyzing the details of your CV, please wait..."):
                if uploaded_file is not None:
                    cv_contents = check_uploaded_file(uploaded_file)  # operation that takes time
                    temp_path = get_temp_path()
                    with open(os.path.join(temp_path, "resume.txt"), "w") as f:
                        f.write(cv_contents)
            # Set session state for next step
            st.session_state['current_step'] = current_step + 1
            # Rerun the script to  load the next step and remove the first one
            st.rerun()
        else:
            st.warning("All fields are required. Please check the fields for errors.")
# Next step: Render gathered information and send to CrewAI for analysis
elif current_step == 2:
    # Define the temp folder path
    temp_path = get_temp_path()
    # Temp  file path for resume
    temp_file_path = f"{temp_path}/resume.txt"
    # Read the resume content
    with open(temp_file_path, 'r') as t:
        cv_contents = t.read()
    # Read the selected vacancy details
    with open('vacancies.json', 'r') as f:
        vacancies_data = json.load(f)
    # Set selected vacancy from session[responses]
    selected_vacancy = next(
        (vacancy for vacancy in vacancies_data if vacancy["vacancy_name"] == responses["selected_vacancy"]), None)
    # Reformat Vacancy details for  better readability
    vacancy_details = (
        f'\tVacancy Name: {selected_vacancy["vacancy_name"]}\n'
        f'\tSuitability Needed For the Vacancy: {selected_vacancy["vacancy_suitability_needed"]}\n'
        '\tVacancy Requirements:\n'
        + "\t\t" + "\n\t\t".join([f'- {req}' for req in selected_vacancy["vacancy_requirements"][0]["vacancy_requirements_description"]]) + "\n"
        + f'\tVacancy Requirements Affect: {selected_vacancy["vacancy_requirements"][0]["vacancy_requirements_affect"]}\n'
        + f'\tWould be plus:\n'
        + "\t\t" + "\n\t\t".join(
        [f'- {detail}' for detail in selected_vacancy["would_be_plus"][0]["would_be_plus_description"]])
        + f'\tWould Be Plus Affect: {selected_vacancy["would_be_plus"][0]["would_be_plus_affect"]}\n'
        + f'\tVacancy Notes: {selected_vacancy["vacancy_notes"]}'
    )
    # Save the new format to a temp file for future use
    with open(os.path.join(temp_path, "vacancy.txt"), "w") as f:
        f.write(vacancy_details)
    # May be removed
    st.session_state["vacancy_details"] = vacancy_details
    # Add a loader and start initializing with crewAI
    with st.spinner("The assistant is analyzing the details of your CV, please wait..."):
        # Get candidate name from session data
        name = st.session_state.get('responses', {}).get("name", "")
        # Display a loading message from assistant
        message1 = st.chat_message("assistant", avatar="🤖")
        message1.write(
            f"*{name}*, **Get yourself a cup of coffee, this may take a few minutes**")
        # Initilze the first query for the first agent
        first_query = query_init(selected_vacancy, cv_contents, vacancy_details)
        # Send the task to agent
        first_analysis = CVAnalystCrew().cv_analysis_task(fq=first_query).execute()
        # Save the results to a temp file for future use
        with open(os.path.join(temp_path, "first_analysis.txt"), "w") as f:
            f.write(first_analysis)
        # May be removed
        st.session_state['first_analysis_report'] = first_analysis
        # Initialize and execute the second task for the second agent
        second_analysis = CVAnalystCrew().hr_manager_task(first_analysis_report=first_analysis).execute()
        # Save the results of second analysis to a temp file for future use
        with open(os.path.join(temp_path, "second_analysis.txt"), "w") as f:
            f.write(second_analysis)
        # Reformat the questions returned from agent
        result_analysis_json = json.loads(second_analysis)
        # Now result_analysis_json is a Python dictionary
        questions = result_analysis_json.get('questions', [])
        # May be removed
        st.session_state["questions"] = questions
        # Change the current step state to next step
        st.session_state['current_step'] = current_step + 1
        # Rerun the script to initialize data
        st.rerun()

#Next step: Retrieve and display the questions from  Assistant
elif current_step == 3:
    # Get the candidate name from  session
    name = st.session_state.get('responses', {}).get("name", "")
    # Display an assistant message
    message = st.chat_message("assistant", avatar="🤖")
    message.write(f"*{name}*, **please answer these questions to better analyze your suitability for the vacancy:**")
    # Retrieve questions from previous session
    questions = st.session_state["questions"]
    # Count the number of questions
    num_questions = len(questions)
    # Set session for answers
    answers = st.session_state.get('answers', [''] * num_questions)
    # Set steps  for questions (In case there are more than 5 questions)
    question_step = st.session_state.get('question_step', 1)
    # If there are more than 5 questions
    if num_questions > 5:
        # First page of questions
        if question_step == 1:
            for i, question in enumerate(questions[:5]):
                answers[i] = st.text_input(f"{i + 1}. {question}", value=answers[i], key=f"q_{i}")

            col1, col2 = st.columns([12, 3])
            col1.button("Previous", disabled=True, key='previous', help='Go to previous page',
                        on_click=lambda: st.session_state.update({'current_step': 1}))
            if col2.button("Next Questions"):
                if all(answers[:5]):
                    st.session_state['answers'] = answers
                    st.session_state['question_step'] = 2
                    st.rerun()
                else:
                    st.warning("Please answer all questions before proceeding.")
        # Second page of questions
        elif question_step == 2:
            for i, question in enumerate(questions[5:]):
                answers[i + 5] = st.text_input(f"{i + 6}. {question}", value=answers[i + 5], key=f"q_{i + 5}")
            col1, col2 = st.columns([11, 2])
            if col1.button("Previous"):
                st.session_state['answers'] = answers
                st.session_state['question_step'] = 1
                st.rerun()
            elif col2.button("Continue"):
                if all(answers[5:]):
                    st.session_state['answers'] = answers
                    st.session_state['question_step'] = 3
                    st.rerun()
                else:
                    st.warning("Please answer all questions before proceeding.")
        # Send the answers to analysis
        elif question_step == 3:
            with st.spinner("The assistant is analyzing your answers, please wait..."):
                temp_path = get_temp_path()
                temp_file_path = f"{temp_path}/resume.txt"
                with open(temp_file_path, 'r') as t:
                    cv_contents = t.read()
                # Gather all answers into a single string
                all_answers = "\n".join(
                    [f"Question: {question}\nAnswer: {answer}\n" for question, answer in zip(questions, answers)])
                with open(os.path.join(temp_path, "all_answers.txt"), "w") as f:
                    f.write(all_answers)
                # Pass answers to third agent for overall analysis
                third_agent_input = {
                    "first_analysis_report": st.session_state.get('first_analysis_report'),
                    "vacancy_details": st.session_state.get("vacancy_details"),
                    "resume": cv_contents,
                    "questions_answers": all_answers,
                }  # Modify this according to the third agent's requirements
                last_report = CVAnalystCrew().hr_manager_report_task(q=third_agent_input).execute()
                temp_path = get_temp_path()
                with open(os.path.join(temp_path, "last_report.txt"), "w") as f:
                    f.write(last_report)
                st.session_state['current_step'] = current_step + 1
                st.rerun()
    else:
        if question_step == 1:
            for i, question in enumerate(questions):
                answers[i] = st.text_input(f"{i + 1}. {question}", value=answers[i], key=f"q_{i}")

            col1, col2 = st.columns([12, 3])
            col1.button("Previous", disabled=True, key='previous', help='Go to previous page',
                        on_click=lambda: st.session_state.update({'current_step': 1}))
            if col2.button("Next Questions"):
                if all(answers):
                    st.session_state['answers'] = answers
                    st.session_state['question_step'] = 2
                    st.rerun()
                else:
                    st.warning("Please answer all questions before proceeding.")
        # Second page of questions