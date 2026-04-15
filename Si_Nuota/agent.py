import ollama
import logging
import json


class Agent:

    def __init__(self, name: str, role: str, context_file: str, description:str ,model: str = "command-r"):
        self.name = name
        self.role = role
        self.data = self._load_context(context_file)
        self.model = model
        self.memory = []
        self.description=description

    # ---------- internal helpers ----------

    @staticmethod
    def _load_context(path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _system_prompt(self) -> str:
        return (
            f'You are "{self.name}", a specialised assistant acting as {self.role} '
            f"for the company.\n\n"
            "You must answer ONLY using the data provided below as your context. "
            "This data describes your company's capabilities, constraints, history "
            "and resources from your role's perspective.\n"
            "If a question requires information not present in your context, "
            "explicitly state that you do not have that information — never invent it.\n\n"
            "Be precise, factual and concise. Do not use bullet lists, tables or "
            "markdown formatting.\n\n"
            "=== YOUR CONTEXT (company knowledge) ===\n"
            f"{json.dumps(self.data, indent=2, ensure_ascii=False)}\n"
            "=== END OF CONTEXT ==="
        )

    def _chat(self, user_message: str, use_memory: bool = True) -> str:
        messages = [{"role": "system", "content": self._system_prompt()}]
        if use_memory:
            self.memory.append({"role": "user", "content": user_message})
            messages.extend(self.memory)
        else:
            messages.append({"role": "user", "content": user_message})

        response = ollama.chat(model=self.model, messages=messages)
        text = response["message"]["content"]

        if use_memory:
            self.memory.append({"role": "assistant", "content": text})
        return text

    # ---------- public API ----------

    def answer(self, message:str)-> str:
        self.memory.append({"role":"user", "content": message})
        logging.log(25, f"{self.name} received: {message}")
        response=ollama.chat(
            model=self.model,
            messages=[
                {'role':'system', 'content':self._system_prompt()},
                *self.memory
            ]
        )
        textual_answer= response['message']['content']
        self.memory.append({"role": "assistant", "content": textual_answer})
        logging.log(25, f"{self.name} answered: {textual_answer}")
        return(textual_answer)

    def assess(self, tender: str) -> str:
        """
        Receive a call for tenders and report, from this agent's role, WHAT CAN BE DONE
        given ONLY the data available in the agent's context.
 
        This is not a proposal or a sales pitch — it is a factual feasibility report:
        the agent inventories, from its own knowledge, the capabilities, resources,
        certifications, references or constraints that are relevant to the tender,
        and states what is feasible, what is partially feasible and what is not
        covered at all.
        """
        instruction = (
            "You have received the following call for tenders (cahier des charges).\n"
            f"Your task — from your role's perspective ({self.role}) — is NOT to "
            "write a proposal, NOT to sell, NOT to invent a solution.\n\n"
            "Your task is to report, FACTUALLY and using ONLY the data in your "
            "context, what can be done to address this tender.\n\n"
            "For every relevant requirement of the tender, tell me:\n"
            "1. What is available in your context that is directly relevant "
            "(capabilities, resources, certifications, past references, numbers, "
            "constraints). Cite the exact elements from your context.\n"
            "2. Whether the requirement is FULLY COVERED, PARTIALLY COVERED, or "
            "NOT COVERED by your context.\n"
            "3. If partial: what exactly is missing, and what exists.\n"
            "4. If not covered: say so explicitly. Do NOT guess, do NOT extrapolate, "
            "do NOT invent capabilities your context does not mention.\n\n"
            "Also list any information in your context that is relevant to the tender "
            "even if not tied to a specific requirement (useful constraints, limits, "
            "trade-offs, known risks).\n\n"
            "Stay strictly within your role. Ignore requirements that are outside "
            "your scope — simply state they are outside your scope.\n\n"
            "=== CALL FOR TENDERS ===\n"
            f"{tender}\n"
            "=== END OF CALL FOR TENDERS ===\n\n"
            "Now produce your factual feasibility report."
        )
        #logging.log(25, f"{self.name} received tender ({len(tender)} chars)")
        text = self._chat(instruction, use_memory=True)
        #logging.log(25, f"{self.name} assessment: {text}")
        return text

    def retry(self, message: str, previous_answer: str) -> str:
        """Re-ask the same question after a failed coherency check,
        telling the agent explicitly that its previous answer was wrong."""
        feedback = (
            "Your previous answer was rejected because it contains information "
            "that is inconsistent with, or not supported by, your context data. "
            "Do NOT invent figures, capabilities or facts that are not explicitly "
            "present in your context. Re-read your context carefully and answer "
            "the original question again, this time strictly based on what your "
            "context contains. If the information is not there, say so explicitly."
        )
        # The previous answer is already in memory (appended by answer()).
        # We add the feedback as a user turn so the model sees it before re-answering.
        self.memory.append({"role": "user", "content": feedback})
        return self.answer(message)

    def coherency_check(self, text: str) -> bool:
        """Check whether `text` is consistent with this agent's context."""
        prompt = (
            "Role: Coherency Checker\n"
            "Verify if the provided Data is consistent with your Context.\n\n"
            "Decision Criteria:\n"
            '- Return "TRUE" if the Data contains NO errors, contradictions or '
            "hallucinations relative to the Context.\n"
            '- Return "FALSE" if even a single detail is inconsistent or incorrect.\n\n'
            f"Data to Verify:\n{text}\n\n"
            'Constraint: Respond ONLY with "TRUE" or "FALSE". No explanation.\n\nResult:'
        )
        logging.log(25, f"{self.name} coherency check on: {text}")
        for _ in range(3):
            answer = self._chat(prompt, use_memory=False)
            cleaned = answer.lower().replace(".", "").strip()
            logging.log(25, f"{self.name} coherency answered: {cleaned}")
            if cleaned == "true":
                return True
            if cleaned == "false":
                return False
        return False


# =====================================================================
# Agent registry + generic factory
# =====================================================================
#
# All role-specific knowledge (Milan HQ, ISO 27001, EcoVadis Silver, ...) lives
# in the JSON context files — NOT hardcoded in Python. The role string here is
# only a short label used in the prompt; the real expertise comes from the JSON.
# To add a new agent, just add an entry below and a JSON context file.

AGENT_REGISTRY = {
    "coordinator": {
        "name": "ProjectCoordinator Agent",
        "role": "project coordinator and consortium lead",
        "context_file": "contexts/Coordinator_Agent.json",
        "description":("Coordinates the consortium and consolidates all agent contributions into a coherent tender response for Nexus Engineering S.r.l. "
            "Knows the company's PM methodologies, past public sector references, consortium partners, available capacity, "
            "and governance practices as of 2024. Responsible for detecting contradictions and maintaining decision traceability.")

    },
    "architect": {
        "name": "TechnicalArchitect Agent",
        "role": "technical architect",
        "context_file": "contexts/Architect_Agent.json",
        "description":(
            "Designs and owns the technical architecture for Nexus Engineering S.r.l. tender responses. "
            "Knows the full technology stack (LLMs, RAG, cloud, integration, security), performance benchmarks, "
            "sovereign hosting options, and technical constraints as of 2024."
        )
    },
    "security": {
        "name": "SecurityCompliance Agent",
        "role": "security and compliance officer",
        "context_file": "contexts/Compliance_Agent.json",
        "description":(
            "Owns the security and regulatory compliance posture for Nexus Engineering S.r.l. tender responses. "
            "Knows the company's certifications, GDPR instruments, AI security controls, audit capabilities, "
            "and experience with EU regulatory frameworks (GDPR, EU AI Act, RGS, SecNumCloud, NIS2) as of 2024."
        )
    },
    "legal": {
        "name": "Legal Agent",
        "role": "legal counsel",
        "context_file": "contexts/Legal_Agent.json",
        "description":(
            "Manages legal eligibility, contractual compliance, and regulatory risk for Nexus Engineering S.r.l. tender responses. "
            "Knows the company's legal standing, procurement experience across EU jurisdictions, IP model, insurance, "
            "standard contractual clauses, and AI regulatory posture (GDPR, EU AI Act) as of 2024."
        )
    },
    "budget": {
        "name": "Budget Agent",
        "role": "financial manager",
        "context_file": "contexts/Budget_Agent.json",
        "description": (
            "Manages financial eligibility, cost estimation, and margin analysis for Nexus Engineering S.r.l. tender responses. "
            "Knows the company's financials, active project budgets, daily rates, overhead, cash position, "
            "tender eligibility thresholds, and cost sensitivity parameters as of 2024."
        ),
    },
    "ai": {
        "name": "AIInnovation Agent",
        "role": "AI and innovation lead",
        "context_file": "contexts/Ai_Agent.json",
        "description":(
            "Designs the AI components and innovation strategy for Nexus Engineering S.r.l. tender responses. "
            "Knows the company's LLM stack, RAG capabilities, fine-tuning methods, explainability tools, "
            "performance benchmarks, past AI use cases, and known trade-offs as of 2024."
        ),
    },
    "rse": {
        "name": "CSRSustainability Agent",
        "role": "CSR and sustainability officer",
        "context_file": "contexts/Rse_Agent.json",
        "description":(
            "Manages the CSR and sustainability posture for Nexus Engineering S.r.l. tender responses. "
            "Knows the company's EcoVadis rating, carbon footprint, green hosting partners, digital sobriety practices, "
            "social commitments, AI ethics principles, and known sustainability trade-offs as of 2024."
        ),
    },
}


def create_agent(agent_type: str, model: str = "command-r") -> Agent:
    """Instantiate a single agent by its registry key."""
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(
            f"Unknown agent type: {agent_type!r}. "
            f"Available: {list(AGENT_REGISTRY)}"
        )
    cfg = AGENT_REGISTRY[agent_type]
    return Agent(
        name=cfg["name"],
        role=cfg["role"],
        context_file=cfg["context_file"],
        description=cfg["description"],
        model=model,
    )


def create_all_agents(model: str = "command-r") -> list:
    """Instantiate every agent declared in the registry."""
    return  [create_agent(key, model) for key in AGENT_REGISTRY]


if __name__=="__main__":
    agent=create_agent("legal")
    with open("file.txt", "r", encoding="utf-8") as f:
        lines=f.readlines()
        text=" ".join(lines)
    print("yo")
    answer=agent.assess(text)
    print(answer)
    boolean=agent.coherency_check(answer)
    print(boolean)