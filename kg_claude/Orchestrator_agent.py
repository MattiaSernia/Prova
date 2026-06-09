import logging
import json
from agent import Agent
from custom_graph import Custom_Graph
from rdflib import Namespace
from rdflib.namespace import RDF, PROV
from utils import uri_to_label, ollama_chat
from mxg import Message


class Orchestrator_Agent:
    def __init__(self, agents:list[Agent], model:str, graph_name:str, chunk_dimension:int, extractor_type:str="llama", kg_format:str="turtle-light", no_schema:bool=False):
        self.agents=agents
        self.model=model
        self.agent_answer=[]
        self._graph_name=graph_name
        self._kg_format=kg_format
        self._cgraph=Custom_Graph(agents, graph_name, model, chunk_dimension, extractor_type, no_schema)

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
    
    def _get_triplets_text(self) -> str:
        EX   = Namespace("http://example.org/ontologia#")
        EDGE = "http://example.org/edge/"
        ds   = self._cgraph._ds

        def local(uri):
            s = str(uri)
            return s.rsplit("#", 1)[-1] if "#" in s else s.rsplit("/", 1)[-1]

        lines = []
        for subj in ds.subjects(RDF.type, EX.Triplet):
            parts = ["a ex:Triplet"]
            s_uri = next(ds.objects(subj, RDF.subject), None)
            if s_uri:
                parts.append(f"rdf:subject node:{local(s_uri)}")
            for p, o in ds.predicate_objects(subj):
                if str(p).startswith(EDGE):
                    parts.append(f"edge:{local(p)} node:{local(o)}")
            for _, _, _, ctx in ds.quads((subj, RDF.type, EX.Triplet, None)):
                chunk_uri = next(ds.objects(ctx.identifier, PROV.wasDerivedFrom), None)
                if chunk_uri:
                    msg_uri = next(ds.objects(chunk_uri, PROV.wasDerivedFrom), None)
                    if msg_uri:
                        agent_uri = next(ds.objects(msg_uri, PROV.wasAttributedTo), None)
                        if agent_uri:
                            parts.append(f"ex:extractedBy node:{local(agent_uri)}")
                break
            lines.append(f"tri:{local(subj)} " + " ; ".join(parts) + " .")
        return "\n".join(lines)

    def _get_triplets_json(self) -> str:
        EX   = Namespace("http://example.org/ontologia#")
        EDGE = "http://example.org/edge/"
        ds   = self._cgraph._ds
        struct: dict = {}
        for subj in ds.subjects(RDF.type, EX.Triplet):
            s_uri = next(ds.objects(subj, RDF.subject), None)
            s = uri_to_label(s_uri) if s_uri else "?"
            pred, obj = "", ""
            for p, o in ds.predicate_objects(subj):
                if str(p).startswith(EDGE):
                    pred = uri_to_label(p)
                    obj  = uri_to_label(o)
                    break
            agent_name = "unknown"
            for _, _, _, ctx in ds.quads((subj, RDF.type, EX.Triplet, None)):
                chunk_uri = next(ds.objects(ctx.identifier, PROV.wasDerivedFrom), None)
                if chunk_uri:
                    msg_uri = next(ds.objects(chunk_uri, PROV.wasDerivedFrom), None)
                    if msg_uri:
                        agent_uri = next(ds.objects(msg_uri, PROV.wasAttributedTo), None)
                        if agent_uri:
                            agent_name = uri_to_label(agent_uri).replace("_", " ").title()
                break
            if agent_name not in struct:
                struct[agent_name] = []
            struct[agent_name].append({"subject": s, "predicate": pred, "object": obj})
        return json.dumps(struct, indent=2, ensure_ascii=False)

    def _get_kg_turtle_light(self) -> str:
        EX   = Namespace("http://example.org/ontologia#")
        EDGE = "http://example.org/edge/"
        ds   = self._cgraph._ds

        def local(uri):
            s = str(uri)
            return s.rsplit("#", 1)[-1] if "#" in s else s.rsplit("/", 1)[-1]

        lines = []
        for subj in ds.subjects(RDF.type, EX.Requirement):
            parts = ["a ex:Requirement"]
            s_uri = next(ds.objects(subj, RDF.subject), None)
            if s_uri:
                parts.append(f"rdf:subject node:{local(s_uri)}")
            for p, o in ds.predicate_objects(subj):
                if str(p).startswith(EDGE):
                    parts.append(f"edge:{local(p)} node:{local(o)}")
            pri_uri = next(ds.objects(subj, EX.priority), None)
            if pri_uri:
                parts.append(f"ex:priority ex:{local(pri_uri)}")
            cat_uri = next(ds.objects(subj, EX.category), None)
            if cat_uri:
                parts.append(f"ex:category ex:{local(cat_uri)}")
            lines.append(f"req:{local(subj)} " + " ; ".join(parts) + " .")

        for subj in ds.subjects(RDF.type, EX.Constraint):
            parts = ["a ex:Constraint"]
            s_uri = next(ds.objects(subj, RDF.subject), None)
            if s_uri:
                parts.append(f"rdf:subject node:{local(s_uri)}")
            for p, o in ds.predicate_objects(subj):
                if str(p).startswith(EDGE):
                    parts.append(f"edge:{local(p)} node:{local(o)}")
            ct_uri = next(ds.objects(subj, EX.constraintType), None)
            if ct_uri:
                parts.append(f"ex:constraintType ex:{local(ct_uri)}")
            lines.append(f"con:{local(subj)} " + " ; ".join(parts) + " .")

        return "\n".join(lines)

    def get_kg_context(self) -> str:
        if self._kg_format == "json":
            return (
                "=== REQUIREMENTS (JSON) ===\n"
                f"{self._get_requirements_text()}\n"
                "=== END REQUIREMENTS ===\n\n"
                "=== CONSTRAINTS (JSON) ===\n"
                f"{self._get_constraints_text()}\n"
                "=== END CONSTRAINTS ==="
            )
        return (
            "=== KNOWLEDGE GRAPH (Turtle Light) ===\n"
            f"{self._get_kg_turtle_light()}\n"
            "=== END KNOWLEDGE GRAPH ==="
        )

    def add_message(self, mxg: Message):
        self._cgraph.add_message(mxg)

    def plan(self, task: str="", attempt:int=0, graph_in_prompt:bool=True, no_text:bool=False) -> dict:
        if attempt==0:
            logging.log(25, f"User asked: {task}")
            self._cgraph.add_message(Message.now(task, "User", "question", "default"))

        if graph_in_prompt:
            kg_context = self.get_kg_context()

            system = f"""You are an orchestrator managing a consortium responding to a public call for tenders.
                You have access to these specialized agents:
                {self._agent_registry()}

                ### CRITICAL CONSTRAINT — READ THIS FIRST:
                Each agent operates in COMPLETE ISOLATION. They have NO access to the Call for Tenders document.
                They can only answer based on their own internal knowledge (their company role and data).
                If your question does not contain the relevant facts from the tender, the agent will answer
                in a vacuum and produce a useless generic response.
                YOUR JOB IS TO BE THEIR EYES: copy every relevant requirement, figure, constraint and
                deadline from both the knowledge graph and the original tender text directly into the
                question you write for that agent.

                ### Your role:
                The user will provide you with two complementary sources:
                1. A structured Knowledge Graph (KG) extracted from the Call for Tenders, serialized in
                   {"Turtle Light format (simplified Turtle: no prefix declarations, subject-factorised, one line per subject)" if self._kg_format == "turtle-light" else "JSON format"}.
                   It contains two types of nodes:
                   - ex:Requirement — high-level business needs and goals the client wants to achieve.
                   - ex:Constraint  — conditions, limits and rules under which the solution must operate
                   (technical bounds, budget limits, regulatory requirements, infrastructure rules, etc.).
                2. The full original Call for Tenders text.
                Use the KG as the primary structured reference and the tender text to fill in any detail,
                context or nuance that the KG may not have captured.
                Your job is to dispatch targeted, self-contained questions to the relevant agents so that
                together they can produce a complete bid response.

                ### How to build each question:
                1. Identify which requirements and constraints from the KG are relevant to that agent's domain.
                2. Cross-reference with the tender text to capture any additional figures, context or nuance.
                3. Extract and include the specific requirements, figures, constraints and deadlines
                that this agent needs to know.
                4. End with a precise, answerable question about our company's capabilities or risks.

                ### Rules:
                - Respond ONLY with a valid JSON object.
                - Keys must be agent names from the list above (use only agents relevant to this tender).
                - Values must be specific, self-contained questions derived from both sources.
                - Each question MUST quote the exact figures and constraints
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
            if no_text:
                user_content = f"=== CALL FOR TENDERS KNOWLEDGE GRAPH ===\n\n{kg_context}"
            else:
                user_content = (
                    f"=== CALL FOR TENDERS KNOWLEDGE GRAPH ===\n\n{kg_context}\n\n"
                    f"=== ORIGINAL CALL FOR TENDERS TEXT ===\n\n{task}"
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

        self._cgraph.add_message(Message.now(raw, "Orchestrator", "answer", "default"))
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

    def propose(self, task: str, use_triplets: bool = False, no_text: bool = False) -> str:
        agents_context = "" if no_text else "\n\n".join(self.agent_answer)

        system = """You are writing a bid response on behalf of a consortium.

