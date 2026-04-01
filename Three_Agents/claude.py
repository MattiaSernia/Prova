import rdflib

# 1. Caricamento
grafo_originale = rdflib.Graph()
grafo_originale.parse("Pippolo.ttl", format="turtle")

# 2. Definizione della Query
# Usiamo CONSTRUCT per creare un sotto-grafo basato sui pattern
query_subgraph = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

CONSTRUCT {
    # Includiamo le triple che entrano o escono dal nodo_target
    <http://example.org/node/message3> ?p1 ?o1 .
    ?s1 ?p2 <http://example.org/node/message3> .

    # Includiamo le triple dei nodi "intermediate" che puntano all'elettricista
    ?intermediate ?p3 ?o3 .
    ?s3 ?p4 ?intermediate .
}
WHERE {
    {
        # Pattern 1: Triple dirette di message3
        <http://example.org/node/message3> ?p1 ?o1 .
    }
    UNION
    {
        # Pattern 2: Triple che puntano a message3
        ?s1 ?p2 <http://example.org/node/message3> .
    }
    UNION
    {
        # Pattern 3: Nodi collegati a message3 che hanno come oggetto l'elettricista
        # Cerchiamo nodi ?intermediate connessi a message3 (in entrata o uscita)
        { <http://example.org/node/message3> ?p_conn ?intermediate }
        UNION
        { ?intermediate ?p_conn <http://example.org/node/message3> }

        # Condizione: l'intermediate deve avere l'elettricista come rdf:object
        ?intermediate rdf:object <http://example.org/node/electrician> .

        # Per questi nodi, prendiamo tutto ciò che entra o esce
        { ?intermediate ?p3 ?o3 }
        UNION
        { ?s3 ?p4 ?intermediate }
    }
}
"""

# 3. Esecuzione
# Il risultato di una query CONSTRUCT è un oggetto rdflib.Graph
subgraph = grafo_originale.query(query_subgraph).graph

# 4. Salvataggio
subgraph.serialize(destination="subgraph.ttl", format="turtle")

print(f"Sottografo creato con {len(subgraph)} triple.")