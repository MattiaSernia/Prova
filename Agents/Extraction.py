import ollama
import json
import re

def Extraction(message):
    # Clean the system prefixes to prevent the small model from confusing them with names
    cleaned_message = re.sub(r"^(?:Answer of|Received by) [a-zA-Z]+: ", "", message).strip()
    
    # Extract the speaker to explicitly tell the model who is talking
    speaker_match = re.search(r"^(?:Answer of|Received by) ([a-zA-Z]+):", message)
    speaker_context = f"The speaker is {speaker_match.group(1)}. " if speaker_match else ""
    system_prompt = """You are a strict relationship extractor. Extract relationships where two human characters know each other.

Strict Rules:

1. Output ONLY a valid JSON object: {"triplets": [["PersonA", "knows", "PersonB"]]}
2. ONLY extract relationships between HUMAN names. NEVER use places (e.g., Hawaii, Europe).
3. Do not extract system words or phrases.
4. If there are no clear human relationships mentioned, output {"triplets": []}

Example 1:
Text: The speaker is Bob. We actually went to Hawaii, it was amazing! I heard Matthew and Liam are planning a trip.
JSON Output: {"triplets": [["Bob", "knows", "Matthew"], ["Bob", "knows", "Liam"], ["Matthew", "knows", "Liam"]]}

Example 2:
Text: The speaker is Frank. Hey, how is it going?
JSON Output: {"triplets": []}

Example 3:
Text: The speaker is Bob. I'll reach out to John and Eleanor.
JSON Output: {"triplets": [["Bob", "knows", "John"], ["Bob", "knows", "Eleanor"], ["John", "knows", "Eleanor"]]}
"""

    response = ollama.chat(
        model='llama3.2:1b',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"Text: {speaker_context}{cleaned_message}\nJSON Output:"}
        ],
        format='json',
        options={
            'temperature': 0.0,
            'top_p': 0.1,
            'num_predict': 100
        }
    )
    
    try:
        data = json.loads(response['message']['content'])
        triplets = data.get("triplets", [])
        
        output_lines = []
        
        for t in triplets:
            if len(t) == 3:
                # Sanity check to filter out remaining hallucinations
                if t[0] != t[2] and t[0] in message and t[2] in message and t[1]=="knows":
                    output_lines.append([t[0], t[1], t[2]])
                
        final_output = output_lines
        print(message)
        print(final_output)
        return final_output
    except json.JSONDecodeError:
        return ""