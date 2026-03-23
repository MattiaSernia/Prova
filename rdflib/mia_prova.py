import rdflib as rdf
from test_edge_addition import test_edge_adding
from stampa_grafo import stampa
from extract import extract
from queries import get_amico
def mia_prova():
    grafo=rdf.Graph()
    edgestr="http://esempio.org/propieta/"
    nodestr="http://esempio.org/nodo/"
    grafo=test_edge_adding("Bob","e_amico", "Alice", grafo, edgestr, nodestr, "init")
    grafo=test_edge_adding("Gianna","ama", "Franco", grafo, edgestr, nodestr, "init")
    grafo=extract(grafo, edgestr, nodestr)
    stampa(grafo)
    Amici_amico= get_amico("Bob",grafo, edgestr)
