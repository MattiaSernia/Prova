import ollama
import logging
from agent import Agent
import json


class Orchestrator_Agent:
    def __init__(self, agents:list[Agent], model:str):
        self.agents=agents
        self.model=model
        self.memory=[]

    def _agent_registry(self) -> str:
        """Builds a description of all available agents for the LLM."""
        lines = []
        for agent in self.agents:
            lines.append(f'- "{agent.name}": {agent.description}')
        return "\n".join(lines)
    
    def plan(self, task: str="I need to build a bathroom. Which worker roles are required for this task, and which employees are available on April 10th? Please also include each available employee's role.", attempt:int=0) -> dict:
        logging.log(25, f"User asked: {task}")
        system = f"""You are an orchestrator managing a consortium responding to a public call for tenders.
You have access to these specialized agents:
{self._agent_registry()}

### Your role:
The user will provide you with the full text of a Call for Tenders document.
Your job is to read it carefully and dispatch targeted, self-contained questions
to the relevant agents so that together they can produce a complete bid response.

### How to read the Call for Tenders:
- Extract the client's requirements, constraints, and evaluation criteria.
- Identify which sections are relevant to each agent's domain.
- For each relevant agent, formulate a precise question that embeds all the details
  that agent needs — do not assume the agent will read the original document.

### Rules:
- Respond ONLY with a valid JSON object.
- Keys must be agent names from the list above (use only agents relevant to this tender).
- Values must be specific, self-contained questions derived from the Call for Tenders text.
- Each question must include the relevant figures, constraints and requirements extracted
  from the document (e.g. budget amount, SLA targets, regulatory requirements, deadlines).
- Do not include any explanation, markdown, or extra text — raw JSON only.
- Questions will be asked in parallel, so each must be fully self-contained.

Example output format:
{{
    "Technical Architect Agent": "The client requires <specific SLA>, <specific integration>, and <specific hosting constraint>. What architecture do you propose and is it feasible given our capabilities?",
    "Budget Agent": "The total contract value is <X EUR> over <Y years>. Are we financially eligible to bid, and what is the projected margin?",
    "Legal Agent": "The tender is governed by <specific law/framework>. Are we eligible to bid and what legal risks should be flagged?"
}}"""
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Call for Tenders:\n\n{task}"},
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
        self.memory.append({agent_name:name, agent_answer:answer})
        textual_answer= response['message']['content']
        cleaned=textual_answer.lower().replace(".","").strip()
        if cleaned== "false":
            logging.log(25,"Orchestrator correct answered: FALSE")
            return False
        elif cleaned== "true":
            logging.log(25,"Orchestrator correct answered: TRUE")
            return True
        return False

    

