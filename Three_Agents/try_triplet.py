from tripletExtractor import TripletExtractor
from CoreferenceResolver import CoreferenceResolver
from triplet import Triplet
if __name__=="__main__":
    with open("test1.log", "r", encoding="utf-8") as log:
        rows=log.readlines()
        
    i=0
    r2=[]
    while i < len(rows)-1:
        j=i+1
        stringa=rows[i]
        if "HTTP" not in stringa.split(" "):
            while not rows[j].startswith("2026"):
                stringa+= "\n"+rows[j]
                i=j
                j+=1
            r2.append(stringa.strip())
        i+=1
    if rows[len(rows)-1].startswith("2026"): r2.append(rows[len(rows)-1])

    extractor= TripletExtractor("command-r", 0)

    cohe=[]
    corr=[]
    HR_Agent=[]
    Orchestrator=[]
    Logistic_Agent=[]

    for row in r2:
        if "coherence" in row.split(" "):
            cohe.append(row.split(" | ")[-1])
        elif "Correct:" in row.split(" "):
            corr.append(row.split(" | ")[-1])
        elif "HR" in row.split(" "):
            HR_Agent.append(row.split(" | ")[-1])
        elif "Logistic" in row.split(" "):
            Logistic_Agent.append(row.split(" | ")[-1])
        else:
            Orchestrator.append(row.split(" | ")[-1])
    
    text=""
    final = []
    for lista in [HR_Agent, Orchestrator, Logistic_Agent]:
        for element in lista:
            first=element.split("answered:")[-1]
            text+=first.split("received:")[-1]+"\n"
        resolver=CoreferenceResolver()
        text=resolver.resolve(text)
        answers=extractor.answer(text)
        for element in answers:
            print(element)
            final.append(Triplet(element[0],element[1],element[2]))

    with open("triplet_file.txt", "w", encoding="utf-8") as trf:
        for element in final:
            trf.write(element.toString()+"\n")
    
    #for row in r2:
    #    answers=extractor.answer(row.split(" | "[-1]))
    #    for element in answers:
    #        print(element[0])


    
    
    
    
    