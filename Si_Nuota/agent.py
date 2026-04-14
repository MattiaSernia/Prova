import ollama
import logging
import json


class Agent:
    """
    Generic specialised agent.

    An agent is fully described by:
      - a name (display label)
      - a role (short description, e.g. "technical architect")
      - a context (dict loaded from JSON) representing the company's knowledge
        from this agent's point of view
      - the underlying LLM to use

    The behaviour is identical for every agent: only the role and the context change.
    """

    def __init__(self, name: str, role: str, context_file: str, model: str = "command-r"):
        self.name = name
        self.role = role
        self.data = self._load_context(context_file)
        self.model = model
        self.memory = []

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

    def answer(self, message: str) -> str:
        """Conversational turn — keeps memory of the exchange."""
        logging.log(25, f"{self.name} received: {message}")
        text = self._chat(message, use_memory=True)
        logging.log(25, f"{self.name} answered: {text}")
        return text

    def propose(self, tender: str) -> str:
        """
        Receive a call for tenders (cahier des charges) and produce concrete
        proposals to satisfy its requirements, using ONLY the agent's own context.
        """
        instruction = (
            "You have received the following call for tenders (cahier des charges).\n"
            f"Analyse it from your role's perspective ({self.role}) and produce "
            "concrete proposals to satisfy its requirements.\n\n"
            "Strict rules:\n"
            "- Use ONLY the information available in your context (company knowledge). "
            "Never invent capabilities, certifications, references or numbers.\n"
            "- For each requirement you address, explain HOW your company's existing "
            "capabilities, resources, certifications or experience meet it.\n"
            "- If a requirement cannot be addressed with your context, explicitly flag "
            "it as a GAP rather than inventing a solution.\n"
            "- Stay within your role: do not produce content that belongs to other "
            "roles unless your context directly supports it.\n"
            "- Identify any constraints, risks or trade-offs visible from your context.\n\n"
            "=== CALL FOR TENDERS ===\n"
            f"{tender}\n"
            "=== END OF CALL FOR TENDERS ===\n\n"
            "Produce your structured proposal now."
        )
        logging.log(25, f"{self.name} received tender ({len(tender)} chars)")
        text = self._chat(instruction, use_memory=True)
        logging.log(25, f"{self.name} proposal: {text}")
        return text

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
    },
    "architect": {
        "name": "TechnicalArchitect Agent",
        "role": "technical architect",
        "context_file": "contexts/Architect_Agent.json",
    },
    "security": {
        "name": "SecurityCompliance Agent",
        "role": "security and compliance officer",
        "context_file": "contexts/Compliance_Agent.json",
    },
    "legal": {
        "name": "Legal Agent",
        "role": "legal counsel",
        "context_file": "contexts/Legal_Agent.json",
    },
    "budget": {
        "name": "Budget Agent",
        "role": "financial manager",
        "context_file": "contexts/Budget_Agent.json",
    },
    "ai": {
        "name": "AIInnovation Agent",
        "role": "AI and innovation lead",
        "context_file": "contexts/Ai_Agent.json",
    },
    "rse": {
        "name": "CSRSustainability Agent",
        "role": "CSR and sustainability officer",
        "context_file": "contexts/Rse_Agent.json",
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
        model=model,
    )


def create_all_agents(model: str = "command-r") -> dict:
    """Instantiate every agent declared in the registry."""
    return {key: create_agent(key, model) for key in AGENT_REGISTRY}