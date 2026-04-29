import ollama
import logging
import json
from agent import Agent
from custom_graph import Custom_Graph
from rdflib import Namespace
from rdflib.namespace import RDF
import copy


class Orchestrator_Agent:
    def __init__(self, agents:list[Agent], model:str, graph_name:str):
        self.agents=agents
        self.model=model
        self.agent_answer=[]
        self._graph_name=graph_name
        self._cgraph=Custom_Graph(agents, graph_name)

    def _agent_registry(self) -> str:
        lines = []
        for agent in self.agents:
            lines.append(f'- "{agent.name}": {agent.description}')
        return "\n".join(lines)

    @staticmethod
    def _local(uri) -> str:
        s = str(uri)
        s = s.rsplit("#", 1)[-1] if "#" in s else s.rsplit("/", 1)[-1]
        return s.replace("_", " ")

    def _get_requirements_text(self) -> str:
        EX   = Namespace("http://example.org/ontologia#")
        EDGE = "http://example.org/edge/"
        ds   = self._cgraph._ds
        struct: dict = {}
        for subj in ds.subjects(RDF.type, EX.Requirement):
            s_uri = next(ds.objects(subj, RDF.subject), None)
            s = self._local(s_uri) if s_uri else "?"
            pred, obj = "", ""
            for p, o in ds.predicate_objects(subj):
                if str(p).startswith(EDGE):
                    pred = self._local(p)
                    obj  = self._local(o)
                    break
            pri_uri = next(ds.objects(subj, EX.priority), None)
            cat_uri = next(ds.objects(subj, EX.category), None)
            if s not in struct:
                struct[s] = []
            entry = {"predicate": pred, "object": obj}
            if pri_uri:
                entry["priority"] = self._local(pri_uri)
            if cat_uri:
                entry["category"] = self._local(cat_uri)
            struct[s].append(entry)
        return json.dumps(struct, indent=2, ensure_ascii=False)

    def _get_constraints_text(self) -> str:
        EX   = Namespace("http://example.org/ontologia#")
        EDGE = "http://example.org/edge/"
        ds   = self._cgraph._ds
        struct: dict = {}
        for subj in ds.subjects(RDF.type, EX.Constraint):
            s_uri = next(ds.objects(subj, RDF.subject), None)
            s = self._local(s_uri) if s_uri else "?"
            pred, obj = "", ""
            for p, o in ds.predicate_objects(subj):
                if str(p).startswith(EDGE):
                    pred = self._local(p)
                    obj  = self._local(o)
                    break
            ct_uri = next(ds.objects(subj, EX.constraintType), None)
            if s not in struct:
                struct[s] = []
            entry = {"predicate": pred, "object": obj}
            if ct_uri:
                entry["constraintType"] = self._local(ct_uri)
            struct[s].append(entry)
        return json.dumps(struct, indent=2, ensure_ascii=False)
    
    def plan(self, task: str="", attempt:int=0, graph_in_prompt:bool=True) -> dict:
        if attempt==0 and graph_in_prompt:
            logging.log(25, f"User asked: {task}")
            self._cgraph.add_content("Conversation.log", False, 0)
            self._ngraph=copy.deepcopy(self._cgraph)
            self._ngraph.rename(f"{self._graph_name}_nokg")

        if graph_in_prompt:
            req_text = self._get_requirements_text()
            con_text = self._get_constraints_text()
            kg_context = (
                "=== REQUIREMENTS (structured JSON) ===\n"
                f"{req_text}\n"
                "=== END REQUIREMENTS ===\n\n"
                "=== CONSTRAINTS (structured JSON) ===\n"
                f"{con_text}\n"
                "=== END CONSTRAINTS ==="
            )

            system = f"""You are an orchestrator managing a consortium responding to a public call for tenders.
                You have access to these specialized agents:
                {self._agent_registry()}

                ### CRITICAL CONSTRAINT — READ THIS FIRST:
                Each agent operates in COMPLETE ISOLATION. They have NO access to the Call for Tenders document.
                They can only answer based on their own internal knowledge (their company role and data).
                If your question does not contain the relevant facts from the tender, the agent will answer
                in a vacuum and produce a useless generic response.
                YOUR JOB IS TO BE THEIR EYES: copy every relevant requirement, figure, constraint and
                deadline from the knowledge graph directly into the question you write for that agent.

                ### Your role:
                The user will provide you with a structured Knowledge Graph (KG) extracted from a Call for
                Tenders document. The KG has two sections:
                - REQUIREMENTS: high-level business needs and goals the client wants to achieve.
                - CONSTRAINTS: conditions, limits and rules under which the solution must operate
                (technical bounds, budget limits, regulatory requirements, infrastructure rules, etc.).
                Your job is to read this KG carefully and dispatch targeted, self-contained questions
                to the relevant agents so that together they can produce a complete bid response.

                ### How to build each question:
                1. Identify which requirements and constraints from the KG are relevant to that agent's domain.
                2. Extract and include the specific requirements, figures, constraints and deadlines
                that this agent needs to know.
                3. End with a precise, answerable question about our company's capabilities or risks.

                ### Rules:
                - Respond ONLY with a valid JSON object.
                - Keys must be agent names from the list above (use only agents relevant to this tender).
                - Values must be specific, self-contained questions derived from the Knowledge Graph.
                - Each question MUST quote the exact figures and constraints from the KG
                (budget amounts, SLA targets, regulatory frameworks, technical specs, deadlines).
                - Do not include any explanation, markdown, or extra text — raw JSON only.
                - Questions will be asked in parallel, so each must be fully self-contained.
                - USE the right name for the Agents, do not modify them

                ### BAD example (never do this — agent has no context to answer):
                {{
                    "Budget Agent": "Given our budget constraints, can we deliver this project?"
                }}

                ### GOOD example (agent has everything it needs to answer):
                {{
                    "Budget Agent": "The client's global budget is 3 million EUR over 4 years. Annual operating costs must remain controlled. The tender requires a pilot phase followed by progressive rollout. Given our pricing model and current financial position, what is our projected margin on this contract, and are there cost-optimization strategies we can propose?"
                }}

                Full example format:
                {{
                    "Technical Architect Agent": "The client requires: response time < 2 seconds, 99.9% availability, API integration with civil-status and town-planning software, EDM and user directories. Hosting must be on SecNumCloud-certified infrastructure within the EU. No dependency on non-European suppliers. Can our current stack meet these requirements, and what architecture do you propose?",
                    "Budget Agent": "The total contract value is 3M EUR over 4 years. Annual exploitation costs must stay within municipal budget capacity. The client expects cost optimisation without sacrificing quality. Are we financially eligible to bid, and what is the projected margin?",
                    "Legal Agent": "The tender requires strict GDPR compliance (EU-only hosting, no data transfer outside EU, encryption of sensitive data). All AI recommendations must be explainable post-hoc. No automated decision is allowed without explicit agent validation. What legal risks should we flag, and are we compliant?"
                }}"""
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Call for Tenders Knowledge Graph:\n\n{kg_context}"},
                ],
            )
        else:
            system =  f"""You are an orchestrator managing a consortium responding to a public call for tenders.
                You have access to these specialized agents:
                {self._agent_registry()}
    
                ### CRITICAL CONSTRAINT — READ THIS FIRST:
                Each agent operates in COMPLETE ISOLATION. They have NO access to the Call for Tenders document.
                They can only answer based on their own internal knowledge (their company role and data).
                If your question does not contain the relevant facts from the tender, the agent will answer
                in a vacuum and produce a useless generic response.
                YOUR JOB IS TO BE THEIR EYES: copy every relevant requirement, figure, constraint and
                deadline from the tender directly into the question you write for that agent.
    
                ### Your role:
                The user will provide you with the full text of a Call for Tenders document.
                Your job is to read it carefully and dispatch targeted, self-contained questions
                to the relevant agents so that together they can produce a complete bid response.
    
                ### How to build each question:
                1. Identify which sections of the tender are relevant to that agent's domain.
                2. Extract and paste the specific requirements, numbers, constraints and deadlines
                that this agent needs to know.
                3. End with a precise, answerable question about our company's capabilities or risks.
    
                ### Rules:
                - Respond ONLY with a valid JSON object.
                - Keys must be agent names from the list above (use only agents relevant to this tender).
                - Values must be specific, self-contained questions derived from the Call for Tenders text.
                - Each question MUST quote the exact figures and constraints from the tender
                (budget amounts, SLA targets, regulatory frameworks, technical specs, deadlines).
                - Do not include any explanation, markdown, or extra text — raw JSON only.
                - Questions will be asked in parallel, so each must be fully self-contained.
                - USE the right name for the Agents, do not modify them
    
                ### BAD example (never do this — agent has no context to answer):
                {{
                    "Budget Agent": "Given our budget constraints, can we deliver this project?"
                }}
    
                ### GOOD example (agent has everything it needs to answer):
                {{
                    "Budget Agent": "The client's global budget is 3 million EUR over 4 years. Annual operating costs must remain controlled. The tender requires a pilot phase followed by progressive rollout. Given our pricing model and current financial position, what is our projected margin on this contract, and are there cost-optimization strategies we can propose?"
                }}
    
                Full example format:
                {{
                    "Technical Architect Agent": "The client requires: response time < 2 seconds, 99.9% availability, API integration with civil-status and town-planning software, EDM and user directories. Hosting must be on SecNumCloud-certified infrastructure within the EU. No dependency on non-European suppliers. Can our current stack meet these requirements, and what architecture do you propose?",
                    "Budget Agent": "The total contract value is 3M EUR over 4 years. Annual exploitation costs must stay within municipal budget capacity. The client expects cost optimisation without sacrificing quality. Are we financially eligible to bid, and what is the projected margin?",
                    "Legal Agent": "The tender requires strict GDPR compliance (EU-only hosting, no data transfer outside EU, encryption of sensitive data). All AI recommendations must be explainable post-hoc. No automated decision is allowed without explicit agent validation. What legal risks should we flag, and are we compliant?"
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
        self.agent_answer.append(f"=== {name} ===\n{answer}")
        textual_answer= response['message']['content']
        cleaned=textual_answer.lower().replace(".","").strip()
        if cleaned== "false":
            logging.log(25,"Orchestrator correct answered: FALSE")
            return False
        elif cleaned== "true":
            logging.log(25,"Orchestrator correct answered: TRUE")
            return True
        return False

    def propose(self, task: str) -> str:

        
        agents_context = "\n\n".join(
            self.agent_answer 
        )

        system = """You are a proposal writer for a consortium responding to a call for tenders.
            You must write a complete, professional tender proposal.

            ### STRICT RULES:
            - Use ONLY the information provided in the agents' answers and the original tender text.
            - Do NOT invent capabilities, figures, references, or commitments not explicitly mentioned.
            - If a requirement from the tender is not covered by any agent's answer, explicitly state it is not addressed.
            - Do not add assumptions, general knowledge, or filler content.

            ### Structure your proposal with these sections:
            1. Executive Summary
            2. Understanding of Requirements
            3. Proposed Solution (per domain: technical, legal, financial, etc.)
            4. Compliance & Certifications
            5. Budget Overview
            6. Conclusion"""

        user_message = f"""=== ORIGINAL CALL FOR TENDERS ===
            {task}

            === AGENTS' ANSWERS ===
            {agents_context}

            Now write the proposal."""

        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ]
        )
        
        proposal = response.message.content
        logging.log(25, f"Final proposal generated: {proposal}")
        self.agent_answer=[]
        return proposal

    def complete(self, graph_in_prompt):
        if graph_in_prompt:
            self._cgraph.add_content("Conversation.log", True, 0)
        else:
            self._ngraph.add_content("Conversation.log", True, self._cgraph.mxgnr()-1)
