from rdflib import Graph, ConjunctiveGraph, Namespace, URIRef, Literal, RDF, Namespace
from rdflib.namespace import RDF, XSD, PROV

EX   = Namespace("http://example.org/ontologia#")
EDGE = Namespace("http://example.org/edge/")
NODE = Namespace("http://example.org/node/")

g=ConjunctiveGraph()

g.parse("Total_nokg.trig", format="trig")
dizionario={}
prop=[]
f=open("total_nokg.txt", "w")
for subj in g.subjects(RDF.type, EX.Proposal):
    s_uri = next(g.objects(subj, RDF.subject), None)
    proposal_subject=s_uri.split("/")[-1].replace("_", " ")
    for p, o in g.predicate_objects(subj):
        if str(p).startswith(str(EDGE)):
                    pred = p.split("/")[-1].replace("_", " ")
                    obj  = o.split("/")[-1].replace("_", " ")
                    break
    f.write("PROPOSAL\n")
    f.write(f"{proposal_subject} {pred} {obj}\n")

    sati_nodes = list(g.objects(subj, EX.Satisfies))
    lista_req=[]
    lista_con=[]
    for node in sati_nodes:
        s_uri1 = next(g.objects(node, RDF.subject), None)
        proposal_subject1=s_uri1.split("/")[-1].replace("_", " ")
        for p, o in g.predicate_objects(node):
            if str(p).startswith(str(EDGE)):
                        pred = p.split("/")[-1].replace("_", " ")
                        obj  = o.split("/")[-1].replace("_", " ")
                        break
        if (node, RDF.type, EX.Requirement) in g:
            lista_req.append(f"{proposal_subject1} {pred} {obj}")
        if (node, RDF.type, EX.Constraint)in g:
            lista_con.append(f"{proposal_subject1} {pred} {obj}")
    f.write("\nREQUIREMENTS\n")
    for element in lista_req:
        f.write(element+"\n")
    f.write("\nCONSTRAINTS\n")
    for element in lista_con:
        f.write(element+"\n")

    f.write("\n")

    sati_nodes = list(g.objects(subj, EX.Does_Not_Satisfies))
    lista_req1=[]
    lista_con1=[]
    for node in sati_nodes:
        s_uri1 = next(g.objects(node, RDF.subject), None)
        proposal_subject1=s_uri1.split("/")[-1].replace("_", " ")
        for p, o in g.predicate_objects(node):
            if str(p).startswith(str(EDGE)):
                        pred = p.split("/")[-1].replace("_", " ")
                        obj  = o.split("/")[-1].replace("_", " ")
                        break
        if (node, RDF.type, EX.Requirement) in g:
            lista_req1.append(f"{proposal_subject1} {pred} {obj}")
        if (node, RDF.type, EX.Constraint)in g:
            lista_con1.append(f"{proposal_subject1} {pred} {obj}")
    f.write("NOT REQUIREMENTS\n")
    for element in lista_req1:
        f.write(element+"\n")
    f.write("\nNOT CONSTRAINTS\n")
    for element in lista_con1:
        f.write(element+"\n")

    f.write("\n")

    dizionario[f"{proposal_subject} {pred} {obj}"]={
        "satisfied_requirement":lista_req,
        "satisfied_constraint":lista_con,
        "not_satisfied_requirement":lista_req1,
        "not_satisfied_constraint":lista_con1,
    }

f.close()
    
    