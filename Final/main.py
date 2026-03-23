from Agent import Agent
from CoreferenceResolver import CoreferenceResolver
from tripletExtractor import TripletExtractor
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("test.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
def main():
    agent=Agent()
    coref=CoreferenceResolver()
    tri_ex=TripletExtractor('phi3.5:latest', 0)
    total_tri=[]
    with open("Questions.txt", "r", encoding="utf-8") as f:
        righe = f.readlines() 
        for riga in righe:
            riga=riga.strip("\n")
            text=agent.answer(riga)
            text=coref.resolve(text)
            answer_triplets= tri_ex.pipe(text)
            total_tri.extend(answer_triplets)
    tripl=open("triplets.txt", "w", encoding="utf-8")
    for t in total_tri:
        tripl.write(t.toString()+ "\n")
    tripl.close()
    


if __name__=="__main__":
    main()
    