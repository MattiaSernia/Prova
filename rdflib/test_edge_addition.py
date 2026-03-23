import rdflib as rdf
def test_edge_adding(s, p, o, graph, stredge, strnode, type):
    a=rdf.URIRef(strnode+s.lower())
    b=rdf.URIRef(strnode+o.lower())
    e=rdf.URIRef(stredge+p.lower())
    has_name=rdf.URIRef(stredge+"si_chiama")
    if type=="init":
        graph.add((a, has_name, rdf.Literal(s)))
        graph.add((b, has_name, rdf.Literal(o)))
        graph.add((a, e, b))
        print(f"Aggiunto nodo s p o")
    else:
        if (None,e, None) in graph:
            if (a, e, b) not in graph:
                if (a, None, None) not in graph:
                    graph.add((a, has_name, rdf.Literal(s)))
                    print("Aggiunto nome ad s")
                if (b, None, None) not in graph:
                    graph.add((b, has_name, rdf.Literal(o)))
                    print("Aggiunto nome ad o")
                graph.add((a, e, b))
                print(f"Aggiunto nodo s p o")
        else:
            print("Nodo s p o non aggiunto per condizioni di OWA")
    return graph

