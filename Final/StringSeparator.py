import re
def string_separator(text:str)->list:     #Separazione presa da OIE_LLM.pdf
    abbrev= r"\b(Mr|Mrs|Dr|Prof|vs|etc|Jr|Sr|Fig|al)\." #trova qualsiasi parola tra quelle nella parentesi seguita dal punto (\.)
    text = re.sub(abbrev, r"\1<DOT>", text) #per \1 si intende la prima parte che viene catturata dalla regrex, quindi per esempio Mr che significa che Mr. -> Mr<DOT>
    sentences= re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])",text) #prima della punto dove splittare ci devono essere o . o ! o ?, poi ci devono essere piu spazi s+ e poi una maiuscola o ' o "
    sentences=[s.replace("<DOT>", ".").strip() for s in sentences]
    phrases=[s for s in sentences if s]
    return phrases


if __name__=="__main__":
    with open("output.txt", "r", encoding="utf-8") as f:
        text=f.read()
    phrases= string_separator(text)
    for s in phrases:
        print(s)