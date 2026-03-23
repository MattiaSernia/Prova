import owlrl
from rdflib import Graph, RDF, Namespace
from rdflib.namespace import OWL, RDFS
from queries import getPersone
from add import popola

g=Graph()

EX = Namespace("http://esempio.org/ontologia#")
g.bind("ex", EX)

g.add((EX.Persona, RDF.type, OWL.Class))
g.add((EX.Uomo, RDFS.subClassOf, EX.Persona))
g.add((EX.Donna, RDFS.subClassOf, EX.Persona))

g.add((EX.si_chiama, RDFS.domain, EX.Persona))
grafo=popola(g, EX)
owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(grafo)
#for s,p,o in grafo:
#    s=s.split("/")[-1].split("#")[-1]
#    o=o.split("/")[-1].split("#")[-1]
#    p=p.split("/")[-1].split("#")[-1]
#    print(s,p,o)
getPersone(grafo, EX)