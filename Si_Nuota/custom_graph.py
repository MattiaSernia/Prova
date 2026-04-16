from rdflib import Graph, Namespace, RDF, Literal
from rdflib.term import BNode
from constraintsExtractor import ConstraintsExtractor
from requirementsExtractor import RequirementsExtractor


class Custom_Graph:

    def __init__(self, name:str):
        self.name=name
        self._graph=Graph()
        self._tripletlist=[]
        self._AO = Namespace("https://belval.fr/ao/ontology#")
        self._graph.bind("ao", self._AO)
        self._req_extr=RequirementsExtractor("command-r",0)
        self._cons_extr=ConstraintsExtractor("command-r",0)


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

    
    def triplet_extractor(self, file:str):
        try:
            with open(file, "r", encoding="utf-8") as log:
                rows=log.readlines()
            
        except Exception as e:
            print(f"Exception {e}")
        rows=self._cleanRows(rows)
        messages=isolation(rows, ["User", "asked"])
        for message in messages:
            req_list=self._req_extr.pipe(message)
            con_list=self._cons_extr.pipe(message)


    


    def _cleanRows(self, rows:list)->list:
    i=0
    r2=[]
    while i < len(rows)-1:
        j=i+1
        stringa=rows[i]
        if "INFO" not in stringa.split(" | "):
            while "INFO" not in rows[j].split(" | ") and "AGENT" not in rows[j].split(" | "):
                if rows[j]!= "\n":
                    stringa+= "\n"+rows[j]
                i=j
                j+=1
            r2.append(stringa.strip())
        i+=1
    if "AGENT" in stringa.split(" | ") and "INFO" not in rows[len(rows)-1].split(" | "): r2.append(rows[len(rows)-1])
    return r2

    def isolation(self, messages:str, iso:list)->list:
        isolated=[]
        for message in messages:
            textual=' | '.join(message.split(" | ")[2:])
            intestation=textual.split(":")[0].split(' ')
            to_iso=True
            for element in iso:
                if element not in intestation:
                    to_iso=False
            if to_iso==True:
                to_add=":".join(textual.split(":")[1:])
                isolated.append(to_add)
        return isolated


if __name__=="__main__":
    name=input("insert the name of the graph: ")
    graph=Custom_Graph(name)
    graph.load("outputConstraints.txt", "constraints")
    graph.load("outputRequirements.txt", "requirements")
    graph.savegraph()