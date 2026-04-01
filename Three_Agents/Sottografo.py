import rdflib
from rdflib import RDF

grafo_originale = rdflib.Graph()
grafo_originale.parse("Pippolo.ttl", format="turtle")

subgraph = rdflib.Graph()
nodo_target = rdflib.URIRef("http://example.org/node/message5")
for bnode in grafo_originale.subjects(RDF.object, rdflib.URIRef("http://example.org/node/electrician")):
    if isinstance(bnode, rdflib.BNode):
        for s, p, o in grafo_originale.triples((bnode, None, None)):
            subgraph.add((s, p, o))
        for s, p, o in grafo_originale.triples((None, None, bnode)):
            subgraph.add((s, p, o))
for s, p, o in grafo_originale.triples((nodo_target, None, None)):
    subgraph.add((s, p, o))
for s, p, o in grafo_originale.triples((None, None, nodo_target)):
    subgraph.add((s, p, o))
subgraph.serialize(destination="subgraph.ttl", format="turtle")