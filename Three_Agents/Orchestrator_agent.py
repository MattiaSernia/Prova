import ollama
import logging
from agent import Agent
import json


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
    
    def plan(self, task: str="I need to build a bathroom. Which worker roles are required for this task, and which employees are available on April 10th? Please also include each available employee's role.", attempt:int=0) -> dict:
        logging.log(25, f"User asked: {task}")
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
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            plan = json.loads(raw)
            logging.log(25,f"Orchestrator Answer: {raw}")
        except json.JSONDecodeError:
            print(f"  [orchestrator] Warning: could not parse plan JSON.\n  Raw: {raw}\n")
            logging.warning(f"  [orchestrator] Warning: could not parse plan JSON.\n  Raw: {raw}\n Attempt nr: {attempt}")
            logging.warning(f"Orchestrator Answer is not in json format, attempt: {attempt}")
            plan={}
        return plan


    def correct_answer(self, name, answer, question):
        text = f"""### Task: Evaluation
            Does the provided Answer satisfy the original Question asked to the agent "{name}"?

            **Question:** {question}
            **Answer:** {answer}

            ### Instructions:
            - Respond with "TRUE" if the answer is accurate and complete.
            - Respond with "FALSE" if the answer is incorrect, incomplete, or irrelevant.
            - Provide ONLY the word "TRUE" or "FALSE". No other text.

            Result:"""
        logging.log(25,f"Orchestrator correct received: {answer}")
        response=ollama.chat(model=self.model,
                messages=[
                        {'role': 'user', 'content': text},
                    ])
        textual_answer= response['message']['content']
        cleaned=textual_answer.lower().replace(".","").strip()
        if cleaned== "false":
            logging.log(25,"Orchestrator correct answered: FALSE")
            return False
        elif cleaned== "true":
            logging.log(25,"Orchestrator correct answered: TRUE")
            return True
        return False

