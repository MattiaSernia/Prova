import ollama
import re
import json
from rdflib import ConjunctiveGraph, Namespace, URIRef
from rdflib.namespace import RDF


class ConstraintJudge:

    def __init__(self, model, temperature, graph):

        self._EX   = Namespace("http://example.org/ontologia#")
        self._EDGE = Namespace("http://example.org/edge/")
        self._NODE = Namespace("http://example.org/node/")

        self.model = model
        self.temperature = temperature
        # Load graph and textualize constraints once
        self._constraints_raw = self._load_constraints(graph)
        self._constraints_text = self._textualize(self._constraints_raw)

        self.context = (
            "You are a strict constraint-compliance judge for public procurement.\n\n"
            "You must answer ONLY using the CONSTRAINTS data provided below as your context.\n"
            "You will receive a single PROPOSAL TRIPLE (subject, predicate, object) committed\n"
            "by a bidding consortium. Your job is to judge it against the constraints.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "WHAT IS A CONSTRAINT?\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "A CONSTRAINT is a non-negotiable condition that restricts the space of\n"
            "acceptable solutions. Constraints concern: budget limits, time/duration,\n"
            "technical thresholds (performance, uptime, response time), regulatory\n"
            "compliance (GDPR, ISO, WCAG), infrastructure rules (hosting location,\n"
            "cloud certification), sovereignty/data rules (no transfer outside a\n"
            "territory), environmental rules, security requirements, etc.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "STEP 1 — RELEVANCE FILTER (apply first)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "For each constraint, ask: does the proposal talk about the SAME TOPIC?\n"
            "The proposal and the constraint must share the same functional domain\n"
            "(e.g. both about data hosting, both about budget, both about response time,\n"
            "both about GDPR, both about availability).\n\n"
            "If the answer is NO — the proposal and the constraint concern DIFFERENT topics —\n"
            "then SKIP that constraint entirely. Do NOT include it in any list.\n\n"
            "Most constraints will be skipped. A single proposal triple typically relates\n"
            "to only 1-3 constraints at most. If you find yourself listing more than 5\n"
            "constraints, you are probably not filtering strictly enough.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "STEP 2 — COMPLIANCE JUDGEMENT (only for relevant constraints)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "For the few constraints that passed Step 1:\n"
            "- SATISFIES: the proposal directly and meaningfully complies with the constraint.\n"
            "  The proposal must meet or exceed the limit/condition imposed by the constraint.\n"
            "- DOES_NOT_SATISFY: the proposal is about the same topic but fails to comply\n"
            "  (insufficient, partial, violates the limit, or mismatched).\n\n"
            "RULES:\n"
            "- Base your judgement EXCLUSIVELY on the semantic content of the triples.\n"
            "- Output ONLY the triples, no explanation, no commentary, no numbering.\n\n"
            "OUTPUT FORMAT (strict — two sections, nothing else):\n\n"
            "SATISFIES:\n"
            "[subject | predicate | object]\n\n"
            "DOES_NOT_SATISFY:\n"
            "[subject | predicate | object]\n\n"
            "If one section is empty, write the header followed by nothing.\n"
            "Use the constraint's own subject, predicate and object — not the proposal's.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "EXAMPLES\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Proposal: (consortium, will host data exclusively within, the european union)\n"
            "SATISFIES:\n"
            "[data | must be hosted exclusively on | territory of the european union]\n"
            "[hosting | will have to be realized on | an infrastructure of secnumcloud type or equivalent]\n\n"
            "DOES_NOT_SATISFY:\n\n"
            "---\n\n"
            "Proposal: (consortium, targets, a gross margin of 28%)\n"
            "SATISFIES:\n\n"
            "DOES_NOT_SATISFY:\n"
            "[global budget | is estimated at | 3 million euros over a duration of 4 years]\n\n"
            "---\n\n"
            "Proposal: (consortium, will use, docker containers for microservices)\n"
            "SATISFIES:\n\n"
            "DOES_NOT_SATISFY:\n\n"
            "---\n\n"
            "Proposal: (solution, guarantees, 99.95% uptime)\n"
            "SATISFIES:\n"
            "[order | is expected to have an availability of | 99.9%]\n\n"
            "DOES_NOT_SATISFY:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "=== YOUR CONTEXT (constraints knowledge graph — Structured JSON) ===\n"
            f"{self._constraints_text}\n"
            "=== END OF CONTEXT ==="
        )

    # ── Graph helpers ───────────────────────────────────────────────────

    @staticmethod
    def _local(uri) -> str:
        s = str(uri)
        if "#" in s:
            s = s.rsplit("#", 1)[-1]
        else:
            s = s.rsplit("/", 1)[-1]
        return s.replace("_", " ")

    def _load_constraints(self, g) -> list[dict]:
        cons = []
        for subj in g.subjects(RDF.type, self._EX.Constraint):
            s_uri = next(g.objects(subj, RDF.subject), None)
            s = self._local(s_uri) if s_uri else "?"

            pred, obj = "", ""
            for p, o in g.predicate_objects(subj):
                if str(p).startswith(str(self._EDGE)):
                    pred = self._local(p)
                    obj  = self._local(o)
                    break

            ct_uri = next(g.objects(subj, self._EX.constraintType), None)

            cons.append({
                "subject":        s,
                "predicate":      pred,
                "object":         obj,
                "constraintType": self._local(ct_uri) if ct_uri else "",
            })
        return cons

    def _textualize(self, cons: list[dict]) -> str:
        """Structured JSON textualization (best strategy per KG-LLM-Bench §7.1)."""
        struct: dict = {}
        for c in cons:
            key = c["subject"]
            if key not in struct:
                struct[key] = []
            entry = {"predicate": c["predicate"], "object": c["object"]}
            if c["constraintType"]:
                entry["constraintType"] = c["constraintType"]
            struct[key].append(entry)
        return json.dumps(struct, indent=2, ensure_ascii=False)

    # ── Parsing ─────────────────────────────────────────────────────────

    def parse_tuples(self, text: str) -> dict:
        satisfies: list[list[str]] = []
        does_not: list[list[str]]  = []
        pattern = r"([^\]|]+)\|([^\]|]+)\|([^\]|]+)"

        current = None
        for line in text.splitlines():
            line = line.rstrip("]").lstrip("[")
            stripped = line.strip().upper()
            if stripped.startswith("SATISFIES"):
                current = "sat"
                continue
            elif stripped.startswith("DOES_NOT_SATISFY") or stripped.startswith("DOES NOT SATISFY"):
                current = "not"
                continue

            matches = re.findall(pattern, line)
            for m in matches:
                triple = [elem.strip() for elem in m]
                if current == "sat":
                    satisfies.append(triple)
                elif current == "not":
                    does_not.append(triple)
        return {"satisfies": satisfies, "does_not_satisfy": does_not}

    # ── LLM call ────────────────────────────────────────────────────────

    def answer(self, proposal_triple: str) -> dict:
        """Evaluate a single proposal triple against all constraints."""
        prompt = (
            f"Evaluate this proposal triple against the constraints in your context:\n"
            f"{proposal_triple}\n"
        )

        response = ollama.chat(
            self.model,
            messages=[
                {"role": "system",  "content": self.context},
                {"role": "user",    "content": prompt},
            ],
        )
        textual_answer = response["message"]["content"]
        print(proposal_triple)
        print(textual_answer)
        return self.parse_tuples(textual_answer)

    # ── Public API (same pattern as other extractors) ───────────────────

    def pipe(self, proposal: dict) -> dict:
        """Evaluate a proposal dict {"subject":…, "predicate":…, "object":…}
        against all constraints.

        Returns {"satisfies": [[s,p,o], …], "does_not_satisfy": [[s,p,o], …]}
        """
        triple_str = f"({proposal['subject']}, {proposal['predicate']}, {proposal['object']})"
        print(triple_str)
        return self.answer(triple_str)

    def extract_proposals(self, graph) -> list[str]:
        proposals = []
        for subj in graph.subjects(RDF.type, self._EX.Proposal):
            s_uri = next(graph.objects(subj, RDF.subject), None)
            s = self._local(s_uri) if s_uri else "?"

            pred, obj = "", ""
            for p, o in graph.predicate_objects(subj):
                if str(p).startswith(str(self._EDGE)):
                    pred = self._local(p)
                    obj  = self._local(o)
                    break

            proposals.append(f"({s}, {pred}, {obj})")
        return proposals


if __name__ == '__main__':
    g = ConjunctiveGraph()
    g.parse("Paura.trig", format="trig")
    con_jud = ConstraintJudge('llama3.3:70b', 0, g)
    proposals = con_jud.extract_proposals(g)
    for element in proposals:
        result = con_jud.answer(element)
        print(f"Proposal: {element}")
        print(f"  Satisfies:         {result['satisfies']}")
        print(f"  Does not satisfy:  {result['does_not_satisfy']}")
        print("---")