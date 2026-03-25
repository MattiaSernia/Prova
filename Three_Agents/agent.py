import ollama
import logging
import json
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, name:str, context:str, description:str, data:dict, model:str):
        self.name=name
        self.context=context
        self.data=data
        self.model=model
        self.description=description
        self.memory=[]
        self.coherency=f"""You are a coherency checker, you must check wheter the data provided by the user are consistent with your context.
                        If no error are found answer TRUE, if even one small error has been found anser FALSE.
                        You must answer ONLY with TRUE or FALSE, do not add any explanation.
                        === Data ===
                        {{text}}
                        === Answer ==="""

    def get_prompt(self)->str:
        return f"""You are a specialized assistent called "{self.name}".
        {self.context}

        Answer ONLY using the data provided below.
        If a question concerns information not present in the data, politely let the user know you dont have that data.
        Be concise and precise.
        
        === AVAILABLE DATA ===
        {json.dumps(self.data, indent=2, ensure_ascii=False)}
        === END OF DATA ==="""
    

    def answer(self, message:str)-> str:
        self.memory.append({"role":"user", "content": message})
        logging.info(f"User asked: {message}")
        response=ollama.chat(
            model=self.model,
            messages=[
                {'role':'system', 'content':self.get_prompt()},
                *self.memory
            ]
        )
        textual_answer= response['message']['content']
        self.memory.append({"role": "assistant", "content": textual_answer})
        logging.info(f"System answered: {textual_answer}")
        return(textual_answer)




    def coherency_check(self, text)->bool:
        text=self.coherency.format(text=text)
        logging.info(f"Agent {self.name} received: {text}")
        for attempt in range(3):
            response=ollama.chat(model=self.model,
                    messages=[
                            {'role': 'system', 'content': self.context},
                            {'role': 'user', 'content': text}
                        ])
            
            textual_answer= response['message']['content']
            logging.info(f"Agent {self.name} answered: {textual_answer}")
            cleaned=textual_answer.lower().replace(".","").strip()
            if cleaned== "false":
                  return False
            elif cleaned== "true":
                  return True
        return False
