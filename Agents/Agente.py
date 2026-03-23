import ollama
import logging
logger = logging.getLogger(__name__)
class Agente:
    def __init__(self,nome,ruolo):
        self.nome=nome
        self.ruolo=ruolo
        self.memoria=[]
    def rispondi(self, messaggio_interlocutore):
        self.memoria.append({"role":"user", "content": messaggio_interlocutore})
        logging.info(f"Received by {self.nome}: {messaggio_interlocutore}")
        response=ollama.chat(
            model='llama3.2:1b',
            messages=[
                {'role':'system', 'content': f"You're {self.nome}, a {self.ruolo}. Continue this conversation chatting about people you are friend with and making assumption about them. Ask also question to your interlocutor. Your answer must contain at most 2 short phrases"},
                *self.memoria
            ]
        )
        risposta_testo= response['message']['content']
        self.memoria.append({"role": "assistant", "content": risposta_testo})
        logging.info(f"Answer of {self.nome}: {risposta_testo}")
        return risposta_testo
    