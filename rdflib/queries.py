from rdflib import RDF
def get_amico(name, grafo, uri_base):

    query = f"""
    SELECT DISTINCT ?nomeAmicoAmico 
    WHERE {{
        ?bob <{uri_base}si_chiama> "{name}" .
        ?bob <{uri_base}e_amico> ?intermediario .
        ?intermediario <{uri_base}e_amico> ?amicoAmico .
        ?amicoAmico <{uri_base}si_chiama> ?nomeAmicoAmico .
        FILTER (?nomeAmicoAmico != "{name}")
    }}
    """
    risultati = grafo.query(query)
    for row in risultati:
        print(f"Amico di un amico di Bob: {row.nomeAmicoAmico}")
    return

def getPersone(grafo, NS):
    query = f"""
    PREFIX ex: <{NS}>
    SELECT DISTINCT ?nome
    WHERE {{
        ?persona rdf:type ex:Persona .
        ?persona ex:si_chiama ?nome
    }}
    """
    risultati=grafo.query(query, initNs={'rdf' : RDF})
    for row in risultati:
        print(f"{row.nome}")
    return