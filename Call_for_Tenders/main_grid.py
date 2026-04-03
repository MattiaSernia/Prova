import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("Primo.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
AGENT_LEVEL = 25  # tra INFO(20) e WARNING(30)
logging.addLevelName(AGENT_LEVEL, "AGENT")

from agent import Agent, generate_Budget, generate_Compliance, generate_Contract, generate_HR, generate_Pipeline
import json
from Orchestrator_agent import Orchestrator_Agent
from custom_graph import Custom_Graph

def get_context(text:str)->dict:
    with open(text, "r") as cont:
        data=json.load(cont)
    return data

if __name__ == "__main__":
    att=0
    HR=generate_HR()
    Budget=generate_Budget()
    Pipeline=generate_Pipeline()
    Contract=generate_Contract()
    Compliance=generate_Compliance()
    agent_list=[HR,Budget, Pipeline, Contract, Compliance]
    Orchestrator=Orchestrator_Agent(agent_list,'command-r')
    plan=Orchestrator.plan("Are we ready to bid for the Regione Lombardia €2M infrastructure tender, submission deadline May 10th?",att)
    while plan=={}: 
        att+=1
        plan=Orchestrator.plan("Are we ready to bid for the Regione Lombardia €2M infrastructure tender, submission deadline May 10th?",att)
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
                correct= Orchestrator.correct_answer(key,risposta, plan[key])
    graph=Custom_Graph("Primo",agent_list)
    graph.triplet_extraction("Primo.log")