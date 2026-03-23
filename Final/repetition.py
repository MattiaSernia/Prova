from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from triplet import Triplet
def td_idf(lista:list):
    unic_nodes=set()
    for t in lista:
        unic_nodes.add(t.getSubject())
        unic_nodes.add(t.getObject())

    nodes=[{'id':i, "label":m} for i, m in enumerate(sorted(unic_nodes))]
    
    labels=[n["label"].lower() for n in nodes]

    vectorizer=TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3,5),
        min_df=1,
        sublinear_tf=True
    )
    tfidf_matrix=vectorizer.fit_transform(labels) #divide tutte le stringe nei loro trigrammi, quadrigrammi e pentagrammi
    tfidf_sim=cosine_similarity(tfidf_matrix) #applica il cosine similarity a tutte le coppie di stringhe. tdidf_sim[i][j] ti dice la cosine similarity tra stringa i e j
    candidates=[]
    n=len(nodes)
    for i in range(n-1):
        for j in range(i+1, n):
            score=round(tfidf_sim[i][j])
            if score>0.7:
                candidates.append({
                    "id_a": i, "label_a": nodes[i]["label"],
                    "id_b": j, "label_b": nodes[j]["label"],
                    "score":score
                    })
    for p in candidates:
        print(f"{p['label_a']}\n{p['label_b']}\n{p['score']}\n")
if __name__=="__main__":
    lista=[]
    with open("triplets.txt", "r", encoding="utf-8") as t:
        righe=t.readlines()
        for riga in righe:
            riga=riga.strip("\n").strip("[ ").strip(" ]").split(" | ")
            lista.append(Triplet(riga[0], riga[1], riga[2]))
    td_idf(lista)