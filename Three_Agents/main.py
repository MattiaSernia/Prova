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
        description="Manages employee availability, roles, departments, and absences for BuildCraft S.r.l. in April 2025.",
        data=get_context("context1.json"),
        model='phi3.5:latest'
    )
    return HR

def generate_Logistic()->Agent:
    Logistic=Agent(
        name="Logistic Agent",
        context=(
            "You are the logistics planner for BuildCraft S.r.l. "
            "You know every phase of a standard house construction: which workers are needed, "
            "how many, how long each phase takes, and which phases depend on others."
        ),
        description=(
            "Plans and manages the construction schedule of a single-family house. "
            "Knows all construction phases, durations, dependencies, and worker requirements "
            "for each part of the house."
        ),
        data=get_context("context1.json"),
        model='phi3.5:latest'
    )
    return Logistic
    
if __name__ == "__main__":

    HR=generate_HR()
    Logistic=generate_Logistic()
    agent_list=[HR,Logistic]
    Orchestrator=Orchestrator_Agent([HR],'phi3.5:latest')
    plan=Orchestrator.plan("I need to build a bathroom. The construction will stat on the 15th of April",0)
    for key in plan.keys():
        for agent in agent_list:
            if agent.name==key:
                risposta=agent.answer(plan[key])
                #coherency=agent.coherency_check(risposta)
                #attempts=1
                #while coherency==False and attempts<=4:
                #    print(coherency)
                #    risposta=agent.answer(plan[key])
                #    coherency=agent.coherency_check(risposta)
                #    attempts+=1
#    answer=HR.answer("Who is fully available for the entire month?")
#    verification=HR.answer("Are this data correct: "+ answer + "\n Answer ONLY TRUE or FAlSE, do not add any additional info.\n ANSWER:")
