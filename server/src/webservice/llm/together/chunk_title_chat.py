from webservice.llm.together.together_chat_completion import TogetherChatCompletion
from webservice.llm.llm_types import ChatRequest, Message
import json

# model = "togethercomputer/Llama-2-7B-32K-Instruct"
# model = "meta-llama/Llama-3-8b-chat-hf"
model = "mistralai/Mistral-7B-Instruct-v0.2"
# model="openchat/openchat-3.5-1210" 

chunk = "The cities that arose among the people called the Sumerians, who dwelled along the Euphrates River in what is now Iraq, gave humankind its first taste of civilization in about 3500 B.C. The Sumerians recorded the legendary flood story later associated with Noah in Hebrew scripture, and they were said by subsequent Babylonian legend to have arrived in their Mesopotamian realm after a sea journey from some long-forgotten and distant homeland. The Sumerians were an accomplished people. They irrigated and farmed the desert, traded far and wide, expressed themselves artistically in metalwork and stone sculpture, and built extensive temples and palaces. Above all else, the Sumerians could write—creating clay tablets in cuneiform by pressing the characters into wet clay with a wedge-shaped wooden stylus. Eventually Sumeria collapsed under the attack of outsiders even more warlike than they were, but well before that end-time the nation’s ideas, techniques, and methods traveled along the trade routes into other lands."

messages = [
    { "role": "system", "content": "Refer to the following text as context when answering user queries:\n\n" + chunk },
    { "role": "user", "content": "Generate summary of this text in this format: {'summary': '...'}"},
]

chat_request: ChatRequest = {
    "model": model,
    "messages": messages,
    "max_tokens": 150,
    "temperature": 0.1,
    "top_p": 0.7,
    "top_k": 50,
    "repetition_penalty": 1.1
}
message, error_response = TogetherChatCompletion.query(chat_request)
if error_response is not None:
    print(f"Failed to generate chat response. Status code: {error_response.status_code}")
else:
    print(f"Content: {message}")
    print('-'*50)

content = message["content"]
if content.startswith("\n\n"): # togethercomputer/Llama-2-7B-32K-Instruct
    title = content.split("\n\n")[1] 
else:
    # Mistral:
    # content = content.replace("'", "\"")
    # content = json.loads(content)
    # title = content['title']

    content = content[content.find("{")+1:content.find("}")].strip()
    content = content.replace("'", "\"")
    content = "{" + content + "}"
    print(f"Content: {content}")
    content = json.loads(content)
    if 'title' in content:
        title = content['title']
    else:
        title = content['summary']

print(f">>>{title}<<<")
