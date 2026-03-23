import logging
from gui import retrieve_data, retrieve_person
from prova import start, prova
import rdflib

if __name__ == "__main__":
    logger, friend1, friend2, rounds, graph_name= retrieve_data()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(f"{logger}.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    start(friend1, friend2, rounds)
    prova(logger, graph_name)
    person=retrieve_person().strip()
    if person:
        grafo_originale = rdflib.Graph()
        grafo_originale.parse(f"{graph_name}.ttl", format="turtle")
        nodo_target = rdflib.URIRef(f"http://esempio.org/nodo/{person}")
        if (nodo_target, None, None) in grafo_originale or (None, None, nodo_target) in grafo_originale:
            for s, p, o in grafo_originale.triples((nodo_target, None, None)):
                s=str(s)
                s=s.split("/")[-1]
                p=str(p)
                p=p.split("#")[-1]
                o=str(o)
                o=o.split("/")[-1]
                print(f"[ {s} - {p} -> {o}")
            for s, p, o in grafo_originale.triples((None, None, nodo_target)):
                s=str(s)
                s=s.split("/")[-1]
                p=str(p)
                p=p.split("#")[-1]
                o=str(o)
                o=o.split("/")[-1]
                print(f"[ {s} - {p} -> {o}")
