import json
import re
from CoreferenceResolver import CoreferenceResolver
from utils import ollama_chat, sentence_split


class Phi4TripletExtractor:

    _SYSTEM = (
        "You are a helpful AI assistant specializing in Information Extraction tasks "
        "such as Named Entity Recognition and Relation Extraction. "
        "Follow the instructions given by the user."
    )

    _SCHEMA = json.dumps({
        "entities": [
            "Organization", "Technology", "Service", "Certification",
            "Budget", "Person", "Infrastructure", "Regulation",
            "Capability", "Project"
        ],
        "relations": [
            "provides", "uses", "has_certification", "complies_with",
            "costs", "employs", "integrates_with", "delivers", "hosts",
            "supports", "has_capacity", "has_budget", "manages",
            "has_risk_level", "has_deadline", "has_value"
        ]
    })

    _EXAMPLE = (
        'Text: "BuildCore SA holds an ISO 14001 environmental certification and employs 320 staff across four regional offices."\n'
        'Output: [{"subject": "BuildCore SA", "predicate": "holds", "object": "ISO 14001 environmental certification"}, '
        '{"subject": "BuildCore SA", "predicate": "employs", "object": "320 staff across four regional offices"}]\n\n'
        'Text: "The logistics framework contract with FastFreight Group is valued at 1.8 million euros and has a submission deadline of 30 June 2025."\n'
        'Output: [{"subject": "logistics framework contract", "predicate": "has_value", "object": "1.8 million euros"}, '
        '{"subject": "logistics framework contract", "predicate": "has_deadline", "object": "30 June 2025"}, '
        '{"subject": "logistics framework contract", "predicate": "involves", "object": "FastFreight Group"}]'
    )

    _OUTPUT_FORMAT = '[{"subject": "...", "predicate": "...", "object": "..."}]'

    def __init__(self, model: str, coref=None, chunk_dim: int = 0, no_schema: bool = False):
        self.model = model
        self.coref = coref if coref is not None else CoreferenceResolver()
        self._chunk_dim = chunk_dim
        self._no_schema = no_schema

    def _build_prompt(self, text: str) -> str:
        base = (
            "Information Extraction is the process of automatically identifying and "
            "extracting structured information from unstructured text data.\n"
            "Always extract numbers, dates, and currency values regardless of the specific task.\n\n"
            "The task at hand is Relation Extraction: extract factual subject-predicate-object "
            "triplets from business and tender-related text.\n\n"
            "Here is an example of task execution:\n"
            f"{self._EXAMPLE}\n\n"
            "Analyze the text and targets carefully, identify relevant information.\n"
            f"Extract the information in the following format: `{self._OUTPUT_FORMAT}`.\n"
            "If no matching entities are found, return an empty list: [].\n"
            "Please provide only the extracted information without any explanations.\n\n"
        )
        if self._no_schema:
            return base + f"Text: {text}"
        else:
            return base + f"Schema: {self._SCHEMA}\nText: {text}"

    def _parse(self, raw: str) -> list:
        raw = raw.strip()
        # estrai il primo array JSON valido dalla risposta
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                if isinstance(data, list):
                    return [
                        {
                            "subject": str(item.get("subject", "")).strip(),
                            "predicate": str(item.get("predicate", "")).strip(),
                            "object": str(item.get("object", "")).strip(),
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
                {"role": "user", "content": self._build_prompt(text)},
            ],
        )
        return self._parse(response["message"]["content"])

    def pipe(self, text: str) -> dict:
        text = self.coref.resolve(text)
        phrases = sentence_split(text, self._chunk_dim)
        chunk_triplets = {}
        for phrase in phrases:
            triplets = self.answer(phrase)
            chunk_triplets[phrase] = triplets
        return chunk_triplets
