import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("Nuova_Prova.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
AGENT_LEVEL = 25  # tra INFO(20) e WARNING(30)
logging.addLevelName(AGENT_LEVEL, "AGENT")

from agent import Agent, create_all_agents
from Orchestrator_agent import Orchestrator_Agent
#from custom_graph import Custom_Graph

import os
import pickle
from custom_graph import Custom_Graph
CHECKPOINT_FILE = "checkpoint_before_graph.pkl"

# SALVATAGGIO CHECKPOINT
def save_checkpoint(agent_list):
    with open(CHECKPOINT_FILE, "wb") as f:
        pickle.dump(agent_list, f)

# CARICAMENTO CHECKPOINT
def load_checkpoint():
    with open(CHECKPOINT_FILE, "rb") as f:
        return pickle.load(f)

from requirementsExtractor import RequirementsExtractor
from constraintsExtractor import ConstraintsExtractor

def load_question(name:str)->str:
    with open(name, "r", encoding="utf-8") as file:
        lines=file.readlines()
        text=""
        for line in lines:
            text+=line+"\n"
    return text

if __name__=="__main__":
    if os.path.exists(CHECKPOINT_FILE):
        print("🔄 Loading checkpoint...")
        agent_list = load_checkpoint()
    else:
        att=0
        agent_list=create_all_agents('llama3.3:70b')
        Orchestrator=Orchestrator_Agent(agent_list,'llama3.3:70b', "Total")
        question=load_question("file.txt")
        plan=Orchestrator.plan(question, att, True)
        while plan=={}: 
            att+=1
            plan=Orchestrator.plan(question,att, True)
        for key in plan.keys():
            for agent in agent_list:
                if agent.name==key:
                    risposta=agent.answer(plan[key])
                    coherency=agent.coherency_check(risposta)
                    attempts=1
                    while coherency==False and attempts<=4:
                        risposta=agent.retry(plan[key], risposta)
                        coherency=agent.coherency_check(risposta)
                        attempts+=1
                    correct= Orchestrator.correct_answer(key,risposta, plan[key])
        proposal=Orchestrator.propose(question)
        Orchestrator.complete(True)

        att=0
        plan=Orchestrator.plan(question, att, False)
        while plan=={}: 
            att+=1
            plan=Orchestrator.plan(question,att, False)
        for key in plan.keys():
            for agent in agent_list:
                if agent.name==key:
                    risposta=agent.answer(plan[key])
                    coherency=agent.coherency_check(risposta)
                    attempts=1
                    while coherency==False and attempts<=4:
                        risposta=agent.retry(plan[key], risposta)
                        coherency=agent.coherency_check(risposta)
                        attempts+=1
                    correct= Orchestrator.correct_answer(key,risposta, plan[key])
        proposal=Orchestrator.propose(question)
        Orchestrator.complete(False)
        
