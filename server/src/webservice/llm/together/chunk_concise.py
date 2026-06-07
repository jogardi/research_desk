from webservice.llm.together.together_completion import TogetherCompletion
from webservice.llm.llm_types import PromptRequest
import json
from webservice.hparams_config import hpc

# model="zero-one-ai/Yi-34B"
model = hpc().LLM_MODEL_CONCISE
# model = "mistralai/Mistral-7B-v0.1"
# model = "zero-one-ai/Yi-6B"

def generate_concise(chunk: str) -> str:
    prompt = 'For the provided text, make this text concise by eliminating unnecessary words, keeping its meaning intact. Do not generate markdown.\n\nOriginal text: ' + chunk + '\n\n' + 'Concise: '
    
    prompt_request: PromptRequest = { 
        "model": model, 
        "prompt": prompt, 
        "max_tokens": 200, 
        "temperature": 0.1, 
        "top_p": 0.7, 
        "top_k": 50, 
        "repetition_penalty": 1.1
    }
    
    content = TogetherCompletion.query(prompt_request)
    return content

if __name__ == "__main__":
    chunk = "The cities that arose among the people called the Sumerians, who dwelled along the Euphrates River in what is now Iraq, gave humankind its first taste of civilization in about 3500 B.C. The Sumerians recorded the legendary flood story later associated with Noah in Hebrew scripture, and they were said by subsequent Babylonian legend to have arrived in their Mesopotamian realm after a sea journey from some long-forgotten and distant homeland. The Sumerians were an accomplished people. They irrigated and farmed the desert, traded far and wide, expressed themselves artistically in metalwork and stone sculpture, and built extensive temples and palaces. Above all else, the Sumerians could write—creating clay tablets in cuneiform by pressing the characters into wet clay with a wedge-shaped wooden stylus. Eventually Sumeria collapsed under the attack of outsiders even more warlike than they were, but well before that end-time the nation’s ideas, techniques, and methods traveled along the trade routes into other lands."
    concise = generate_concise(chunk)
    print(f"Concise: >{concise}<")



