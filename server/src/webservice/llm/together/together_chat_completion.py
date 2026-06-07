from dotenv import load_dotenv
import os
import json
import requests
from webservice.llm.llm_types import Message, ChatRequest

# Load environment variables from .env file
load_dotenv()

TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

class TogetherChatCompletion:
    @staticmethod
    def query(chat_request: ChatRequest) -> Message:
        print("\nQuerying model: " + chat_request["model"] + " ...")

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {TOGETHER_API_KEY}"
        }

        if "stop" not in chat_request:
            chat_request["stop"] = ["<|endoftext|>"] #'["</s>", "###""]',
        
        json_str = json.dumps(chat_request, indent=4)

        response = requests.post(TOGETHER_API_URL, json=chat_request, headers=headers)
        
        if response.status_code != 200:
            return None, response

        output = response.json()

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

        return estimated_num_tokens






