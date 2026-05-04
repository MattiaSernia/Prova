import ollama
import json
class Validation:
    def __init__(self, model, temperature):
        self.model=model
        self.temperature=temperature
        self._requirements=self._load("requirements.json", "requirements")
        self._constraints=self._load("constraints.json", "constraints")
        

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
    print(Val.validate_requirements("""**Proposal for Artificial Intelligence Solution for City of Belval**

## 1. Executive Summary
Nexus Engineering S.r.l., in partnership with renowned experts, proposes a comprehensive artificial intelligence (AI) solution to enhance the efficiency and quality of administrative services for the City of Belval. Our proposal aligns with the city's digital transformation strategy, addressing the needs for an intelligent assistance tool that facilitates access to information, improves response quality, and reduces processing times. We commit to delivering a secure, sovereign, and sustainable solution that respects regulatory requirements and minimizes environmental impact.

## 2. Understanding of Requirements
We have carefully reviewed the tender document and understand the City of Belval's objectives and requirements for an AI-powered assistance tool. This includes providing municipal agents with an intelligent platform accessible from their work environment, capable of assisting in administrative activities such as information search, drafting, file instruction, and suggesting actions or steps within administrative processes. The solution must integrate seamlessly into existing systems, ensure high performance and availability, and adhere to strict regulatory and legal constraints.

## 3. Proposed Solution
### Technical Domain:
Our technical architecture leverages expertise in integrating various systems (EDM, ERP, CRM), utilizing containerization (Docker, Kubernetes) and IAC tools (Terraform). We propose hosting on SecNumCloud-certified infrastructure within the EU, ensuring sovereignty and security. Our performance benchmarks indicate we can achieve a response time below 2 seconds and maintain an availability of 99.92%.

### Legal Domain:
We ensure compliance with regulatory requirements, including GDPR, through strict data residency in the EU, no cross-border data transfer without legal basis, and robust access control measures. Our standard contractual clauses guarantee data sovereignty, and we have a DPIA support available.

### Financial Domain:
While specific budget details are not provided, our pricing model aims for a target gross margin of 28%. We propose cost-optimization strategies such as rate renegotiations with subcontractors and identifying areas to minimize fixed and variable costs without compromising project quality.

### AI Innovation Domain:
Our Large Language Model (LLM) stack, specifically the sovereign Mistral 7B Instruct model, will provide contextualized answers. We utilize Retrieval-Augmented Generation (RAG) capabilities for accessing relevant information and rules. Explainability and trust are ensured through source citation, chain-of-thought display, SHAP, LIME, and confidence scoring.

### Sustainability Domain:
We prioritize environmental sustainability by hosting solutions through green partners utilizing 100% renewable energy. Digital sobriety practices include model quantization, auto-scaling, and query result caching to reduce energy consumption. Our social commitments encompass a high gender equality index, accessibility standards, local subcontracting, and employee training.

## 4. Compliance & Certifications
We hold necessary certifications such as ISO 27001 for information security management and are GDPR compliant with a Data Protection Officer appointed. Our experience with security frameworks like RGS v2 (ANSSI) and SecNumCloud ensures we can meet stringent security requirements.

## 5. Budget Overview
Given the global budget of 3 million euros over 4 years, our projected annual revenue would be approximately 750,000 euros. Applying our target gross margin percentage of 28% implies aiming for a gross profit of around 210,000 euros per year. However, detailed cost-optimization strategies require more specific information about the contract's scope and current budget allocation.

## 6. Conclusion
Nexus Engineering S.r.l., along with its partners, is committed to delivering an innovative AI solution that meets the City of Belval's needs for efficiency, quality, and regulatory compliance while prioritizing sustainability and social responsibility. We believe our proposal offers a comprehensive approach to addressing the city's requirements and look forward to the opportunity to contribute to its digital transformation journey.

**Note:** This proposal strictly adheres to the information provided in the agents' answers and the original tender text, without inventing capabilities, figures, references, or commitments not explicitly mentioned.
"""))

