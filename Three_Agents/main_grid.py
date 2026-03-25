from agent import Agent
import json
import logging
from Orchestrator_agent import Orchestrator_Agent
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("test.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_context(text:str)->dict:
    with open(text, "r") as cont:
        data=json.load(cont)
    return data

def generate_HR()->Agent:
    HR=Agent(
        name="HR Agent",
        context=(
            "You are the HR assistant for BuildCraft S.r.l., a house construction company. "
            "You manage employee availability, roles, and scheduling for April 2025."
        ),
        description=(
            "Manages employee availability, roles, departments, and absences for BuildCraft S.r.l. in April 2025. "
            "Can answer questions about staffing coverage, availability by date, and absence reasons "
            "for a team of 10 employees across Construction, Engineering, Design, Systems, and Operations."
            ),
        data=get_context("context1.json"),
        model='command-r'
    )
    return HR

def generate_Logistic()->Agent:
    Logistic=Agent(
        name="Logistic Agent",
        context=(
            "You are the logistics planner for BuildCraft S.r.l., a house construction company. "
            "You have full knowledge of every part of a standard house construction. "
            "For each house part you know: its name, the estimated number of days required to complete it, "
            "and the exact number and roles of workers needed. "
            "Use this information to plan construction schedules, estimate total durations, "
            "identify resource requirements, and allocate the right workers to each task."
        ),
        description=(
            "Manages the construction planning of each part of a house for BuildCraft S.r.l. "
            "Knows the estimated duration in days and the required worker roles and counts "
            "for each of the 10 house parts, from Foundation to Final Inspection."
        ),
        data=get_context("context2.json"),
        model='command-r'
    )
    return Logistic
    
if __name__ == "__main__":

    HR=generate_HR()
    Logistic=generate_Logistic()
    agent_list=[HR,Logistic]
    Orchestrator=Orchestrator_Agent(agent_list,'command-r')
    plan=Orchestrator.plan("I just need to build a bathroom in one house. The work will begin on the 15th of April 2025 and end in the 29th of April, who is available and which roles do I need?",0)
    for key in plan.keys():
        for agent in agent_list:
            if agent.name==key:
                risposta=agent.answer(plan[key])
                coherency=agent.coherency_check(risposta)
                attempts=1
                while coherency==False and attempts<=4:
                    risposta=agent.answer(plan[key])
                    coherency=agent.coherency_check(risposta)
                    attempts+=1
#    answer=HR.answer("Who is fully available for the entire month?")
#    verification=HR.answer("Are this data correct: "+ answer + "\n Answer ONLY TRUE or FAlSE, do not add any additional info.\n ANSWER:")
