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

from agent import Agent, generate_Coordinator, generate_AIInnovation, generate_TechnicalArchitect, generate_SecurityCompliance, generate_Legal, generate_Budget, generate_RSE
from Orchestrator_agent import Orchestrator_Agent
from custom_graph import Custom_Graph

import os
import pickle

CHECKPOINT_FILE = "checkpoint_before_graph.pkl"

# SALVATAGGIO CHECKPOINT
def save_checkpoint(agent_list):
    with open(CHECKPOINT_FILE, "wb") as f:
        pickle.dump(agent_list, f)

# CARICAMENTO CHECKPOINT
def load_checkpoint():
    with open(CHECKPOINT_FILE, "rb") as f:
        return pickle.load(f)

def load_question(name:str)->str:
    with open(name, "r", encoding="utf-8") as file:
        lines=file.readlines()
        text=""
        for line in lines:
            text+=line+"\n"
    return text


if __name__ == "__main__":
    if os.path.exists(CHECKPOINT_FILE):
        print("🔄 Loading checkpoint...")
        agent_list = load_checkpoint()
    else:
        att=0
        Coordinator=generate_Coordinator()
        Budget=generate_Budget()
        AIInnovation=generate_AIInnovation()
        Technical=generate_TechnicalArchitect()
        SecurityCompliance=generate_SecurityCompliance()
        Legal=generate_Legal()
        RSE=generate_RSE()
        agent_list=[Coordinator, Budget, AIInnovation, Technical, SecurityCompliance, Legal, RSE]
        Orchestrator=Orchestrator_Agent(agent_list,'command-r')
        question=load_question("file.txt")
        plan=Orchestrator.plan(question,att)
        while plan=={}: 
            att+=1
            plan=Orchestrator.plan(question,att)
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
        save_checkpoint(agent_list)
    graph=Custom_Graph("Nuova_Prova",agent_list)
    graph.triplet_extraction("Nuova_Prova.log")
    graph.saveGraph()