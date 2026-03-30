from rdflib import Graph
from mxg import Message
class Custom_Graph:
    def __init__(self, file=""):
        self.graph=Graph()
        if not file =="":
            try:
                self.graph.parse(file)
            except Exception:
                print("File not found")
        self.extractor= TripletExtractor("command-r", 0)
        self.dict={}
        self.nodeUri="http://esempio.org/node/"
        self.edgeUri="http://esempio.org/edge/"

    def triplet_extraction(self, file=""):
        try:
            with open(file, "r", encoding="utf-8"):
                rows=log.readlines()
            rows=self.cleanRows(rows)
            for row in rows:
                mxg=generate_mxg(row)
                print(mxg.toString())
        except Exception as e:
            print(f"Excetion {e}")

    def generate_mxg(self, text:str)->Message:
        split=text.split(" | ")
        timestamp = split[0]
        unmodified_text = split[2]
        split=unmodified_text.split(":")
        mxgCorp = join(split.split(":")[1:], ":")
        mxgInfo = split[0]
        total = mxgIfo.split[" "]
        if "received" in total:
            node = "Orchestrator"
            convPart = "question"
        elif "Orchestrator" in total:
            node="Orchestrator"
            convPart = "answer"
        elif "HR Agent" in total:
            node="HR Agent"
            convPart = "answer"
        elif "Logistic Agent" in total:
            node="Logistic Agent"
            convPart = "answer"
        elif "User" in total:
            node="User"
            convPart = "answer"
        role = "default"
        
        if "coherence" in total:
            role = "coherency"
        elif "Correct" in total:
            role: "correction"
        return(Message(mxgCorp, timestamp, node, convPart, role))

    def cleanRows(self, rows:list)->list:
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
        return r2

if __name__=="__main__":
    grafo=Custom_Graph()
    grafo.triplet_extraction("test1.log")
