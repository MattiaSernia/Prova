import ollama
import logging
from agent import Agent
import json
logger = logging.getLogger(__name__)

class Orchestrator_Agent:
    def __init__(self, agents:list[Agent], model:str):
        self.agents=agents
        self.model=model
        self.memory=[]
        self._asked_question={}

    def _agent_registry(self) -> str:
        """Builds a description of all available agents for the LLM."""
        lines = []
        for agent in self.agents:
            lines.append(f'- "{agent.name}": {agent.description}')
        return "\n".join(lines)
    
    def plan(self, task: str, attempt:int) -> dict:
        logging.info(f"User asked: {task}")
        system = f"""You are an orchestrator. You have access to these specialized agents:
 
        {self._agent_registry()}
        
        Given a user task, respond ONLY with a valid JSON object.
        Keys must be agent names from the list above (use only the agents that are relevant).
        Values must be the specific question to ask that agent.
        Do not include any explanation, markdown, or extra text — raw JSON only.
        
        Example output:
        {{
        "HR Agent": "Which employees are available next week?",
        "PC Prices Agent": "What is the price of the RTX 4070?"
        }}"""
        self.memory.append(system)
        self.memory.append(f"Task: {task}")
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Task: {task}"},
            ],
        )

        raw = response.message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            self.asked_question = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  [orchestrator] Warning: could not parse plan JSON.\n  Raw: {raw}\n")
            logging.info(f"  [orchestrator] Warning: could not parse plan JSON.\n  Raw: {raw}\n Attempt nr: {attempt}")
            if attempt<=4:
                attempt+=1
                self._asked_question  = self.plan(task, attempt)
            else:
                self._asked_question ={}
        logging.info(f"Orchestrator plan: {self._asked_question}")
        self.memory.append(raw)
        return self._asked_question


    def correct_answer(self, name, answer):
        text = f"""Does this answer: {answer} satisfy this question {self._asked_question[name]} you've previously asked to this agent {name}?
        If if it does answer True, else answer False.
        You must answer ONLY with TRUE or FALSE, do not add any explanation.
        === Answer ==="""
        logging.info(f"Orchestrator received: {text}")
        for attempt in range(3):
            response=ollama.chat(model=self.model,
                    messages=[
                            {'role': 'user', 'content': text},
                            *self.memory
                        ])
            textual_answer= response['message']['content']
            logging.info(f"Agent {self.name} answered: {textual_answer}")
            cleaned=textual_answer.lower().replace(".","").strip()
            if cleaned== "false":
                logging.info(cleaned)
                return False
            elif cleaned== "true":
                logging.info(cleaned)
                return True
        return False

