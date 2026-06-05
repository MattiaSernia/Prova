import json
import re
from CoreferenceResolver import CoreferenceResolver
from utils import ollama_chat, sentence_split


class Phi4ConstraintsExtractor:

    _SYSTEM = (
        "You are a helpful AI assistant specializing in Information Extraction tasks "
        "such as Named Entity Recognition and Relation Extraction. "
        "Follow the instructions given by the user."
    )

    _SCHEMA = json.dumps({
        "entities": [
            "System", "Data", "Provider", "Infrastructure", "Contract",
            "Candidate", "Solution", "Platform", "Supplier"
        ],
        "relations": [
            "must comply with", "shall not exceed", "must be located in",
            "must achieve", "is limited to", "must not transfer",
            "must be encrypted", "must integrate with", "must guarantee",
            "shall not exceed", "must hold", "must demonstrate"
        ],
        "constraintType_values": [
            "Budgetary", "Temporal", "Technical", "Regulatory",
            "Environmental", "Sovereignty"
        ]
    })

    _EXAMPLE = (
        'Text: "The total contract value shall not exceed 2.5 million dollars over five years. '
        'All servers hosting citizen data must be located within the national territory."\n'
        'Output: ['
        '{"subject": "total contract value", "predicate": "shall not exceed", "object": "2.5 million dollars over five years", "constraintType": "Budgetary"}, '
        '{"subject": "servers hosting citizen data", "predicate": "must be located", "object": "within the national territory", "constraintType": "Sovereignty"}'
        ']'
    )

    _OUTPUT_FORMAT = '[{"subject": "...", "predicate": "...", "object": "...", "constraintType": "Budgetary|Temporal|Technical|Regulatory|Environmental|Sovereignty or null"}]'

    def __init__(self, model: str, coref=None, chunk_dim: int = 0):
        self.model = model
        self.coref = coref if coref is not None else CoreferenceResolver()
        self._chunk_dim = chunk_dim

    def _build_prompt(self, text: str) -> str:
        return (
            "Information Extraction is the process of automatically identifying and "
            "extracting structured information from unstructured text data.\n"
            "Always extract numbers, dates, and currency values regardless of the specific task.\n\n"
            "The task at hand is Constraints Extraction: extract CONSTRAINTS from the text. "
            "A constraint expresses HOW or UNDER WHAT CONDITIONS the solution must operate. "
            "It is non-negotiable and restricts the space of acceptable solutions. "
            "Ignore business goals and desired outcomes.\n\n"
            "Here is an example of task execution:\n"
            f"{self._EXAMPLE}\n\n"
            "Analyze the text carefully. Extract only conditions, limits, rules, and mandatory requirements.\n"
            f"Extract the information in the following format: `{self._OUTPUT_FORMAT}`.\n"
            "If no constraints are found, return an empty list: [].\n"
            "Please provide only the extracted information without any explanations.\n\n"
            f"Schema: {self._SCHEMA}\n"
            f"Text: {text}"
        )

    def _parse(self, raw: str) -> list:
        raw = raw.strip()
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                if isinstance(data, list):
                    return [
                        {
                            "subject":        str(item.get("subject", "")).strip(),
                            "predicate":      str(item.get("predicate", "")).strip(),
                            "object":         str(item.get("object", "")).strip(),
                            "constraintType": item.get("constraintType") or None,
                        }
                        for item in data
                        if isinstance(item, dict)
                        and item.get("subject") and item.get("predicate") and item.get("object")
                    ]
            except json.JSONDecodeError:
                pass
        return []

    def answer(self, text: str) -> list:
        response = ollama_chat(
            self.model,
            [
                {"role": "system", "content": self._SYSTEM},
                {"role": "user",   "content": self._build_prompt(text)},
            ],
        )
        return self._parse(response["message"]["content"])

    def pipe(self, text: str) -> dict:
        text = self.coref.resolve(text)
        phrases = sentence_split(text, self._chunk_dim)
        chunk_constraints = {}
        for phrase in phrases:
            chunk_constraints[phrase] = self.answer(phrase)
        return chunk_constraints
