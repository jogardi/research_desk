import os
from types import SimpleNamespace as Sn
from webservice.hparams_config import hpc
from webservice.models import defaultModel
import dotenv
dotenv.load_dotenv()
import litellm

# model="zero-one-ai/Yi-34B"
# model="mistralai/Mistral-7B-v0.1"
# model = "mistralai/Mixtral-8x22B"
# model = "zero-one-ai/Yi-6B"
# model = "mistralai/Mistral-7B-Instruct-v0.3"
# model = "moonshotai/Kimi-K2-Instruct"
# model = 'cerebras/qwen-3-235b-a22b-instruct-2507'
model = 'openrouter/gpt-oss-120b'

def generate_title(text: str, user_query: str | None = None) -> str:
    
    # Query the language model for the summary
    # estimated_tokens = TogetherChatCompletion   .estimated_tokens(text)
    # estimated_tokens = int(estimated_tokens * 1.05)
    # estimated_tokens = 4096 - estimated_tokens - 100
    print("query", user_query)
    if hpc().USE_QUERY_FOR_TITLE:
        # instruction = f"The user just entered this search query: {user_query}. "
        instruction = f'''Create a succinct title for the following search result. 
The title must be at least 5 words long, concise, descriptive, and no longer than 14 words. 
Return only the title without any additional text or labels (like \"Title: \”). 
Remember, some title MUST be provided even if the text seems complex or unclear. 
While, it may make sense to deprioritize information that is less relevant to the user query, DO NOT repeat what is already in the user query ("{user_query}") because that would be redundant. 
Prefer using specific precise technical terms that appear in the search result over vague general words. 
Rare words tend to be more helpful for narrowing down what the search result is about and differentiating from other search results.'''.replace('\n', ' ')
        instruction += '\n\nSearch result: '

        # if user_query:
        #     instruction += " For context, you are given the user's query but your job is to make a title for the search result."# so that you can make a title that explain why the search result is relevant to the user query provided."

        user_content = instruction 
            # user_content += f'User query: "{user_query}"\n\nSearch result: '
        user_content += text
    else:
        user_content = "Create a succinct title for the following text. The title must be at least three words long, concise, descriptive, and no longer than 10 words. Return only the title without any additional text or labels (like \"Title: \"). Remember, some title MUST be provided even if the text seems complex or unclear:\n\n" + text

    messages = [{"role": "user", "content": user_content}]

    try:
        resp = litellm.completion_with_retries(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=1000,
            fallbacks=['openai/gpt-4o']
        )
        title = resp.choices[0].message.content or ""
    except Exception as e:
        print(f"Error: {e}")
        return None, Sn(status_code=500, error=str(e))

    if len(title) == 0:
        title = "Untitled"
    if (title.startswith("Title:")):
        title = title[7:]
    return title, None

if __name__ == "__main__":
    text = "The cities that arose among the people called the Sumerians, who dwelled along the Euphrates River in what is now Iraq, gave humankind its first taste of civilization in about 3500 B.C. The Sumerians recorded the legendary flood story later associated with Noah in Hebrew scripture, and they were said by subsequent Babylonian legend to have arrived in their Mesopotamian realm after a sea journey from some long-forgotten and distant homeland. The Sumerians were an accomplished people. They irrigated and farmed the desert, traded far and wide, expressed themselves artistically in metalwork and stone sculpture, and built extensive temples and palaces. Above all else, the Sumerians could write—creating clay tablets in cuneiform by pressing the characters into wet clay with a wedge-shaped wooden stylus. Eventually Sumeria collapsed under the attack of outsiders even more warlike than they were, but well before that end-time the nation’s ideas, techniques, and methods traveled along the trade routes into other lands."
    title, error_response = generate_title(text)
    if error_response is not None:
        print(f"Failed to generate title. Status code: {error_response.status_code}")
    else:
        print(f"Title is: {title}")
        # print('-'*50)
        # print(text)




