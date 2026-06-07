from dotenv import load_dotenv
import os
import json
import requests
from webservice.llm.llm_types import PromptRequest

# Load environment variables from .env file
load_dotenv()

TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
TOGETHER_API_URL = "https://api.together.xyz/v1/completions"

class TogetherCompletion:
    @staticmethod
    def query(prompt_request: PromptRequest) -> str:
        print("\nQuerying model: " + prompt_request["model"] + " ...")

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {TOGETHER_API_KEY}"
        }

        if "stop" not in prompt_request:
            prompt_request["stop"] = ["<|endoftext|>"] #'["</s>", "###""]',

        response = requests.post(TOGETHER_API_URL, json=prompt_request, headers=headers)
        
        if response is None:
            print("No response")
            return None
        elif response.status_code != 200:
            print(f"Error: {response.status_code}")
            try:
                print(response.json())
            except Exception as e:
                print(f"Failed to parse JSON from response: {e}")
            return None

        output = response.json()

        json_str = json.dumps(output, indent=4)
        print(json_str)
        print('-'*50)

        message_content = output['choices'][0]['text']
        return message_content.strip()
    
    @staticmethod
    def estimated_tokens(text: str) -> int:
        # Define the average ratio of tokens to words
        TOKENS_PER_WORD_RATIO = 1.5 # 1.5 tokens per word - this is an average value across different language models (1.2 - 1.5)
        
        # Estimate the number of tokens based on the number of words
        num_words = len(text.split()) # Split the text into words and count them
        estimated_num_tokens = int(num_words * TOKENS_PER_WORD_RATIO) # Rounded to the nearest integer

        return estimated_num_tokens
        










