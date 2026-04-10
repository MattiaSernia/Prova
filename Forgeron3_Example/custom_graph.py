from rdflib import Graph, Literal, RDF, Namespace, URIRef
from rdflib.term import BNode
from rdflib.namespace import PROV, XSD
from mxg import Message
from tripletExtractorClaude import TripletExtractor
from CoreferenceResolver import CoreferenceResolver
import re

class Custom_Graph:
    def __init__(self, graph_name:str, agent_list:list ,file=""):
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
        self.activityUri = "http://example.org/activity/"
        self.graph.bind("prov",PROV)
        self.resolver=CoreferenceResolver()
        self._activity_counter=0
        self.agent_list=agent_list
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
                if (URIagent, RDF.type, PROV.Agent) not in self.graph:
                    self.graph.add((URIagent, RDF.type, PROV.Agent))
                
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
                    self.graph.add((URImxg, RDF.type, PROV.Entity))

                    URIactivity= self._new_activity_uri()
                    self.graph.add((URIactivity, RDF.type, PROV.Activity))
                    self.graph.add((URIactivity, PROV.wasAssociatedWith, URIagent)) 
                    self.graph.add((URIactivity, PROV.startedAtTime, Literal(mxg.timestamp, datatype=XSD.dateTime)))

                    self.graph.add((URImxg, PROV.wasGeneratedBy, URIactivity))

                    self.graph.add((URImxg, PROV.wasAttributedTo, URIagent))
                    self.graph.add((URImxg, PROV.generatedAtTime, Literal(mxg.timestamp, datatype=XSD.dateTime)))

                    text=mxg.text
                    if mxg.convPart== "question":
                        URInext = URIRef(self.nodeUri + self.clean_uri(messages[i + 1].node))
                        self.graph.add((URImxg, self.NS.sended_at,URIRef(self.nodeUri + URInext)))

                    elif mxg.convPart== "answer":
                        URIprev = URIRef(self.nodeUri + self.clean_uri(messages[i - 1].node))
                        self.graph.add((URImxg, self.NS.sended_at, URIprev))
                        # La risposta è DERIVATA dalla domanda precedente (PROV-O)
                        if messages[i - 1].text in self.dict:
                            URIprevMsg = self.dict[messages[i - 1].text]
                            self.graph.add((URImxg, PROV.wasDerivedFrom, URIprevMsg))
                            # L'activity ha USATO la domanda per produrre la risposta
                            self.graph.add((URIactivity, PROV.used, URIprevMsg))
                        text=messages[i-1].text+"\n"+text

                    text=self.resolver.resolve(text)
                    answers=self.extractor.answer(text)
                    for element in answers:
                        stmt = BNode()
                        self.graph.add((stmt, RDF.type, PROV.Entity))
                        self.graph.add((stmt, RDF.subject,   URIRef(self.nodeUri + self.clean_uri(element[0]))))
                        self.graph.add((stmt, RDF.predicate, URIRef(self.edgeUri + self.clean_uri(element[1]))))
                        self.graph.add((stmt, RDF.object,    URIRef(self.nodeUri + self.clean_uri(element[2]))))
                        self.graph.add((stmt, PROV.wasDerivedFrom, URImxg))
                        
            elif mxg.role=="coherency":
                if mxg.convPart=="answer":
                    URImxg=self.dict[messages[i-1].text]
                    self.graph.add((URImxg, self.NS.is_coherent,Literal(messages[i].text)))

            elif mxg.role=="correction":
                if mxg.convPart=="answer":
                    URImxg=self.dict[messages[i-1].text]
                    self.graph.add((URImxg, self.NS.does_answer,Literal(messages[i].text.lstrip().rstrip())))

        self.saveGraph()
    
    def _new_activity_uri(self) -> URIRef:
        self._activity_counter += 1
        return URIRef(self.activityUri + f"activity{self._activity_counter}")

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
        node=""
        if "received" in total:
            node = "Orchestrator"
            convPart = "question"
        elif "Orchestrator" in total:
            node="Orchestrator"
            convPart = "answer"
        elif "User" in total:
            node="User"
            convPart = "question"
        if node=="":
            for agent in self.agent_list:
                name=agent.name.split(" ")[0]
                if name in total:
                    node=agent.name
                    convPart = "answer"
                    
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
            if "INFO" not in stringa.split(" | "):
                while "INFO" not in rows[j].split(" | ") and "AGENT" not in rows[j].split(" | "):
                    if rows[j]!= "\n":
                        stringa+= "\n"+rows[j]
                    i=j
                    j+=1
                r2.append(stringa.strip())
            i+=1
        if "AGENT" in stringa.split(" | ") and "INFO" not in rows[len(rows)-1].split(" | "): r2.append(rows[len(rows)-1])
        return r2

    def saveGraph(self):
        self.graph.serialize(destination=f"{self.name}.ttl", format="turtle", encoding="utf-8")


if __name__=="__main__":
    grafo=Custom_Graph("Pircillo")
    grafo.triplet_extraction("Primo.log")
