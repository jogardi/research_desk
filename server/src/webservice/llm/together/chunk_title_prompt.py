from webservice.llm.together.together_completion import TogetherCompletion
from webservice.llm.llm_types import PromptRequest
import json

# model = "togethercomputer/Llama-2-7B-32K-Instruct"
# model = "meta-llama/Llama-3-8b-chat-hf"
# model = "mistralai/Mistral-7B-Instruct-v0.2"
model="openchat/openchat-3.5-1210"
 

chunk = "The cities that arose among the people called the Sumerians, who dwelled along the Euphrates River in what is now Iraq, gave humankind its first taste of civilization in about 3500 B.C. The Sumerians recorded the legendary flood story later associated with Noah in Hebrew scripture, and they were said by subsequent Babylonian legend to have arrived in their Mesopotamian realm after a sea journey from some long-forgotten and distant homeland. The Sumerians were an accomplished people. They irrigated and farmed the desert, traded far and wide, expressed themselves artistically in metalwork and stone sculpture, and built extensive temples and palaces. Above all else, the Sumerians could write—creating clay tablets in cuneiform by pressing the characters into wet clay with a wedge-shaped wooden stylus. Eventually Sumeria collapsed under the attack of outsiders even more warlike than they were, but well before that end-time the nation’s ideas, techniques, and methods traveled along the trade routes into other lands."

prompt = 'Provide a title and summary in JSON format for the following text:\n\n' + chunk

prompt_request: PromptRequest = { 
    "model": model, 
    "prompt": prompt, 
    "max_tokens": 150, 
    "temperature": 0.1, 
    "top_p": 0.7, 
    "top_k": 50, 
    "repetition_penalty": 1.1
}

content = TogetherCompletion.query(prompt_request)

content = content[content.find("{")+1:content.find("}")].strip()
# content = content.replace("'", "\"")
content = "{" + content + "}"
print(f"Content: {content}")
print('-'*50)

content = json.loads(content)
print(content['title'])
print('-'*50)
print(content['summary'])



