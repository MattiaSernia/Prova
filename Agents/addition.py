import rdflib as rdf

def addition(nodo1, arco, nodo2, grafo, strnode, NS ):
    IRInodo1=rdf.URIRef(strnode + nodo1)
    if (IRInodo1, None, None) not in grafo and (None, None, IRInodo1) not in grafo:
        grafo.add((IRInodo1, NS.is_called, rdf.Literal(nodo1)))
    IRInodo2=rdf.URIRef(strnode + nodo2)
    if (IRInodo2, None, None) not in grafo and (None, None, IRInodo2) not in grafo:
        grafo.add((IRInodo2, NS.is_called, rdf.Literal(nodo2)))
    if (IRInodo1, arco, IRInodo2) not in grafo:
        grafo.add((IRInodo1, arco, IRInodo2))
    return grafo