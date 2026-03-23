import ollama

def is_informative(stringa:str)->bool:
        print(stringa)
        prompt=f"""Tell if the user question is satisfied:
           Does the triplet {stringa} provide useful information?
            Answer:"""
        for attempt in range(3):
            response=ollama.chat(
                model='phi3.5:latest',
                messages=[
                {'role':'system', 'content': f"""You are a True/False classifier for knowledge graph triplets.
                                                A triplet is informative if it states a specific, verifiable fact about an entity.
                                                A triplet is NOT informative if it is:
                                                - too vague (e.g. "Marie Curie | is | often referred to as")
                                                - incomplete (e.g. "techniques | were | for measuring radioactivity levels")
                                                - a fragment without a clear object

                                                Respond ONLY with True or False. No explanation."""},
                {'role': 'user', 'content': prompt}
                ]
            )
            textual_response=response['message']['content'].split(" ")[0].strip()
            cleaned=textual_response.lower().replace(".","").strip()
            if cleaned== "false":
                  print("False")
                  return False
            elif cleaned== "true":
                  print("True")
                  return True
            print(attempt)
            
        print(cleaned)
        return 

if __name__=="__main__":
    f=open("trash.txt", "w", encoding="utf-8")
    with open("triplets.txt", "r", encoding="utf-8") as t:
        righe = t.readlines() 
        for riga in righe:
            riga=riga.strip()
            if not is_informative(riga):
                f.write(riga+"\n")
    f.close()
    


