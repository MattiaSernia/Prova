import ollama
import re
from CoreferenceResolver import CoreferenceResolver

class ConstraintsExtractor:
    def __init__(self, model, temperature):
        self.model=model
        self.temperature=temperature
        self.coref=CoreferenceResolver()
        self.context=("You are a strict constraint-compliance judge for public procurement.\n\n"
            "You must answer ONLY using the CONSTRAINTS data provided below as your context.\n"
            "You will receive a single PROPOSAL TRIPLE (subject, predicate, object) committed\n"
            "by a bidding consortium. Your job is to judge it against the constraints.\n\n"
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
            "STEP 2 — SATISFACTION JUDGEMENT (only for relevant constraints)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "For the few constraints that passed Step 1:\n"
            "- SATISFIES: the proposal directly and meaningfully addresses the constraint.\n"
            "- DOES_NOT_SATISFY: the proposal is about the same topic but fails to meet it\n"
            "  (insufficient, partial, or mismatched).\n"
            "CRITICAL: a constraint that was SKIPPED in Step 1 must NEVER appear in\n"
            "DOES_NOT_SATISFY. DOES_NOT_SATISFY is ONLY for constraints that share the\n"
            "same topic as the proposal but the proposal fails to meet them.\n"
            "If a constraint is about a DIFFERENT topic, it does not belong in ANY list.\n\n"
            "RULES:\n"
            "- Base your judgement EXCLUSIVELY on the semantic content of the triples.\n"
            "- Consider constraintType: hard constraints require strict satisfaction;\n"
            "  soft constraints are more lenient.\n"
            "- Output ONLY the triples, no explanation, no commentary, no numbering.\n"
            "- Write EXACTLY ONE triple per line.\n"
            "- Use ONLY the pipe character | as separator, never commas.\n\n"
            "OUTPUT FORMAT (strict — two sections, nothing else):\n\n"
            "SATISFIES:\n"
            "[subject | predicate | object]\n"
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
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "=== YOUR CONTEXT (constraints knowledge graph — Structured JSON) ===\n"
            f"{self._constraints_text}\n"
            "=== END OF CONTEXT ===")
        
        self.examples= """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            EXAMPLES
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

            Sentence: The total contract value shall not exceed 2.5 million dollars over five years.
            Tuples:
            [Budgetary | total contract value | shall not exceed | 2.5 million dollars over five years]

            Sentence: The agency wants to modernise its document management system and make information easier to find for staff.
            Tuples:

            Sentence: All servers hosting citizen data must be located within the national territory and must not be operated by non-national entities.
            Tuples:
            [Sovereignty | servers hosting citizen data | must be located | within the national territory]
            [Sovereignty | servers hosting citizen data | must not be operated by | non-national entities]

            Sentence: The framework agreement will run for an initial period of two years, with the possibility of two one-year extensions.
            Tuples:
            [Temporal | framework agreement | will run for | initial period of two years with two possible one-year extensions]

            Sentence: The platform must achieve a minimum uptime of 99.5% and return search results in under 4 seconds.
            Tuples:
            [Technical | platform | must achieve | minimum uptime of 99.5%]
            [Technical | platform | must return search results in | under 4 seconds]

            Sentence: The solution should allow inspectors to file reports remotely and reduce duplicated data entry.
            Tuples:

            Sentence: Tenderers must demonstrate compliance with ISO 27001 and hold valid professional liability insurance of at least 1 million euros.
            Tuples:
            [Regulatory | tenderers | must demonstrate compliance with | ISO 27001]
            [Budgetary | professional liability insurance | must be of at least | 1 million euros]

            Sentence: The fleet of vehicles deployed under this contract must meet Euro 6 emission standards.
            Tuples:
            [Environmental | fleet of vehicles | must meet | Euro 6 emission standards]

            Sentence: The system shall integrate with the existing HR software via a REST API. The goal of the project is to reduce administrative workload for HR staff.
            Tuples:
            [Technical | system | shall integrate with | existing HR software via a REST API]

            Sentence: Personal data processed under this contract must be encrypted at rest and in transit using AES-256, and must never be transferred outside the European Economic Area.
            Tuples:
            [Technical | personal data | must be encrypted at rest and in transit using | AES-256]
            [Sovereignty | personal data | must never be transferred outside | the European Economic Area]

            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            Now extract ONLY constraints from:
            Sentence: {sentence}
            Tuples:"""

    def parse_tuples(self, text:str)->list:
        pattern=r"\[([^\]|]*)\|([^\]|]+)\|([^\]|]+)\|([^\]|]+)\]" 
        results = re.findall(pattern, text)
        return [[elem.strip() for elem in match] for match in results]
    
    def answer(self, text:str)->list:
        prompt = self.examples.format(sentence=text)
        response=ollama.chat(self.model,
                             messages=[
                                {'role': 'system', 'content': self.context},
                                {'role': 'user', 'content': prompt}
                            ])
        textual_answer= response['message']['content']
        return self.parse_tuples(textual_answer)

    def string_separator(self, text:str)->list:     
        abbrev= r"\b(Mr|Mrs|Dr|Prof|vs|etc|Jr|Sr|Fig|al)\." 
        text = re.sub(abbrev, r"\1<DOT>", text) 
        sentences= re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])",text) 
        sentences=[s.replace("<DOT>", ".").strip() for s in sentences]
        phrases=[s for s in sentences if s]
        return phrases

    def pipe(self, text:str) -> list:
        text=self.coref.resolve(text)
        phrases=self.string_separator(text)
        text_constraints=[]
        for phrase in phrases:
            sentence_tuples=self.answer(phrase)
            for const in sentence_tuples:
                constraint_data = {
                    "constraintType": const[0] if const[0] else None,
                    "subject": const[1],
                    "predicate": const[2],
                    "object": const[3]
                }
                text_constraints.append(constraint_data)
        return text_constraints