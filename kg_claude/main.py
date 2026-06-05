import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)
_log_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_log_formatter)
logger.addHandler(_stream_handler)

AGENT_LEVEL = 25  # tra INFO(20) e WARNING(30)
logging.addLevelName(AGENT_LEVEL, "AGENT")

def _setup_output_dir(mode_folder: str, format_folder: str, extractor: str, exp_name: str) -> str:
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "experiments")
    parts = [base, mode_folder] + ([format_folder, extractor] if format_folder else []) + [exp_name]
    out  = os.path.join(*parts)
    os.makedirs(out, exist_ok=True)
    fh = logging.FileHandler(os.path.join(out, "Conversation.log"), mode="w", encoding="utf-8")
    fh.setFormatter(_log_formatter)
    logger.addHandler(fh)
    return out

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
    mode.add_argument("--c-null", action="store_true", help="Run without knowledge graph in prompt")
    mode.add_argument("--c-oa", action="store_true", help="Pass KG to agents in addition to orchestrator")
    mode.add_argument("--c-oap", action="store_true", help="Pass KG to agents and include extracted triplets in proposal")
    mode.add_argument("--c-op", action="store_true", help="Pass KG to orchestrator only, CFT text to agents")
    parser.add_argument(
        "--kg-format",
        choices=["json", "turtle-light"],
        default="turtle-light",
        help="KG serialization format in prompts (default: turtle-light)",
    )
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

    fmt = "TURTLE" if args.kg_format == "turtle-light" else "JSON"

    if args.c_null:
        use_kg, kg_agents, cft_agents, triplets_in_proposal = False, False, False, False
        mode_folder, exp_prefix = "C_null", "C_null"
        graph_base, single_val_base = "Total_nokg", "single_validation_nokg.txt"
    elif args.c_oa:
        use_kg, kg_agents, cft_agents, triplets_in_proposal = True, True, False, False
        mode_folder, exp_prefix = "C_{OA}", "C_{OA}"
        graph_base, single_val_base = "Total_kgagents", "single_validation_kgagents.txt"
    elif args.c_oap:
        use_kg, kg_agents, cft_agents, triplets_in_proposal = True, True, False, True
        mode_folder, exp_prefix = "C_{OAP}", "C_{OAP}"
        graph_base, single_val_base = "Total_kgagents_tri", "single_validation_kgagents_tri.txt"
    elif args.c_op:
        use_kg, kg_agents, cft_agents, triplets_in_proposal = True, False, True, True
        mode_folder, exp_prefix = "C_{OP}", "C_{OP}"
        graph_base, single_val_base = "Total_kgcft", "single_validation_kgcft.txt"
    else:
        use_kg, kg_agents, cft_agents, triplets_in_proposal = True, False, False, False
        mode_folder, exp_prefix = "C_{O}", "C_{O}"
        graph_base, single_val_base = "Total", "single_validation_kg.txt"

    exp_name  = f"{exp_prefix}_{args.chunk_dimension}"
    if args.c_null:
        out_dir = _setup_output_dir(mode_folder, "", "", exp_name)
    else:
        out_dir = _setup_output_dir(mode_folder, fmt, args.extractor, exp_name)
    graph_name    = os.path.join(out_dir, graph_base)
    single_val_file = os.path.join(out_dir, single_val_base)
    val_file      = os.path.join(out_dir, single_val_base.replace("single_", ""))

    val = va.Validation("llama3.3:70b", 0)
    agent_list = create_all_agents('llama3.3:70b')
    Orchestrator = Orchestrator_Agent(agent_list, 'llama3.3:70b', graph_name, args.chunk_dimension, args.extractor, args.kg_format)
    question = load_question("file.txt")
    _run_pipeline(Orchestrator, agent_list, question, use_kg, kg_agents, cft_agents, triplets_in_proposal, val_file, single_val_file, val)
