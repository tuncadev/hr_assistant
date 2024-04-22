import json
import os
import re
import time
import streamlit as st
from dotenv import load_dotenv

from hr_crew.crew import CVAnalystCrew
from tools.read_file import ReadFileContents
from tools.css_manipulator import CSSManipulator


# Function to validate email format
def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(pattern, email):
        return True
    else:
        return False


def validate_inputs(inputs):
    invalid_fields = []
    for field_name, field_value in inputs.items():
        if not field_value:
            invalid_fields.append(field_name)
    return invalid_fields


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

def crew_init():
    load_dotenv()
    openai_api = os.getenv("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = str(openai_api)

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


def run():
    css_manipulator = CSSManipulator()
    cv_contents = ""
    questions = ""
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

    css_manipulator.add_style({
        ".block-container": "padding: 80px 0px;",
        ".test p": "color: #cccccc;",
        ".test": "width:100%;background-color: #202060;"
    })
    with open('vacancies.json', 'r') as f:
        vacancies_data = json.load(f)
        vacancy_names = [vacancy['vacancy_name'] for vacancy in vacancies_data]
    with st.form(key='my_form'):
        form_submitted = False
        fields = {
            "name": st.text_input(label='Enter your name'),
            "email": st.text_input(label='Enter your email'),
            "selected_vacancy": st.selectbox('Select a vacancy', vacancy_names, index=None),
            "uploaded_file": st.file_uploader("Choose a file"),
        }

        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            selected_vacancy = fields["selected_vacancy"]
            invalid_fields = validate_inputs(fields)
            uploaded_file = fields["uploaded_file"]
            for field_name in invalid_fields:
                st.warning(f'{field_name} is required.')
            if not invalid_fields:
                form_submitted = True
    if form_submitted:
        selected_vacancy = next(
            (vacancy for vacancy in vacancies_data if vacancy["vacancy_name"] == fields['selected_vacancy']), None)
        vacancy_details = (
            f'\tVacancy Name: {selected_vacancy["vacancy_name"]}\n'
            f'\tSuitability Needed For the Vacancy: {selected_vacancy["vacancy_suitability_needed"]}\n'
            '\tVacancy Requirements:\n'
            + "\t\t" + "\n\t\t".join([f'- {req}' for req in selected_vacancy["vacancy_requirements"][0][
            "vacancy_requirements_description"]]) + "\n"
            + f'\tVacancy Requirements Affect: {selected_vacancy["vacancy_requirements"][0]["vacancy_requirements_affect"]}\n'
            + f'\tWould be plus:\n'
            + "\t\t" + "\n\t\t".join(
            [f'- {detail}' for detail in selected_vacancy["would_be_plus"][0]["would_be_plus_description"]])
            + f'\tWould Be Plus Affect: {selected_vacancy["would_be_plus"][0]["would_be_plus_affect"]}\n'
            + f'\tVacancy Notes: {selected_vacancy["vacancy_notes"]}'
        )
        css_manipulator.add_style({".st-emotion-cache-r421ms": "display:none;"})
        with st.spinner("The assistant is analyzing the details of your CV, please wait..."):
            cv_contents = check_uploaded_file(uploaded_file)  # operation that takes time
            if uploaded_file is not None:
                with open(os.path.join("uploads", uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
            first_query = query_init(selected_vacancy, cv_contents, vacancy_details)
            result_analysis = CVAnalystCrew().crew().kickoff(inputs=first_query)
            # Assuming result_analysis is a JSON string
            result_analysis_json = json.loads(result_analysis)
            # Now result_analysis_json is a Python dictionary
            questions = result_analysis_json.get('questions', [])
        st.write(questions)


if __name__ == "__main__":
    run()
