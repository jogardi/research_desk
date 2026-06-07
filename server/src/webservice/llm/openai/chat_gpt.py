import os

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def chat(messages, model="gpt-3.5-turbo-0125", temperature=0.3, top_p=1.0, n=1, stream=False, 
        max_tokens=None, presence_penalty=0.0, frequency_penalty=0.0, user=None):
        response = openai.ChatCompletion.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        top_p=top_p,
                        n=n,
                        stream=stream,
                        max_tokens=max_tokens,
                        presence_penalty=presence_penalty,
                        frequency_penalty=frequency_penalty,
                        user=user
                    )

        if stream:
            reply = ""
            for chunk in response:
                reply += chunk["choices"][0]["delta"].get("content", "")
        else:
            reply = response["choices"][0]["message"]["content"]

        return reply

# params:
# temperature (float, default=1.0): Controls the randomness of the generated text. Higher values (up to 2.0) make the output more random, while lower values (down to 0.0) make it more deterministic.
# top_p (float, default=1.0): Nucleus sampling parameter that controls the diversity of the generated text. A value of 1.0 means no filtering, while a value less than 1.0 filters out less probable tokens.
# n (int, default=1): The number of completions to generate for each prompt.
# stream (bool, default=False): Whether to stream the response back or wait until the entire response is generated.
# max_tokens (int, optional): The maximum number of tokens to generate in the response. By default, it's set to 4096 for gpt-3.5-turbo-0125 and 4097 for gpt-3.5-turbo-instruct.
# presence_penalty (float, default=0.0): A value between -2.0 and 2.0 that controls the likelihood of repeating the same tokens in the generated text.
# frequency_penalty (float, default=0.0): A value between -2.0 and 2.0 that controls the likelihood of repeating the same tokens across different completions.
#user (str, optional): A unique identifier representing your end-user, which can help OpenAI to monitor and detect abuse.
