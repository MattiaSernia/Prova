import ollama
import re
from triplet import Triplet
from CoreferenceResolver import CoreferenceResolver
class TripletExtractor:
    def __init__(self, model, temperature):
        self.model=model
        self.temperature=temperature
        self.context=("""You are an expert in Open Information Extraction (OIE) for business intelligence.
You extract factual subject-relation-object triplets from messages produced by AI agents 
operating in the context of company management and public tender evaluation.
 
The domain includes: financial data, HR resources, project portfolios, 
compliance certifications, contracts, and tender bids.
 
RULES:
- Extract only concrete, factual triplets (numbers, statuses, names, dates, amounts)
- Use the company or agent name as subject when it is the source of the fact
- Keep relations short and descriptive (e.g. "has_cash_position", "has_risk_level", "available_FTE")
- Keep objects specific and literal (e.g. "€520,000", "low", "38%", "2", "up-to-date")
- DO NOT extract generic or encyclopedic facts (e.g. "Italy has capital Rome")
- DO NOT extract meta-facts about the conversation itself
- If no concrete factual triplets can be extracted, output nothing
- Output ONLY the triplets, one per line, using this exact format: [subject | relation | object]
- No numbering, no explanation, no other text""")
        self.examples= """EXAMPLES:
 
Sentence: Your current cash position is €520,000, while the available credit line is €300,000, for a combined liquidity of €820,000.
Triplets:
[Nexus Engineering | has_cash_position | €520,000]
[Nexus Engineering | has_credit_line | €300,000]
[Nexus Engineering | has_liquidity | €820,000]
 
Sentence: There are a total of two FTEs available for new projects in Q2 2025.
Triplets:
[Nexus Engineering | available_FTE_Q2_2025 | 2]
 
Sentence: Two out of three projects are assessed as having low risk (CTR001 and CTR002), while one project has been evaluated as medium-risk (CTR003).
Triplets:
[CTR001 | has_risk_level | low]
[CTR002 | has_risk_level | low]
[CTR003 | has_risk_level | medium]
 
Sentence: The total completion percentage of ongoing projects is approximately 38%.
Triplets:
[Nexus Engineering portfolio | completion_percentage | 38%]
 
Sentence: Yes, all mandatory certifications are up-to-date as of April 1st 2025.
Triplets:
[Nexus Engineering | certifications_status | up-to-date]
[Nexus Engineering | certifications_valid_as_of | 2025-04-01]
 
Sentence: Are we ready to bid for the Regione Lombardia €2M infrastructure tender, submission deadline May 10th?
Triplets:
[Regione Lombardia tender | value | €2,000,000]
[Regione Lombardia tender | submission_deadline | 2025-05-10]
[Regione Lombardia tender | type | infrastructure]
 
Now extract triplets from:
Sentence: {sentence}
Triplets:"""

    def parse_triplets(self, text:str)->list:
        #pattern = r"\[([^\]|]+)\|([^\]|]+)\|([^\]]+)\]" #parserizza [A | B | C] 
        pattern=r"\[([^\]|]+)\|([^\]|]+)\|([^\]|]+)\]" #ignora righe con piu di tre elementi
        # Versione per 4 elementi
        #pattern = r"\[([^\]|]+)\|([^\]|]+)\|([^\]|]+)\|([^\]|]+)\]"
        return re.findall(pattern, text)
    
    def answer(self, text:str)->list:
        prompt = self.examples.format(sentence=text)
        response=ollama.chat(self.model,
                             messages=[
                                {'role': 'system', 'content': self.context},
                                {'role': 'user', 'content': prompt}
                            ])
        textual_answer= response['message']['content']
        return self.parse_triplets(textual_answer)
    
    def string_separator(self, text:str)->list:     #Separazione presa da OIE_LLM.pdf
        abbrev= r"\b(Mr|Mrs|Dr|Prof|vs|etc|Jr|Sr|Fig|al)\." #trova qualsiasi parola tra quelle nella parentesi seguita dal punto (\.)
        text = re.sub(abbrev, r"\1<DOT>", text) #per \1 si intende la prima parte che viene catturata dalla regrex, quindi per esempio Mr che significa che Mr. -> Mr<DOT>
        sentences= re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])",text) #prima della punto dove splittare ci devono essere o . o ! o ?, poi ci devono essere piu spazi s+ e poi una maiuscola o ' o "
        sentences=[s.replace("<DOT>", ".").strip() for s in sentences]
        phrases=[s for s in sentences if s]
        return phrases

    def pipe(self, text:str) -> list:
        phrases=self.string_separator(text)
        text_triplets=[]
        for p in phrases:
            sentence_triplets=self.answer(p)
            for tri in sentence_triplets:
                triplet=Triplet(tri[0], tri[1], tri[2])
                text_triplets.append(triplet)
        return text_triplets
    


if __name__=="__main__":
    tri=TripletExtractor('llama3.2:1b', 0)
    tri.answer("Marie Curie isolated the elements polonium and radium, which were both highly radioactive.")
