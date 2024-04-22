import yaml
import os
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from langchain_openai import ChatOpenAI


class CVAnalystCrew:
    agents_config_path = os.path.join(os.path.dirname(__file__), "config/agents.yaml")
    tasks_config_path = os.path.join(os.path.dirname(__file__), "config/tasks.yaml")

    def __init__(self) -> None:
        with open(self.agents_config_path, 'r') as file:
            self.agents_config = yaml.safe_load(file)
        with open(self.tasks_config_path, 'r') as file:
            self.tasks_config = yaml.safe_load(file)

        self.ai_llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.3
        )

    def cv_analyst(self) -> Agent:

        return Agent(
            role=self.agents_config['cv_analyst']['role'],
            goal=self.agents_config['cv_analyst']['goal'],
            backstory=self.agents_config['cv_analyst']['back_story'],
            allow_delegation=self.agents_config['cv_analyst']['allow_delegation'],
            verbose=self.agents_config['cv_analyst']['verbose'],
            llm=self.ai_llm
        )

    def hr_interviewer(self) -> Agent:
        return Agent(
            role=self.agents_config['hr_interviewer']['role'],
            goal=self.agents_config['hr_interviewer']['goal'],
            backstory=self.agents_config['hr_interviewer']['back_story'],
            allow_delegation=self.agents_config['hr_interviewer']['allow_delegation'],
            verbose=self.agents_config['hr_interviewer']['verbose'],
            llm=self.ai_llm
        )

    def cv_analysis_task(self) -> Task:
        return Task(
            description=self.tasks_config['cv_analysis_task']['description'],
            expected_output=self.tasks_config['cv_analysis_task']['expected_output'],
            agent=self.cv_analyst()
        )

    def hr_manager_task(self) -> Task:
        return Task(
            description=self.tasks_config['hr_manager_task']['description'],
            expected_output=self.tasks_config['hr_manager_task']['expected_output'],
            agent=self.cv_analyst()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.cv_analyst(), self.hr_interviewer()],
            tasks=[self.cv_analysis_task(), self.hr_manager_task()],
            process=Process.sequential,
            verbose=2
        )