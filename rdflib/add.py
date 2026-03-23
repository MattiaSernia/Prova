import rdflib as rdf
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import OWL, RDFS
def add_person(grafo, NS, testo):
    persona=testo.split(" ")
    nodo= rdf.BNode()
    grafo.add((nodo, NS.si_chiama, rdf.Literal(persona[0])))
    if len(persona) > 1:
        if persona[1]=="Uomo":
            grafo.add((nodo, RDF.type, NS.Uomo))
        else:
            grafo.add((nodo, RDF.type, NS.Donna))
    return grafo
def popola(grafo, NS):
    with open("Persone.txt", "r", encoding="utf-8") as f:
        righe = f.readlines() 
        for riga in righe:
            testo=riga.strip()
            grafo=add_person(grafo, NS, testo)
    return grafo

