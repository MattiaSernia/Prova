import rdflib
from triplet import Triplet
class customGraph():
    def __init__(self):
        self.grafo=rdflib.Graph()
        self.nodeUri="http://esempio.org/node/"
        self.edgeUri="http://esempio.org/edge/"
    
    def add(self, triplet):
        s=rdflib.URIRef(self.nodeUri+triplet.getSubject().strip().replace(" ", "_"))
        p=rdflib.URIRef(self.edgeUri+triplet.getPredicate().strip().replace(" ", "_"))
        o=rdflib.URIRef(self.nodeUri+triplet.getObject().strip().replace(" ", "_"))
        if (s,p,o) not in self.grafo:
            self.grafo.add((s,p,o))

    def saveGraph(self,name:str):
        self.grafo.serialize(destination=f"{name}.ttl", format="turtle", encoding="utf-8")

    def findEdges(self, node_name:str)->list:
        so=rdflib.URIRef(self.nodeUri+node_name.strip().replace(" ", "_"))
        if (so, None, None) in self.grafo or (None, None, so) in self.grafo:
            lista=[]
            for s, p, o in self.grafo.triples((so, None, None)):
                s=s.split("/")[-1].replace("_", " ")
                p=p.split("/")[-1].replace("_", " ")
                o=o.split("/")[-1].replace("_", " ")
                lista.append(Triplet(s,p,o))
            for s, p, o in self.grafo.triples((None, None, so)):
                s=s.split("/")[-1].replace("_", " ")
                p=p.split("/")[-1].replace("_", " ")
                o=o.split("/")[-1].replace("_", " ")
                lista.append(Triplet(s,p,o))
            return lista
        return None


if __name__=="__main__":
    c_graph=customGraph()
    with open("triplets.txt", "r", encoding="utf-8") as doc:
        rows=doc.readlines()
        for row in rows:
            row=row.strip("\n").strip("[ ").strip(" ]").split(" | ")
            c_graph.add(Triplet(row[0], row[1], row[2]))
    c_graph.saveGraph("vediamo")
    connection=c_graph.findEdges("Marie Curie")
    if connection:
        for tri in connection:
            print(tri.toString())



