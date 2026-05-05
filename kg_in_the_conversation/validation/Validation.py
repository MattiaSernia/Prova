import ollama
import json
from typing import Optional
class Validation:
    def __init__(self, model, temperature):
        self.model=model
        self.temperature=temperature
        self._requirements=self._load("validation/requirements.json", "requirements")
        self._constraints=self._load("validation/constraints.json", "constraints")
        
    def sprint(self):
        print(self._requirements)
    def validate_requirements(self, proposal: str) -> list[str]:
        prompt = (
            "You are an expert requirements analyst.\n\n"
            "Below is a list of requirements in JSON format:\n"
            f"{self._requirements}\n\n"
            "Below is a proposal:\n"
            f"{proposal}\n\n"
            "Identify which requirements are satisfied by this proposal.\n"
            'Return a JSON object with a single key "satisfied" whose value is an array of the matching requirement IDs.\n'
            'Example: {"satisfied": ["REQ-01", "REQ-03"]}\n'
            "If none are satisfied return: {\"satisfied\": []}"
        )

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": self.temperature},
            format="json",
        )

        content = response["message"]["content"]
        data = json.loads(content)
        return data.get("satisfied", [])

    def validate_constraints(self, proposal: str) -> list[str]:
        prompt = (
            "You are an expert compliance analyst.\n\n"
            "Below is a list of constraints in JSON format:\n"
            f"{self._constraints}\n\n"
            "Below is a proposal:\n"
            f"{proposal}\n\n"
            "Identify which constraints are satisfied (respected) by this proposal.\n"
            'Return a JSON object with a single key "satisfied" whose value is an array of the matching constraint IDs.\n'
            'Example: {"satisfied": ["CON-01", "CON-03"]}\n'
            "If none are satisfied return: {\"satisfied\": []}"
        )

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": self.temperature},
            format="json",
        )

        content = response["message"]["content"]
        data = json.loads(content)
        return data.get("satisfied", [])


    def _validate_constraint(self, proposal: str, constraint: dict) -> tuple:
        text = f"{constraint.get('subject', '')} {constraint.get('predicate', '')} {constraint.get('object', '')}"
        if constraint.get("constraintType"):
            text += f" ({constraint['constraintType']})"

        prompt = (
            "You are an expert compliance analyst.\n\n"
            "Below is a single constraint:\n"
            f"{text}\n\n"
            "Below is a proposal:\n"
            f"{proposal}\n\n"
            "Is this constraint satisfied (respected) by the proposal?\n"
            'Return a JSON object with a single key "satisfied" whose value is true or false.\n'
            'Example: {"satisfied": true}'
        )

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": self.temperature},
            format="json",
        )

        content = response["message"]["content"]
        print(content)
        data = json.loads(content)
        satisfied = bool(data.get("satisfied", False))
        return (True, text) if satisfied else (False, None)

    def validate(self, proposal: str):
        constraint_list=[]
        for element in self._constraints:
            answer=self._validate_constraint(proposal, element)
            print(answer)
            if answer[0]:
                constraint_list.append(answer[1])



    def _load(self, file, doc):
        with open(file, "r", encoding="utf-8") as f:
            file=json.load(f)
        struct={}
        for f in file:
            key = f["id"]
            entry = {"subject":f["subject"], "predicate": f["predicate"], "object": f["object"]}
            if doc=="requirements":
                if f["priority"]:
                    entry["priority"] = f["priority"]
                if f["category"]:
                    entry["category"] = f["category"]
            else:
                if f["constraintType"]:
                    entry["constraintType"] = f["constraintType"]
            struct[key]=entry
        return json.dumps(struct, indent=2, ensure_ascii=False)



if __name__=="__main__":
    Val=Validation("llama3.3:70b",0)
    self.validate("""Final proposal generated: ### Executive Summary
Nexus Engineering S.r.l., as part of a consortium, is pleased to submit this tender proposal in response to the City of Belval's call for implementing an artificial intelligence solution to assist municipal agents in their daily missions. Our proposed solution leverages cutting-edge AI technologies, including Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG), to provide intelligent assistance across various administrative activities. We are committed to ensuring compliance with all regulatory requirements, particularly GDPR, while prioritizing innovation, sustainability, and cost-effectiveness.

### Understanding of Requirements
We have thoroughly reviewed the City of Belval's requirements for an AI solution that can assist municipal agents in searching for information, drafting letters or answers, suggesting actions or steps, and accompanying them in the instruction of files. We understand the importance of integrating this solution into existing practices without disrupting current workflows. Additionally, we recognize the need for high availability, performance, security, and compliance with regulatory requirements such as GDPR.

### Proposed Solution
- **Technical Solution**: Our technical approach involves leveraging API integration to connect with civil-status and town-planning software, EDM systems, and user directories. We propose a microservices-based architecture deployed on SecNumCloud-certified infrastructure to ensure high availability and scalability. While our typical response time exceeds the required 2 seconds, we plan to optimize our architecture using caching, load balancing, and auto-scaling.
  
- **AI Innovation**: Our AI solution utilizes LLMs like Mistral 7B for tasks such as information search, drafting, and suggestion. We also propose leveraging RAG capabilities for providing relevant information to agents. Furthermore, we aim to innovate by applying knowledge graphs for procedural reasoning and exploring multi-agent collaboration frameworks.

- **Legal Compliance**: We confirm our compliance with GDPR requirements, ensuring data hosting within the EU, no cross-border transfers without legal basis, and protection of sensitive data through anonymization and encryption. Our AI practices are designed to be transparent and explainable, with human oversight over automated decisions.

- **Security and Compliance**: We guarantee that all data is hosted exclusively within the EU and protect sensitive data through anonymization tools and multi-factor authentication. Our network security architecture follows zero-trust principles, and we conduct regular penetration tests. We also maintain ISO 27001 certification for our AI-powered information systems.

- **Sustainability**: To reduce energetic consumption, we propose hosting solutions with green hosting partners powered by renewable energy. Our digital sobriety practices include model quantization, auto-scaling, query result caching, and a green IT hardware procurement policy, aiming to achieve a typical energy reduction of around 35%.

### Compliance & Certifications
We confirm our compliance with all specified regulatory requirements, including GDPR, EU AI Act, and ISO 27001 certification. Our data processing agreements are aligned with GDPR standards, ensuring transparency and explainability in our AI practices.

### Budget Overview
Given the total contract value of 3 million euros, we estimate our projected margin based on a target gross margin percentage of 28%, which would amount to approximately 840,000 euros. However, actual costs and margins may vary depending on project specifics.

### Conclusion
Nexus Engineering S.r.l., as part of this consortium, is committed to delivering an innovative AI solution that meets the City of Belval's requirements for assisting municipal agents while ensuring regulatory compliance, sustainability, and cost-effectiveness. We believe our proposed solution offers a balanced approach to innovation, security, and environmental responsibility, making us an ideal partner for this project.
""")