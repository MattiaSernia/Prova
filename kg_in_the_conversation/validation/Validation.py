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

