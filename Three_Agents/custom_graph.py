from rdflib import Graph, Literal, RDF, Namespace, URIRef
from rdflib.term import BNode
from rdflib.namespace import PROV, XSD
from mxg import Message
from tripletExtractor import TripletExtractor
from CoreferenceResolver import CoreferenceResolver
import re
class Custom_Graph:
    def __init__(self, file="", graph_name:str):
        self.name=graph_name
        self.graph=Graph()
        if not file =="":
            try:
                self.graph.parse(file)
            except Exception:
                print("File not found")
        self.extractor= TripletExtractor("command-r", 0)
        self.dict={}
        self.NS = Namespace("http://esempio.org/ontologia#")
        self.graph.bind("ns", self.NS)
        self.nodeUri="http://example.org/node/"
        self.edgeUri="http://example.org/edge/"
        self.graph.bind("prov",PROV)
        self.resolver=CoreferenceResolver()

    def triplet_extraction(self, file=""):
        try:
            with open(file, "r", encoding="utf-8") as log:
                rows=log.readlines()
            
        except Exception as e:
            print(f"Exception {e}")
        rows=self.cleanRows(rows)
        messages=[]
        for row in rows:
            mxg=self.generate_mxg(row)
            messages.append(mxg)
        self.generate_graph(messages)

    def generate_graph(self, messages:list):     
        for i in range(len(messages)):
            mxg=messages[i]
            error=False
            if mxg.role=="default":
                URIagent=URIRef(self.nodeUri + self.clean_uri(mxg.node))
                if (URIagent, RDF.type, self.NS.Agent) not in self.graph:
                    self.graph.add((URIagent, RDF.type, self.NS.Agent))
                if mxg.text in self.dict:
                    URImxg=self.dict[mxg.text]
                    if (URImxg, self.NS.is_coherent,Literal('FALSE')) in self.graph or (URImxg, self.NS.does_answer,Literal('FALSE')):
                        for (s,o,p) in self.graph:
                            if s==URImxg:
                                self.graph.remove((s, o, p))
                            if p==URImxg:
                                if isinstance(s, BNode):
                                    self.graph.remove((s, None, None))
                                else:
                                    self.graph.remove((s,o,p))

                    else:
                        error=True             
                else:
                    URImxg=URIRef(self.nodeUri +f"message{len(self.dict.keys())}")
                    self.dict[mxg.text]=URImxg
                if not error:
                    text=mxg.text
                    self.graph.add((URImxg, self.NS.sended_by,URIagent))
                    if mxg.convPart== "question":
                        self.graph.add((URImxg, self.NS.sended_at,URIRef(self.nodeUri + self.clean_uri(messages[i+1].node))))
                    elif mxg.convPart== "answer":
                        self.graph.add((URImxg, self.NS.sended_at,URIRef(self.nodeUri + self.clean_uri(messages[i-1].node))))
                        text=messages[i-1].text+"\n"+text
                    self.graph.add((URImxg, self.NS.timestamp, Literal(mxg.timestamp, datatype=XSD.dateTime)))
                    print(text)
                    text=self.resolver.resolve(text)
                    answers=self.extractor.answer(text)
                    for element in answers:
                        stmt = BNode()
                        #self.graph.add((stmt, RDF.type, RDF.Statement))
                        self.graph.add((stmt, RDF.subject,   URIRef(self.nodeUri + self.clean_uri(element[0]))))
                        self.graph.add((stmt, RDF.predicate, URIRef(self.edgeUri + self.clean_uri(element[1]))))
                        self.graph.add((stmt, RDF.object,    URIRef(self.nodeUri + self.clean_uri(element[2]))))
                        self.graph.add((stmt, self.NS.estracted_from, URImxg))
                        print(element[0], element[1], element[2])
            elif mxg.role=="coherency":
                if mxg.convPart=="answer":
                    URImxg=self.dict[messages[i-1].text]
                    self.graph.add((URImxg, self.NS.is_coherent,Literal(messages[i].text)))
            elif mxg.role=="correction":
                if mxg.convPart=="answer":
                    URImxg=self.dict[messages[i-1].text]
                    self.graph.add((URImxg, self.NS.does_answer,Literal(messages[i].text.lstrip().rstrip())))
        self.saveGraph()

    def clean_uri(self, label: str) -> str:
        label = label.strip().lower()
        label = re.sub(r'[^a-zA-Z0-9]', '_', label)
        label = re.sub(r'_+', '_', label)
        return label.strip('_')                

    def generate_mxg(self, text:str)-> Message:
        split=text.split(" | ")
        timestamp = split[0]
        unmodified_text = split[2]
        split=unmodified_text.split(": ")
        mxgCorp = ": ".join(split[1:])
        mxgInfo = split[0]
        total = mxgInfo.split(" ")
        if "received" in total:
            node = "Orchestrator"
            convPart = "question"
        elif "Orchestrator" in total:
            node="Orchestrator"
            convPart = "answer"
        elif "HR" in total:
            node="HR Agent"
            convPart = "answer"
        elif "Logistic" in total:
            node="Logistic Agent"
            convPart = "answer"
        elif "User" in total:
            node="User"
            convPart = "question"
        role = "default"
        
        if "coherence" in total:
            role = "coherency"
        elif "correct" in total:
            role= "correction"
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

    def saveGraph(self):
        self.graph.serialize(destination=f"{self.name}.ttl", format="turtle", encoding="utf-8")


if __name__=="__main__":
    grafo=Custom_Graph()
    grafo.triplet_extraction("test.log")
