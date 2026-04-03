import gui
import logging

loggering, question, graph_name= gui.retrieve_data()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(f"{loggering}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
AGENT_LEVEL = 25  # tra INFO(20) e WARNING(30)
logging.addLevelName(AGENT_LEVEL, "AGENT")

from agent import Agent, generate_Budget, generate_Compliance, generate_Contract, generate_HR, generate_Pipeline
import json
from Orchestrator_agent import Orchestrator_Agent
from custom_graph import Custom_Graph

if __name__ == "__main__":
    att=0
    HR=generate_HR()
    Budget=generate_Budget()
    Pipeline=generate_Pipeline()
    Contract=generate_Contract()
    Compliance=generate_Compliance()
    agent_list=[HR,Budget, Pipeline, Contract, Compliance]
    Orchestrator=Orchestrator_Agent(agent_list,'command-r')
    if question.strip()!="":
        plan=Orchestrator.plan(question)
    else:
        plan=Orchestrator.plan()
    while plan=={}: 
        att+=1
        if question.strip()!="":
            plan=Orchestrator.plan(question)
        else:
            plan=Orchestrator.plan()
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
    graph=Custom_Graph(graph_name, agent_list)
    graph.triplet_extraction(f"{loggering}.log")