Your only job: go through every requirement and constraint in the Call for Tenders and state, point by point, exactly how the consortium meets it — or explicitly flag that it is not covered.

Rules (no exceptions):
- Ground every claim in the agents' answers. If an agent did not say it, do not write it.
- Copy exact figures, technologies, costs, regulations, and deadlines from the agents' answers.
- No introductions, no conclusions, no summaries. Start directly with the first requirement.
- No filler sentences ("we are pleased to", "our team is committed to", etc.).
- If a requirement has no coverage in the agents' answers, skip it entirely.
- Output only the proposal text."""

        triplets_section = ""
        kg_section = ""
        if use_triplets:
            triplets_content = self._get_triplets_json() if self._kg_format == "json" else self._get_triplets_text()
            triplets_section = f"\n\n=== TRIPLETS EXTRACTED FROM AGENT CONVERSATIONS ===\n{triplets_content}\n=== END TRIPLETS ==="
            kg_section = (
                f"\n\n=== REQUIREMENTS AND CONSTRAINTS — address and respect each one ===\n"
                f"{self.get_kg_context()}\n"
                f"=== END REQUIREMENTS AND CONSTRAINTS ==="
            )

        cft_section = "" if no_text else f"=== CALL FOR TENDERS ===\n{task}\n\n"
        agents_section = "" if not agents_context else f"=== AGENTS' ANSWERS ===\n{agents_context}"

        user_message = (
            f"{cft_section}"
            f"{agents_section}"
            f"{triplets_section}"
            f"{kg_section}\n\n"
            "Address each requirement and constraint listed above in order. "
            "For each one, state exactly what the consortium offers, using only what the agents said."
        )

        response = ollama_chat(
            self.model,
            [{"role": "system", "content": system}, {"role": "user", "content": user_message}],
        )

        proposal = response["message"]["content"]
        logging.log(25, f"Final proposal generated: {proposal}")
        self.agent_answer = []
        return proposal
