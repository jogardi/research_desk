import requests
import json
import os
from dotenv import load_dotenv

from webservice.llm.llm_types import Message, ChatRequest

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

class OpenAIChatCompletion:
    @staticmethod
    def query(chat_request: ChatRequest) -> Message:
        print("\nQuerying model: " + chat_request["model"] + " ...")
        
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        if "stop" not in chat_request:
            chat_request["stop"] = ["<|endoftext|>"] #'["</s>", "###""]',
        
        print("Request:")
        json_str = json.dumps(chat_request, indent=4)
        print(json_str)

        # delete unsupported 'repetition_penalty' and 'top_k' from chat_request:
        del chat_request['repetition_penalty']
        del chat_request['top_k']

        # Send the request to the OpenAI API
        response = requests.post(OPENAI_API_URL, json=chat_request, headers=headers)

        if response.status_code != 200:
            return None, response
        
        output = response.json()

        json_str = json.dumps(output, indent=4)
        print(json_str)
        print('-'*50)

        message_content = output['choices'][0]['message']['content']
        message: Message =  { "role": "assistant", "content": message_content.strip()}
        return message, None
    
    @staticmethod
    def estimated_tokens(text: str) -> int:
        # TODO: Implement this function with nltk.
        # Define the average ratio of tokens to words
        TOKENS_PER_WORD_RATIO = 1.5 # 1.5 tokens per word - this is an average value across different language models (1.2 - 1.5)
        
        # Estimate the number of tokens based on the number of words
        num_words = len(text.split()) # Split the text into words and count them
        estimated_num_tokens = int(num_words * TOKENS_PER_WORD_RATIO) # Rounded to the nearest integer
        print(f'Estimated tokens: {estimated_num_tokens}')
        return estimated_num_tokens

if (__name__ == "__main__"):
    # Example usage
    user_query = "What is the capital of France?"
    chat_request: ChatRequest = { 
        "model": "gpt-4o", 
        "messages": [{"role": "user", "content": "What is the capital of France?"}], 
        "max_tokens": 1000,
        "temperature": 0.1, 
        "top_p": 0.7, 
        "top_k": 50, 
        "repetition_penalty": 1.1
    }
    message: Message = OpenAIChatCompletion.query(chat_request)

    print(message)
