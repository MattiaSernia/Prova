from fastcoref import FCoref
class CoreferenceResolver: ###-------- Risolvere problema pronomi negli head -----------
    ## Si usa s2e+spanBERT, Lai et al. 2022
    ## Fonte surveyoncoreferenceresolution.pdf
    def __init__(self, device:str="cpu"):
        self.model=FCoref(device=device)
        self.pronouns={"he", "she", "it", "they", "him", "her", "them", 
                       "his", "hers", "its", "their", "theirs",
                        "himself", "herself", "itself", "themselves", "this","that"}
    def clean(self,text:str)->str:
        text=text.replace("\n\n\n", " ").replace("\n\n", " ").replace("\n", " ")
        return text
    
    def resolve(self, text:str)->str:
        text=self.clean(text)
        predictions=self.model.predict(text) #ritorna il testo e poi una lista di liste che rappresentano i cluster
        clusters_str=predictions.get_clusters(as_strings=True) #prendo i cluster da pred
        clusters_span= predictions.get_clusters(as_strings=False) #per ogni parola nel cluster mi dice dove inizia e dove finisce nel testo
        cleaned_text=self._replace_pronouns(text, clusters_span, clusters_str)
        return cleaned_text
    
    def _replace_pronouns(self, text, clusters_span, cluster_str):
        replacements={} #lista che conterra come chiave il carattere da cui partire per cambiare e come chiave (end, e la parola da rimpiazzare)

        for spans, strings in zip(clusters_span,cluster_str):
            if len(spans)<2: #vuol dire che il cluster contiene solo un'entita
                continue

            head=strings[0] #usiamo solo la prima occorrenza
            for span, string in zip(spans[1:], strings[1:]): #saltiamo la prima occorrenza poiche è quella canonica
                replacements[span[0]]=[span[1],head]
        
        if not replacements:
            return text
        
        chars=list(text) #tokenizziamo il testo
        for start in sorted(replacements.keys(), reverse=True): #Facciamo replacement perché cosi non modifichiamo la posizione dei caratteri prima
            chars[start:replacements[start][0]]=list(replacements[start][1])
        
        return "".join(chars)


