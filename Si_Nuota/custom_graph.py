from rdflib import Graph, ConjunctiveGraph, Namespace, URIRef, Literal, RDF, Namespace
from rdflib.namespace import RDF, XSD, PROV
from constraintsExtractor import ConstraintsExtractor
from requirementsExtractor import RequirementsExtractor
from proposalsExtractor import ProposalsExtractor
from tripletExtractorClaude import TripletExtractor
from CoreferenceResolver import CoreferenceResolver
from Requirementjudge import RequirementJudge
from Constraintjudge import ConstraintJudge
from mxg import Message






import os
import re
import pickle
CHECKPOINT_FILE = "checkpoint_before_graph.pkl"
def load_checkpoint():
    with open(CHECKPOINT_FILE, "rb") as f:
        return pickle.load(f)

class Custom_Graph:

    def __init__(self, agent_list:list,name:str):
        self._EX  = Namespace("http://example.org/ontologia#")
        self._REQ = Namespace("http://example.org/requirement/")
        self._EXT = Namespace("http://example.org/extraction/")
        self._CON = Namespace("http://example.org/constraint/")
        self._PRO = Namespace("http://example.org/proposal/")
        self._TRI = Namespace("http://example.org/triplet/")

        self._ds = ConjunctiveGraph()
        self._ds.bind("ex",  self._EX)
        self._ds.bind("req", self._REQ)
        self._ds.bind("ext", self._EXT)
        self._ds.bind("prov",PROV)
        self._ds.bind("con", self._CON)
        self._ds.bind("pro", self._PRO)
        self._ds.bind("tri", self._TRI)

        self._agent_list=agent_list

        self._nodeUri="http://example.org/node/"
        self._activityUri = "http://example.org/activity/"
        self._extractionUri= "http://example.org/extraction/"
        self._edgeUri="http://example.org/edge/"

        self._dict={}

        self._activity_counter=0
        self._extraction_counter=0
        self._requirement_counter=0
        self._constraint_counter=0
        self._proposal_counter=0
        self._triplet_counter=0

        self._req_extr=RequirementsExtractor("llama3.3:70b",0)
        self._con_extr=ConstraintsExtractor("llama3.3:70b",0)
        self._pro_extr=ProposalsExtractor("llama3.3:70b",0)
        self._extractor=TripletExtractor("llama3.3:70b",0)

        self._name=name


    def add_content(self, file:str):
        messages=self._load(file)
        #messages=self._isolation(messages, "User", "proposal")
        self._generate_graph(messages)
        self._saveGraph()

    def _load(self, file:str)->list:
        try:
            f = open(file, "r", encoding="utf-8")
        except Exception as e:
            print(e)
            return None
        
        rows=f.readlines()
        f.close()
        rows=self._cleanRows(rows)

        messages=[]
        for row in rows:
            mxg=self._generate_mxg(row)
            messages.append(mxg)
        return messages

    def _cleanRows(self, rows:list)->list:
        i=0
        r2=[]
        while i < len(rows)-1:
            j=i+1
            stringa=rows[i]
            if "INFO" not in stringa.split(" | "):
                while j<len(rows) and "INFO" not in rows[j].split(" | ") and "AGENT" not in rows[j].split(" | "):
                    if rows[j]!= "\n":
                        stringa+= "\n"+rows[j]
                    i=j
                    j+=1
                r2.append(stringa.strip())
            i+=1
        stringa=rows[-1]
        if "AGENT" in stringa.split(" | ") and "INFO" not in rows[len(rows)-1].split(" | "): r2.append(rows[len(rows)-1])
        return r2

    def _generate_mxg(self, text:str)-> Message:
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
        elif "Final" in total:
            node="Orchestrator"
            convPart = "proposal"
        if node=="":
            for agent in self._agent_list:
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

    def _isolation(self,messages:list ,node:str, convPart:str)->list:
        output=[]
        for message in messages:
            if message.node==node:
                output.append(message)
            elif message.convPart==convPart:
                output.append(message)
        return output

    def _generate_graph(self, messages:list):
        for i in range(len(messages)):
            mxg=messages[i]
            error=False

            if mxg.role=="default":
                #check if the agent is in the graph or not
                URIagent=URIRef(self._nodeUri + self._clean_uri(mxg.node))
                if (URIagent, RDF.type, PROV.Agent, self._ds.default_context) not in self._ds:
                    self._ds.add((URIagent, RDF.type, PROV.Agent, self._ds.default_context))
            
                #----------- ricontrollare dopo ------------------
                if mxg.text in self._dict:
                    URImxg=self._dict[mxg.text]
                    if (URImxg, self._EX.is_coherent,Literal('FALSE'),self._ds.default_context) in self._ds or (URImxg, self._EX.does_answer,Literal('FALSE'), self._ds.default_context) in self._ds:
                        self._remove_derived_graphs(URImxg)
                        self._ds.remove((URImxg, None, None, self._ds.default_context))
                        self._ds.remove((None, None, URImxg, self._ds.default_context))

                    else:
                        error=True
                #----------- ricontrollare dopo ------------------             
                else:
                    URImxg=URIRef(self._nodeUri +f"message{len(self._dict.keys())}")
                    self._dict[mxg.text]=URImxg
                
                if not error:
                    self._ds.add((URImxg, RDF.type, PROV.Entity, self._ds.default_context))

                    URIactivity= self._new_activity_uri()
                    self._ds.add((URIactivity, RDF.type, PROV.Activity, self._ds.default_context))
                    self._ds.add((URIactivity, PROV.wasAssociatedWith, URIagent, self._ds.default_context)) 
                    self._ds.add((URIactivity, PROV.startedAtTime, Literal(mxg.timestamp, datatype=XSD.dateTime), self._ds.default_context))

                    self._ds.add((URImxg, PROV.wasGeneratedBy, URIactivity, self._ds.default_context))

                    self._ds.add((URImxg, PROV.wasAttributedTo, URIagent, self._ds.default_context))
                    self._ds.add((URImxg, PROV.generatedAtTime, Literal(mxg.timestamp, datatype=XSD.dateTime), self._ds.default_context))

                    text=mxg.text
                    
                    #--------------- not now -------------
                    if mxg.convPart== "question" and i<len(messages)-1:
                        URInext = URIRef(self._nodeUri + self._clean_uri(messages[i + 1].node))
                        self._ds.add((URImxg, self._EX.sended_at,URIRef(self._nodeUri + URInext),self._ds.default_context))

                    elif mxg.convPart== "answer":
                        URIprev = URIRef(self._nodeUri + self._clean_uri(messages[i - 1].node))
                        self._ds.add((URImxg, self._EX.sended_at, URIprev, self._ds.default_context))
                        # La risposta è DERIVATA dalla domanda precedente (PROV-O)
                        if messages[i - 1].text in self._dict:
                            URIprevMsg = self._dict[messages[i - 1].text]
                            self._ds.add((URImxg, PROV.wasDerivedFrom, URIprevMsg,self._ds.default_context))
                            # L'activity ha USATO la domanda per produrre la risposta
                            self._ds.add((URIactivity, PROV.used, URIprevMsg, self._ds.default_context))
                        text=messages[i-1].text+"\n"+text

                    elif mxg.convPart== "proposal":
                        URIprev = URIRef(self._nodeUri + self._clean_uri(messages[i - 1].node))
                        self._ds.add((URImxg, self._EX.sended_at, URIprev, self._ds.default_context))
                        # La risposta è DERIVATA dalla domanda precedente (PROV-O)
                        if messages[i - 1].text in self._dict:
                            URIprevMsg = self._dict[messages[0].text]
                            self._ds.add((URImxg, PROV.wasDerivedFrom, URIprevMsg,self._ds.default_context))
                            # L'activity ha USATO la domanda per produrre la risposta
                            self._ds.add((URIactivity, PROV.used, URIprevMsg, self._ds.default_context))

                    if mxg.node=="User":
                        self._userExtraction(text,URImxg)
                    elif mxg.convPart=="proposal":
                        self._propExtraction(text, URImxg)
                    else:
                        self._normalExtraction(text, URImxg)
            
            elif mxg.role=="coherency":
                if mxg.convPart=="answer":
                    URImxg=self._dict[messages[i-1].text]
                    self._ds.add((URImxg, self._EX.is_coherent,Literal(messages[i].text), self._ds.default_context))

            elif mxg.role=="correction":
                if mxg.convPart=="answer":
                    URImxg=self._dict[messages[i-1].text]
                    self._ds.add((URImxg, self._EX.does_answer,Literal(messages[i].text.lstrip().rstrip()), self._ds.default_context))                  
    def _userExtraction(self, text: str, URImxg):
        requirements=self._req_extr.pipe(text)
        ReqURI=self._new_extraction_uri("req/")
        ng1=self._ds.get_context(ReqURI)
        for requirement in requirements:
            node=self._new_requirement_uri()
            ng1.add((node, RDF.type, self._EX.Requirement))
            ng1.add((node, RDF.subject,    URIRef(self._nodeUri + self._clean_uri(requirement["subject"]))))
            ng1.add((node, URIRef(self._edgeUri + self._clean_uri(requirement["predicate"])),    URIRef(self._nodeUri + self._clean_uri(requirement["object"]))))
            if requirement["priority"]:
                ng1.add((node, self._EX.priority,   self._EX[self._clean_uri(requirement["priority"])]))
            if requirement["category"]:
                ng1.add((node, self._EX.category,   self._EX[self._clean_uri(requirement["category"])]))
        self._ds.add((ReqURI, RDF.type, self._EX.Extraction,   self._ds.default_context))
        self._ds.add((ReqURI, PROV.wasDerivedFrom, URImxg,   self._ds.default_context))

        constraints=self._con_extr.pipe(text)
        ConURI=self._new_extraction_uri("con/")
        ng2=self._ds.get_context(ConURI)
        for constraint in constraints:
            node=self._new_constraint_uri()
            ng2.add((node, RDF.type, self._EX.Constraint))
            ng2.add((node, RDF.subject,    URIRef(self._nodeUri + self._clean_uri(constraint["subject"]))))
            ng2.add((node, URIRef(self._edgeUri + self._clean_uri(constraint["predicate"])),    URIRef(self._nodeUri + self._clean_uri(constraint["object"]))))
            if constraint["constraintType"]:
                ng2.add((node, self._EX.constraintType,   self._EX[self._clean_uri(constraint["constraintType"])]))
        self._ds.add((ConURI, RDF.type, self._EX.Extraction,   self._ds.default_context))
        self._ds.add((ConURI, PROV.wasDerivedFrom, URImxg,   self._ds.default_context))

    def _clean_uri(self, label: str) -> str:
        label = label.strip().lower()
        label = re.sub(r'[^a-zA-Z0-9]', '_', label)
        label = re.sub(r'_+', '_', label)
        return label.strip('_')     

    def _new_activity_uri(self) -> URIRef:
        self._activity_counter += 1
        return URIRef(self._activityUri + f"activity{self._activity_counter}")

    def _new_extraction_uri(self, string:str="") -> URIRef:
        self._extraction_counter += 1
        return URIRef(self._extractionUri + f"{string}extraction{self._extraction_counter}")
    
    def _new_requirement_uri(self) -> URIRef:
        self._requirement_counter += 1
        return self._REQ[f"req{self._requirement_counter}"]

    def _new_constraint_uri(self) -> URIRef:
        self._constraint_counter += 1
        return self._CON[f"con{self._constraint_counter}"]

    def _propExtraction(self, text:str, URImxg):
        proposals=self._pro_extr.pipe(text)
        ProURI=self._new_extraction_uri("pro/")
        ng=self._ds.get_context(ProURI)
        for proposal in proposals:
            node=self._new_proposal_uri()
            ng.add((node, RDF.type, self._EX.Proposal))
            ng.add((node, RDF.subject,    URIRef(self._nodeUri + self._clean_uri(proposal["subject"]))))
            ng.add((node, URIRef(self._edgeUri + self._clean_uri(proposal["predicate"])),    URIRef(self._nodeUri + self._clean_uri(proposal["object"]))))
            req_nodes=self._findreq(f"{proposal['subject']}, {proposal['predicate']}, {proposal['object']}")
            for subjnode in req_nodes["satisfies"]:
                ng.add((node, self._EX.Satisfies, subjnode))
            for subjnode in req_nodes["does_not_satisfy"]:
                ng.add((node, self._EX.Does_Not_Satisfies, subjnode))
            con_nodes=self._findcon(f"{proposal['subject']}, {proposal['predicate']}, {proposal['object']}")
            for subjnode in con_nodes["satisfies"]:
                ng.add((node, self._EX.Satisfies, subjnode))
            for subjnode in con_nodes["does_not_satisfy"]:
                ng.add((node, self._EX.Does_Not_Satisfies, subjnode))
        self._ds.add((ProURI, RDF.type, self._EX.Extraction,   self._ds.default_context))
        self._ds.add((ProURI, PROV.wasDerivedFrom, URImxg,   self._ds.default_context))

    def _normalExtraction(self, text:str, URImxg):
        triplets=self._extractor.pipe(text)
        TriURI=self._new_extraction_uri("tri/")
        ng=self._ds.get_context(TriURI)
        for triplet in triplets:
            node=self._new_triplet_uri()
            ng.add((node, RDF.type, self._EX.Triplet))
            ng.add((node, RDF.subject,    URIRef(self._nodeUri + self._clean_uri(triplet["subject"]))))
            ng.add((node, URIRef(self._edgeUri + self._clean_uri(triplet["predicate"])),    URIRef(self._nodeUri + self._clean_uri(triplet["object"]))))
        self._ds.add((TriURI, RDF.type, self._EX.Extraction,   self._ds.default_context))
        self._ds.add((TriURI, PROV.wasDerivedFrom, URImxg,   self._ds.default_context))
    
    def _new_proposal_uri(self)->URIRef:
        self._proposal_counter += 1
        return self._PRO[f"pro{self._proposal_counter}"]
    
    def _new_triplet_uri(self) -> URIRef:
        self._triplet_counter += 1
        return self._TRI[f"tri{self._triplet_counter}"]

    def _saveGraph(self):
        trig_str = self._ds.serialize(format="trig")
    
        # Sostituisce il blocco anonimo { ... } con GRAPH esplicito
        # rdflib scrive il default context come "{\n" — lo sostituiamo
        trig_str = re.sub(
            r'(?m)^{$',
            'GRAPH <urn:x-arq:DefaultGraph> {',
            trig_str
        )
        
        with open(f"{self._name}.trig", "w", encoding="utf-8") as f:
            f.write(trig_str)
        print("salvato")
        #self._ds.serialize(destination=f"{self._name}.trig", format="trig", encoding="utf-8")

    def _remove_derived_graphs(self, URImxg):
        """Remove all named graphs (extractions) derived from this message."""
        # 1. Find all extraction URIs linked to this message
        extraction_uris = list(self._ds.subjects(PROV.wasDerivedFrom, URImxg))
        
        for ext_uri in extraction_uris:
            # 2. Remove the entire named graph (all extracted triples inside it)
            ng = self._ds.get_context(ext_uri)
            self._ds.remove_context(ng)
            
            # 3. Remove provenance metadata from the default graph
            #    (rdf:type ex:Extraction, prov:wasDerivedFrom, etc.)
            self._ds.remove((ext_uri, None, None, self._ds.default_context))

    def _findreq(self, proposal:str)->dict:
        req_judge=RequirementJudge("llama3.3:70b", 0, self._ds)
        nodes=req_judge.answer(proposal)
        satlist=[]
        for element in nodes["satisfies"]:
            if self._searchnode(element,"requirement"):
                satlist.append(self._searchnode(element,"requirement"))
        not_satlist=[]
        for element in nodes["does_not_satisfy"]:
            if self._searchnode(element,"requirement"):
                not_satlist.append(self._searchnode(element,"requirement"))
        return {"satisfies":satlist, "does_not_satisfy":not_satlist}

    def _searchnode(self, triple:list, typ:str):
        if typ=="requirement":
            typ=self._EX.Requirement
        elif typ == "constraint":
            typ=self._EX.Constraint
        for subj in self._ds.subjects(RDF.type, typ):
            if (subj, RDF.subject, URIRef(self._nodeUri + self._clean_uri(triple[0]))) in self._ds and (subj, URIRef(self._edgeUri + self._clean_uri(triple[1])), URIRef(self._nodeUri + self._clean_uri(triple[2]))) in self._ds:
                return subj
    
    def _findcon(self, proposal:str)->dict:
        con_judge=ConstraintJudge("llama3.3:70b", 0, self._ds)
        nodes=con_judge.answer(proposal)
        satlist=[]
        for element in nodes["satisfies"]:
            if self._searchnode(element,"constraint"):
                satlist.append(self._searchnode(element,"constraint"))
        not_satlist=[]
        for element in nodes["does_not_satisfy"]:
            if self._searchnode(element,"constraint"):
                not_satlist.append(self._searchnode(element,"constraint"))
        return {"satisfies":satlist, "does_not_satisfy":not_satlist}

if __name__=="__main__":
    agent_list = load_checkpoint()
    grafo=Custom_Graph(agent_list, "Paura")
    grafo.add_content("Nuova_Prova.log")