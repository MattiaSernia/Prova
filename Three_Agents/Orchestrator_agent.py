import ollama
import logging
from agent import Agent
import json
logger = logging.getLogger(__name__)

class Orchestrator_Agent:
    def __init__(self, agents:list[Agent], model:str):
        self.agents=agents
        self.model=model

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
        
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Task: {task}"},
            ],
        )

        raw = response.message.content.strip()
        # Strip markdown fences if the model wraps in ```json ... ```
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            plan = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  [orchestrator] Warning: could not parse plan JSON.\n  Raw: {raw}\n")
            logging.info(f"  [orchestrator] Warning: could not parse plan JSON.\n  Raw: {raw}\n Attempt nr: {attempt}")
            if attempt<=4:
                attempt+=1
                plan = plan(task, attempt)
            else:
                plan={}
        logging.info(f"Orchestrator plan: {plan}")
        return plan