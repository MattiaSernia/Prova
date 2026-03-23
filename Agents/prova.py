from Agente import Agente
import logging
from custom_graph import custom_Graph
from text_handling import text_handling
def start(friend1, friend2, turns):
    logging.info("Multi agent system start")

    agente_a = Agente("Bob", f"Universitary student named Bob friend of {friend1}. You only know the people mentioned before, if you don't know somebody just state it. You are talking with Frank")
    agente_b = Agente("Frank", f"Universitary student named Frank friend of {friend2}. You only know the people mentioned before, if you don't know somebody just state it. You are talking with Bob")

    messaggio = "Hey Frank, how is it going?"
    for i in range(int(turns)):
        logging.info(f"--- Turn {i+1} ---")
        messaggio= agente_b.rispondi(f"{messaggio}")
        messaggio= agente_a.rispondi(f"{messaggio}")
    logging.info("Conversation ended")

def prova(logger, nome):
    custom_graph=custom_Graph()
    custom_graph.ontology()
    with open(f"{logger}.log", "r", encoding="utf-8") as f:
        righe = f.readlines()
        conv=open("conversation.txt", "w", encoding="utf-8")
        for riga in righe:
            testo=riga.strip()
            if "Received" in testo or "Answer" in testo:
                nodemxg, mxg, date = text_handling(testo)
                conv.write(mxg+"\n")
                custom_graph.msg_addition(nodemxg, mxg)
                custom_graph.additional_info(nodemxg, mxg, date)
        conv.close()
    custom_graph.vuoto_inconmensurabile()
    custom_graph.saveGraph(nome)
    
if __name__== "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler("agents_session_new2.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )