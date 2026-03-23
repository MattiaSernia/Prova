import ollama
import logging
logger = logging.getLogger(__name__)
class Agent:
    def __init__(self):
        self.memory=[]
    
    def answer(self, message):
        self.memory.append({"role":"user", "content": message})
        print(message)
        logging.info(f"User asked: {message}")
        response=ollama.chat(
            model='phi3.5:latest',
            messages=[
                {'role':'system', 'content': f"The answer must be plain text only, without any formatting, special characters, bullet points, or emphasis."},
                *self.memory
            ]
        )
        textual_answer= response['message']['content']
        self.memory.append({"role": "assistant", "content": textual_answer})
        logging.info(f"System answered: {textual_answer}")
        return(textual_answer)