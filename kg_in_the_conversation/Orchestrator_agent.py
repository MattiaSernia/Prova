import logging
import json
from agent import Agent
from custom_graph import Custom_Graph
from rdflib import Namespace
from rdflib.namespace import RDF
from utils import uri_to_label, ollama_chat
import copy


class Orchestrator_Agent:
    def __init__(self, agents:list[Agent], model:str, graph_name:str):
        self.agents=agents
        self.model=model
        self.agent_answer=[]
        self._graph_name=graph_name
        self._cgraph=Custom_Graph(agents, graph_name, model)

    def _agent_registry(self) -> str:
        lines = []
        for agent in self.agents:
            lines.append(f'- "{agent.name}": {agent.description}')
        return "\n".join(lines)

    def _get_requirements_text(self) -> str:
        EX   = Namespace("http://example.org/ontologia#")
        EDGE = "http://example.org/edge/"
        ds   = self._cgraph._ds
        struct: dict = {}
        for subj in ds.subjects(RDF.type, EX.Requirement):
            s_uri = next(ds.objects(subj, RDF.subject), None)
            s = uri_to_label(s_uri) if s_uri else "?"
            pred, obj = "", ""
            for p, o in ds.predicate_objects(subj):
                if str(p).startswith(EDGE):
                    pred = uri_to_label(p)
                    obj  = uri_to_label(o)
                    break
            pri_uri = next(ds.objects(subj, EX.priority), None)
            cat_uri = next(ds.objects(subj, EX.category), None)
            if s not in struct:
                struct[s] = []
            entry = {"predicate": pred, "object": obj}
            if pri_uri:
                entry["priority"] = uri_to_label(pri_uri)
            if cat_uri:
                entry["category"] = uri_to_label(cat_uri)
            struct[s].append(entry)
        return json.dumps(struct, indent=2, ensure_ascii=False)

    def _get_constraints_text(self) -> str:
        EX   = Namespace("http://example.org/ontologia#")
        EDGE = "http://example.org/edge/"
        ds   = self._cgraph._ds
        struct: dict = {}
        for subj in ds.subjects(RDF.type, EX.Constraint):
            s_uri = next(ds.objects(subj, RDF.subject), None)
            s = uri_to_label(s_uri) if s_uri else "?"
            pred, obj = "", ""
            for p, o in ds.predicate_objects(subj):
                if str(p).startswith(EDGE):
                    pred = uri_to_label(p)
                    obj  = uri_to_label(o)
                    break
            ct_uri = next(ds.objects(subj, EX.constraintType), None)
            if s not in struct:
                struct[s] = []
            entry = {"predicate": pred, "object": obj}
            if ct_uri:
                entry["constraintType"] = uri_to_label(ct_uri)
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
            user_content = f"Call for Tenders Knowledge Graph:\n\n{kg_context}"
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
            user_content = f"Call for Tenders:\n\n{task}"

        response = ollama_chat(
            self.model,
            [{"role": "system", "content": system}, {"role": "user", "content": user_content}],
        )

        raw = response["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            plan = json.loads(raw)
            logging.log(25, f"Orchestrator Answer: {raw}")
        except json.JSONDecodeError:
            logging.warning(f"[orchestrator] Could not parse plan JSON (attempt {attempt}). Raw: {raw}")
            plan = {}
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
        response = ollama_chat(self.model, [{'role': 'user', 'content': text}])
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
        agents_context = "\n\n".join(self.agent_answer)

        system = f"""You are a proposal writer for a consortium responding to a call for tenders.
            You must write a complete, professional, and CONCRETE tender proposal.

            The consortium is composed of the following specialized agents (each with their domain):
            {self._agent_registry()}

            ### STRICT RULES:
            - Use ONLY the information provided in the agents' answers and the original tender text.
            - Do NOT invent capabilities, figures, references, or commitments not explicitly mentioned by the agents.
            - If a requirement from the tender is not covered by any agent's answer, explicitly state it is not addressed.
            - Be SPECIFIC: name the exact technologies, tools, frameworks, products, and figures the agents mentioned.
            - Every claim must be traceable to an agent's answer. No filler, no generic statements.

            ### Structure your proposal as follows:
            1. Executive Summary
            2. Understanding of Requirements
            3. Proposed Solution — a single, flowing section that integrates all agents' contributions into
               a coherent description of what the consortium intends to do: what will be built or delivered,
               which technologies and methods will be used, what it will cost, and how constraints will be met.
               Do NOT split this into sub-sections by agent. Write it as one unified narrative.
            4. Unaddressed Requirements (if any requirement from the tender was not covered by any agent)
            5. Conclusion"""

        user_message = f"""=== ORIGINAL CALL FOR TENDERS ===
{task}

=== AGENTS' ANSWERS ===
{agents_context}

Write the proposal now. For each agent's domain, be concrete and specific: name exact technologies, exact costs, exact regulations, exact figures as stated by the agents."""

        response = ollama_chat(
            self.model,
            [{"role": "system", "content": system}, {"role": "user", "content": user_message}],
        )

        proposal = response["message"]["content"]
        logging.log(25, f"Final proposal generated: {proposal}")
        self.agent_answer = []
        return proposal

    def complete(self, graph_in_prompt):
        if graph_in_prompt:
            self._cgraph.add_content("Conversation.log", True, 0)
        else:
            self._ngraph.add_content("Conversation.log", True, self._cgraph.mxgnr())
