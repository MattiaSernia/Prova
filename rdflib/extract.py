import rdflib as rdf
from test_edge_addition import test_edge_adding
def extract(grafo, stred, strno):
    inputi= input("Scrivi una frase qui ")
    tokenlist= inputi.split(" ")
    for i in range(len(tokenlist)-2):
        grafo=test_edge_adding(tokenlist[i], tokenlist[i+1], tokenlist[i+2],grafo, stred, strno, "input")
    return grafo