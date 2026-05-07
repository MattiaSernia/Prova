import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("Conversation.log", mode = 'w', encoding='utf-8'),
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
import validation.Validation as va
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

def load_question(name: str) -> str:
    with open(name, "r", encoding="utf-8") as f:
        return "".join(line + "\n" for line in f.readlines())

def _run_pipeline(orchestrator, agents, question, use_kg, val_file, single_val_file, val):
    att = 0
    plan = orchestrator.plan(question, att, use_kg)
    while plan == {}:
        att += 1
        plan = orchestrator.plan(question, att, use_kg)
    for key in plan:
        for agent in agents:
            if agent.name == key:
                risposta = agent.answer(plan[key])
                coherency = agent.coherency_check(risposta)
                attempts = 1
                while not coherency and attempts <= 4:
                    risposta = agent.retry(plan[key], risposta)
                    coherency = agent.coherency_check(risposta)
                    attempts += 1
                orchestrator.correct_answer(key, risposta, plan[key])
    proposal = orchestrator.propose(question)
    with open(val_file, "w") as f:
        f.write("REQUIREMENTS\n")
        for element in val.validate_requirements(proposal):
            f.write(element + "\n")
        f.write("\nCONSTRAINTS\n")
        for element in val.validate_constraints(proposal):
            f.write(element + "\n")
    val.validate(proposal, single_val_file)
    orchestrator.complete(use_kg)

if __name__ == "__main__":
    val = va.Validation("llama3.3:70b", 0)
    if os.path.exists(CHECKPOINT_FILE):
        print("🔄 Loading checkpoint...")
        agent_list = load_checkpoint()
    else:
        agent_list = create_all_agents('llama3.3:70b')
        Orchestrator = Orchestrator_Agent(agent_list, 'llama3.3:70b', "Total")
        question = load_question("file.txt")
        _run_pipeline(Orchestrator, agent_list, question, True,  "validation_kg.txt",   "single_validation_kg.txt",   val)
        _run_pipeline(Orchestrator, agent_list, question, False, "validation_nokg.txt", "single_validation_nokg.txt", val)

