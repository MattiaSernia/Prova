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
        self.coherency="""### Role: Coherency Checker
            Verify if the provided Data is strictly consistent with your Context. 

            **Decision Criteria:**
            - Return "TRUE" only if the Data contains NO errors, contradictions, or hallucinations relative to the Context.
            - Return "FALSE" if even a single detail is inconsistent, incorrect, or missing from the Context.

            ### Data to Verify:
            {{text}}

            ### Constraint:
            Respond ONLY with "TRUE" or "FALSE". Do not include any explanation or extra text.

            Result:"""

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
