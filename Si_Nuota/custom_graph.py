from rdflib import Graph, Namespace, RDF, Literal
from rdflib.term import BNode


class Custom_Graph:

    def __init__(self, name:str):
        self.name=name
        self._graph=Graph()
        self._tripletlist=[]
        self._AO = Namespace("https://belval.fr/ao/ontology#")
        self._graph.bind("ao", self._AO)



    def load(self, file:str, gtype:str) -> None:
        with open(file, "r", encoding="utf-8") as f:
            lines=f.readlines()
        for line in lines:
            self._add(line, gtype)



    def _add(self, line:str, gtype:str) -> None:
        triplet=line.strip("\n").strip(".").split(" | ")
        match gtype:
            case "constraints":
                if len(triplet) == 4:
                    if triplet[1] and triplet[2] and triplet[3]:
                        if f"{triplet[1]} | {triplet[2]} | {triplet[3]}" not in self._tripletlist:
                            stmt=BNode()
                            self._graph.add((stmt, RDF.type, self._AO.Contraint))
                            self._graph.add((stmt, self._AO.subject, Literal(triplet[1])))
                            self._graph.add((stmt, self._AO.predicate, Literal(triplet[2])))
                            self._graph.add((stmt, self._AO.object, Literal(triplet[3])))
                            if triplet[0]:
                                if triplet[0]!= None:
                                    self._graph.add((stmt, self._AO.constraintType, Literal(triplet[0])))
                            self._tripletlist.append(f"{triplet[1]} | {triplet[2]} | {triplet[3]}")
            case "requirements":
                if len(triplet) == 5:
                    if triplet[2] and triplet[3] and triplet[4]:
                        if f"{triplet[2]} | {triplet[3]} | {triplet[4]}" not in self._tripletlist:
                            stmt=BNode()
                            self._graph.add((stmt, RDF.type, self._AO.Requirement))
                            self._graph.add((stmt, self._AO.subject, Literal(triplet[2])))
                            self._graph.add((stmt, self._AO.predicate, Literal(triplet[3])))
                            self._graph.add((stmt, self._AO.object, Literal(triplet[4])))
                            if triplet[0]:
                                if triplet[0]!= None:
                                    self._graph.add((stmt, self._AO.category, Literal(triplet[0])))
                            if triplet[1]:
                                if triplet[1]!= None:
                                    self._graph.add((stmt, self._AO.priority, Literal(triplet[1])))
                            self._tripletlist.append(f"{triplet[2]} | {triplet[3]} | {triplet[4]}")

    def savegraph(self) -> None:
        self._graph.serialize(destination=f"{self.name}.ttl", format="turtle", encoding="utf-8")


if __name__=="__main__":
    name=input("insert the name of the graph: ")
    graph=Custom_Graph(name)
    graph.load("outputConstraints.txt", "constraints")
    graph.load("outputRequirements.txt", "requirements")
    graph.savegraph()