from rdflib import URIRef
def stampa(grafo):
    for s,o,p in grafo:
        if isinstance(s, URIRef):
            s=s.split("/")[-1]
        if isinstance(p, URIRef):
            p=p.split("/")[-1]
        if isinstance(o, URIRef):
            o=o.split("/")[-1]
        print(s,o,p)