import ollama
import re
import json
from rdflib import ConjunctiveGraph, Namespace, URIRef
from rdflib.namespace import RDF


class RequirementJudge:

    def __init__(self, model, temperature, graph):

        self._EX   = Namespace("http://example.org/ontologia#")
        self._EDGE = Namespace("http://example.org/edge/")
        self._NODE = Namespace("http://example.org/node/")

        self.model = model
        self.temperature = temperature
        # Load graph and textualize requirements once
        self._requirements_raw = self._load_requirements(graph)
        self._requirements_text = self._textualize(self._requirements_raw)

        self.context = (
            "You are a strict requirement-satisfaction judge for public procurement.\n\n"
            "You must answer ONLY using the REQUIREMENTS data provided below as your context.\n"
            "You will receive a single PROPOSAL TRIPLE (subject, predicate, object) committed\n"
            "by a bidding consortium. Your job is to judge it against the requirements.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "STEP 1 — RELEVANCE FILTER (apply first)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "For each requirement, ask: does the proposal talk about the SAME TOPIC?\n"
            "The proposal and the requirement must share the same functional domain\n"
            "(e.g. both about AI, both about data hosting, both about response time).\n\n"
            "If the answer is NO — the proposal and the requirement concern DIFFERENT topics —\n"
            "then SKIP that requirement entirely. Do NOT include it in any list.\n\n"
            "Most requirements will be skipped. A single proposal triple typically relates\n"
            "to only 1-3 requirements at most. If you find yourself listing more than 5\n"
            "requirements, you are probably not filtering strictly enough.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "STEP 2 — SATISFACTION JUDGEMENT (only for relevant requirements)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "For the few requirements that passed Step 1:\n"
            "- SATISFIES: the proposal directly and meaningfully addresses the requirement.\n"
            "- DOES_NOT_SATISFY: the proposal is about the same topic but fails to meet it\n"
            "  (insufficient, partial, or mismatched).\n\n"
            "RULES:\n"
            "- Base your judgement EXCLUSIVELY on the semantic content of the triples.\n"
            "- Consider priority: 'must' requires strict satisfaction; 'may' is more lenient.\n"
            "- Output ONLY the triples, no explanation, no commentary, no numbering.\n\n"
            "OUTPUT FORMAT (strict — two sections, nothing else):\n\n"
            "SATISFIES:\n"
            "[subject | predicate | object]\n\n"
            "DOES_NOT_SATISFY:\n"
            "[subject | predicate | object]\n\n"
            "If one section is empty, write the header followed by nothing.\n"
            "Use the requirement's own subject, predicate and object — not the proposal's.\n\n"
            "=== YOUR CONTEXT (requirements knowledge graph — Structured JSON) ===\n"
            f"{self._requirements_text}\n"
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

    def _load_requirements(self, g) -> list[dict]:
        reqs = []
        for subj in g.subjects(RDF.type, self._EX.Requirement):
            s_uri = next(g.objects(subj, RDF.subject), None)
            s = self._local(s_uri) if s_uri else "?"

            pred, obj = "", ""
            for p, o in g.predicate_objects(subj):
                if str(p).startswith(str(self._EDGE)):
                    pred = self._local(p)
                    obj  = self._local(o)
                    break

            pri_uri = next(g.objects(subj, self._EX.priority), None)
            cat_uri = next(g.objects(subj, self._EX.category), None)

            reqs.append({
                "subject":   s,
                "predicate": pred,
                "object":    obj,
                "priority":  self._local(pri_uri) if pri_uri else "",
                "category":  self._local(cat_uri) if cat_uri else "",
            })
        return reqs

    def _textualize(self, reqs: list[dict]) -> str:
        """Structured JSON textualization (best strategy per KG-LLM-Bench §7.1)."""
        struct: dict = {}
        for r in reqs:
            key = r["subject"]
            if key not in struct:
                struct[key] = []
            entry = {"predicate": r["predicate"], "object": r["object"]}
            if r["priority"]:
                entry["priority"] = r["priority"]
            if r["category"]:
                entry["category"] = r["category"]
            struct[key].append(entry)
        return json.dumps(struct, indent=2, ensure_ascii=False)

    # ── Parsing ─────────────────────────────────────────────────────────

    def parse_tuples(self, text: str) -> dict:
        """Parse the LLM output into two lists of triples."""
        satisfies: list[list[str]] = []
        does_not: list[list[str]]  = []
        pattern = r"\[([^\]|]+)\|([^\]|]+)\|([^\]|]+)\]"

        current = None
        for line in text.splitlines():
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
        for element in satisfies:
            print(f'sati\n {element}\n\n')

        for element in does_not:
            print(f'does not\n {element}\n\n')

        return {"satisfies": satisfies, "does_not_satisfy": does_not}

    # ── LLM call ────────────────────────────────────────────────────────

    def answer(self, proposal_triple: str) -> dict:
        """Evaluate a single proposal triple against all requirements."""
        print(proposal_triple)
        prompt = (
            f"Evaluate this proposal triple against the requirements in your context:\n"
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
        print(textual_answer + "\n\n\n\n")
        return self.parse_tuples(textual_answer)

    # ── Public API (same pattern as other extractors) ───────────────────

    def pipe(self, proposal: dict) -> dict:
        """Evaluate a proposal dict {"subject":…, "predicate":…, "object":…}
        against all requirements.

        Returns {"satisfies": [[s,p,o], …], "does_not_satisfy": [[s,p,o], …]}
        """
        triple_str = f"({proposal['subject']}, {proposal['predicate']}, {proposal['object']})"
        print(triple_str)
        return self.answer(triple_str)

    def extract_proposals(self, graph) -> list[str]:
        """Extract all ex:Proposal triples from the graph, returned as
        strings ready to be passed to answer().
        Format: '(subject, predicate, object)'
        """
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

if __name__=='__main__':
        g = ConjunctiveGraph()
        g.parse("Paura.trig", format="trig")
        req_jud=RequirementJudge('llama3.3:70b',0 ,g)
        proposals=req_jud.extract_proposals(g)
        #i=0
        for element in proposals:
            #if i==5:
                #break
            capperi=req_jud.answer(element)
            #i+=1

        
