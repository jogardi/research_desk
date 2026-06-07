from webservice.llm.together.together_completion import TogetherCompletion
from webservice.llm.llm_types import PromptRequest
import json

# model="zero-one-ai/Yi-34B"

model = "mistralai/Mistral-7B-v0.1"
# model = "zero-one-ai/Yi-6B"

def generate_title(chunk: str) -> str: 
    # prompt = 'Provide a title for the following text: ' +  chunk + '\n\n' + 'Generate a title for the text above.'
    prompt = (
        "You are an expert title generator. Your task is to read the following text and generate a concise and descriptive title. "
        "The title should be one short phrase that accurately captures the main topic of the text. "
        "Here is the text:\n\n"
        f"{chunk}\n\n"
        "Title:"
    )
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
    content = content.strip()
    # print(f"Content: {content}")
    if (content.startswith("Title:")):
        title = content[content.find(":")+1:].strip()
    else:
        title = content
    return title
    

if __name__ == "__main__":
    chunk = "The cities that arose among the people called the Sumerians, who dwelled along the Euphrates River in what is now Iraq, gave humankind its first taste of civilization in about 3500 B.C. The Sumerians recorded the legendary flood story later associated with Noah in Hebrew scripture, and they were said by subsequent Babylonian legend to have arrived in their Mesopotamian realm after a sea journey from some long-forgotten and distant homeland. The Sumerians were an accomplished people. They irrigated and farmed the desert, traded far and wide, expressed themselves artistically in metalwork and stone sculpture, and built extensive temples and palaces. Above all else, the Sumerians could write—creating clay tablets in cuneiform by pressing the characters into wet clay with a wedge-shaped wooden stylus. Eventually Sumeria collapsed under the attack of outsiders even more warlike than they were, but well before that end-time the nation’s ideas, techniques, and methods traveled along the trade routes into other lands."
    title = generate_title(chunk)
    print(f"Title: >{title}<")




