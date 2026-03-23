import rdflib

grafo_originale = rdflib.Graph()
grafo_originale.parse("grafo1.ttl", format="turtle")

subgraph = rdflib.Graph()
nodo_target = rdflib.URIRef("http://esempio.org/nodo/Liam")
nodo_target1= rdflib.URIRef("http://esempio.org/nodo/Message_5")
nodo_target2= rdflib.URIRef("http://esempio.org/nodo/Message_8")
for s, p, o in grafo_originale.triples((nodo_target, None, None)):
    subgraph.add((s, p, o))
for s, p, o in grafo_originale.triples((None, None, nodo_target)):
    subgraph.add((s, p, o))
for s, p, o in grafo_originale.triples((nodo_target1, None, None)):
    subgraph.add((s, p, o))
for s, p, o in grafo_originale.triples((nodo_target2, None, None)):
    subgraph.add((s, p, o))
subgraph.serialize(destination="subgraph.ttl", format="turtle")