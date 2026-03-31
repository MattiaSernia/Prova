import ollama
import re
from triplet import Triplet
from CoreferenceResolver import CoreferenceResolver
class TripletExtractor:
    def __init__(self, model, temperature):
        self.model=model
        self.temperature=temperature
        self.context=("You are a natural language processing expert specializing in Open Information Extraction (OIE). "
                        "Extract all subject-relation-object triplets from the sentence provided. "
                        "Use this exact format: [subject | relation | object]\n"
                        "Rules:\n"
                        "- Extract one triplet per distinct relation\n"
                        "- Preserve negations in the relation (e.g. 'did not win' not 'win')\n"
                        "- Keep subjects and objects as specific as possible\n"
                        "- Output only the triplets, no other text, no numbering")
        self.examples= """EXAMPLES:
                Sentence: Marie Curie discovered the elements polonium and radium and was the first woman to win a Nobel Prize, as well as the first person to win two Nobel Prizes in different fields, physics and chemistry.
                Triplets:
                [Marie Curie | discovered | polonium]
                [Marie Curie | discovered | radium]
                [Marie Curie | won | the Nobel Prize in Physics]
                [Marie Curie | won | the Nobel Prize in Chemistry]

                Sentence: Albert Einstein, who was born in Germany, developed the theory of relativity and won the Nobel Prize in Physics in 1921.
                Triplets:
                [Albert Einstein | was born in | Germany]
                [Albert Einstein | developed | the theory of relativity]
                [Albert Einstein | won | the Nobel Prize in Physics]
                [Albert Einstein | won the Nobel Prize | in 1921]

                Sentence: The committee did not approve the proposal because it lacked sufficient evidence.
                Triplets:
                [the committee | did not approve | the proposal]
                [the proposal | lacked | sufficient evidence]

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
