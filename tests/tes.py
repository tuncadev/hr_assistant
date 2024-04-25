import json
import os
import uuid
import streamlit as st

from hr_crew.crew import CVAnalystCrew
from tools.read_file import ReadFileContents

questions = [
    "questions1",
    "questions 2",
    "questuons 3"
]
# Count the number of questions
num_questions = len(questions)
# Set session for answers
answers = ('answers', [''] * num_questions)
for i, question in enumerate(questions):
    answers[i] = input(f"{i + 1}. {question}")

if all(answers):
    print("All")
else:
    print("Please answer all questions before proceeding.")
