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

from agent import create_all_agents
from Orchestrator_agent import Orchestrator_Agent
from mxg import Message

import argparse
import validation.Validation as va


def load_question(name: str) -> str:
    with open(name, "r", encoding="utf-8") as f:
        return "".join(line + "\n" for line in f.readlines())

def _run_pipeline(orchestrator, agents, question, use_kg, kg_agents, cft_agents, triplets_in_proposal, val_file, single_val_file, val):
    att = 0
    plan = orchestrator.plan(question, att, use_kg)
    while plan == {}:
        att += 1
        plan = orchestrator.plan(question, att, use_kg)
    kg_context = orchestrator.get_kg_context() if kg_agents else None
    for key in plan:
        for agent in agents:
            if agent.name == key:
                if kg_agents:
                    agent.set_kg_context(kg_context)
                if cft_agents:
                    agent.set_cft_context(question)
                orchestrator.add_message(Message.now(plan[key], "Orchestrator", "question", "default"))
                risposta = agent.answer(plan[key])
                orchestrator.add_message(Message.now(risposta, agent.name, "answer", "default"))
                coherency = agent.coherency_check(risposta)
                orchestrator.add_message(Message.now(str(coherency).upper(), agent.name, "answer", "coherency"))
                attempts = 1
                while not coherency and attempts <= 4:
                    risposta = agent.retry(plan[key], risposta)
                    orchestrator.add_message(Message.now(risposta, agent.name, "answer", "default"))
                    coherency = agent.coherency_check(risposta)
                    orchestrator.add_message(Message.now(str(coherency).upper(), agent.name, "answer", "coherency"))
                    attempts += 1
                correction = orchestrator.correct_answer(key, risposta, plan[key])
                orchestrator.add_message(Message.now(str(correction).upper(), "Orchestrator", "answer", "correction"))
    proposal = orchestrator.propose(question, triplets_in_proposal)
    orchestrator.add_message(Message.now(proposal, "Orchestrator", "proposal", "default"))
    # with open(val_file, "w") as f:
    #     f.write("REQUIREMENTS\n")
    #     for element in val.validate_requirements(proposal):
    #         f.write(element + "\n")
    #     f.write("\nCONSTRAINTS\n")
    #     for element in val.validate_constraints(proposal):
    #         f.write(element + "\n")
    val.validate(proposal, single_val_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--no-kg", action="store_true", help="Run without knowledge graph in prompt")
    mode.add_argument("--kg-agents", action="store_true", help="Pass KG to agents in addition to orchestrator")
    mode.add_argument("--kg-agents-triplets", action="store_true", help="Pass KG to agents and include extracted triplets in proposal (implies --kg-agents)")
    mode.add_argument("--kg-cft-agents", action="store_true", help="Pass KG to orchestrator only, CFT text to agents")
    parser.add_argument(
        "--extractor",
        choices=["llama", "phi4"],
        default="llama",
        help="Triplet extractor to use (default: llama)",
    )
    parser.add_argument(
        "--chunk-dimension",
        type=int,
        choices=range(0, 110, 10),
        default=0,
        metavar="N",
        help="Chunk dimension (0-100, multiples of 10, default: 0)",
    )
    args = parser.parse_args()

    if args.no_kg:
        use_kg, kg_agents, cft_agents, triplets_in_proposal = False, False, False, False
        graph_name, val_file, single_val_file = "Total_nokg", "validation_nokg.txt", "single_validation_nokg.txt"
    elif args.kg_agents:
        use_kg, kg_agents, cft_agents, triplets_in_proposal = True, True, False, False
        graph_name, val_file, single_val_file = "Total_kgagents", "validation_kgagents.txt", "single_validation_kgagents.txt"
    elif args.kg_agents_triplets:
        use_kg, kg_agents, cft_agents, triplets_in_proposal = True, True, False, True
        graph_name, val_file, single_val_file = "Total_kgagents_tri", "validation_kgagents_tri.txt", "single_validation_kgagents_tri.txt"
    elif args.kg_cft_agents:
        use_kg, kg_agents, cft_agents, triplets_in_proposal = True, False, True, True
        graph_name, val_file, single_val_file = "Total_kgcft", "validation_kgcft.txt", "single_validation_kgcft.txt"
    else:
        use_kg, kg_agents, cft_agents, triplets_in_proposal = True, False, False, False
        graph_name, val_file, single_val_file = "Total", "validation_kg.txt", "single_validation_kg.txt"

    val = va.Validation("llama3.3:70b", 0)
    agent_list = create_all_agents('llama3.3:70b')
    Orchestrator = Orchestrator_Agent(agent_list, 'llama3.3:70b', graph_name, args.chunk_dimension, args.extractor)
    question = load_question("file.txt")
    _run_pipeline(Orchestrator, agent_list, question, use_kg, kg_agents, cft_agents, triplets_in_proposal, val_file, single_val_file, val)
