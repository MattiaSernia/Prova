import rdflib as rdf
from rdflib.namespace import OWL, RDFS
from Extraction import Extraction
import owlrl

class custom_Graph:
    def __init__(self):
        self.grafo = rdf.Graph()
        self.NS = rdf.Namespace("http://esempio.org/ontologia#")
        self.grafo.bind("ns", self.NS)
        self.edgestr="http://esempio.org/propieta/"
        self.nodestr="http://esempio.org/nodo/"
        self.dictionary={}

    def ontology(self):
        self.grafo.add((self.NS.Person, rdf.RDF.type, OWL.Class))
        self.grafo.add((self.NS.User, RDFS.subClassOf, self.NS.Person))
        self.grafo.add((self.NS.is_called, RDFS.domain, self.NS.Person))
        self.grafo.add((self.NS.received_by, RDFS.domain, self.NS.Message))
        self.grafo.add((self.NS.received_by, RDFS.range, self.NS.User))
        self.grafo.add((self.NS.sended_by, RDFS.domain, self.NS.Message))
        self.grafo.add((self.NS.sended_by, RDFS.range, self.NS.User))
        self.grafo.add((self.NS.knows, rdf.RDF.type, OWL.SymmetricProperty))
        self.grafo.add((self.NS.knows, RDFS.domain, self.NS.Person))
        self.grafo.add((self.NS.knows, RDFS.range, self.NS.Person))
        self.grafo.add((self.NS.received_at, RDFS.range, self.NS.Person))
        self.grafo.add((self.NS.mentioned_in, OWL.inverseOf, self.NS.mentions))

    def msg_addition(self, nodemxg, mxg):
        if nodemxg not in self.dictionary:
            IRImxg=rdf.URIRef(self.nodestr + f"Message_{len(self.dictionary)+1}")
            self.dictionary[nodemxg]=IRImxg
            self.grafo.add((IRImxg, self.NS.hasText, rdf.Literal(nodemxg)))
            lista= Extraction(mxg)
            for element in lista:
                nomi=element
                if len(nomi) ==3:
                    nodo1 = "".join(char for char in nomi[0] if char.isalpha())
                    nodo2="".join(char for char in nomi[2] if char.isalpha())
                    self.addition(nodo1, self.NS.knows, nodo2)
                    self.grafo.add((rdf.URIRef(self.nodestr+nodo1), self.NS.mentioned_in, IRImxg))
                    self.grafo.add((rdf.URIRef(self.nodestr+nodo2), self.NS.mentioned_in, IRImxg))

    def additional_info(self, nodemxg, mxg, date):
        splitting=mxg.split(" ")
        IRImxg=self.dictionary[nodemxg]
        IRIperson=rdf.URIRef(self.nodestr + mxg.split(" ")[2].strip(":"))
        if splitting[0]== "Received":
            self.grafo.add((IRImxg, self.NS.received_by, IRIperson))
            self.grafo.add((IRImxg, self.NS.received_at, rdf.Literal(date)))
        else:
            self.grafo.add((IRImxg, self.NS.sended_by, IRIperson))
            self.grafo.add((IRImxg, self.NS.sended_at, rdf.Literal(date)))



    def addition(self, nodo1, arco, nodo2):
        IRInodo1=rdf.URIRef(self.nodestr + nodo1)
        if (IRInodo1, None, None) not in self.grafo and (None, None, IRInodo1) not in self.grafo:
            self.grafo.add((IRInodo1, self.NS.is_called, rdf.Literal(nodo1)))
        IRInodo2=rdf.URIRef(self.nodestr + nodo2)
        if (IRInodo2, None, None) not in self.grafo and (None, None, IRInodo2) not in self.grafo:
            self.grafo.add((IRInodo2, self.NS.is_called, rdf.Literal(nodo2)))
        if (IRInodo1, arco, IRInodo2) not in self.grafo:
            self.grafo.add((IRInodo1, arco, IRInodo2))

    def saveGraph(self, nome):
        self.grafo.serialize(destination=f"{nome}.ttl", format="turtle", encoding="utf-8")

    def vuoto_inconmensurabile(self):
        # Applica solo RDFS e symmetric property
        owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(self.grafo)
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(self.grafo)
        # Filtra triple con soggetti non URI/BNode
        g_clean = rdf.Graph()
        for s, p, o in self.grafo:
            if isinstance(s, (rdf.URIRef, rdf.BNode)):
                # rimuovi auto-equivalenze owl:sameAs
                if not (p == OWL.sameAs and s == o):
                    g_clean.add((s, p, o))
        self.grafo = g_clean