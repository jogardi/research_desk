The idea is to have a hybrid model called "fast then slow". The idea is that the users's question is sent to both gpt4o and gemini 2.5 pro in parallel. The answer from gpt4o is streamed. Then when gemini is finished, gpt4o is given gemini's answer
and can use insights from gemini's answer to add to it's own answer. 

The fast then slow model would be an option in the drop down where the user picks what model they want. It would appear along side existing models such as gpt4o and llama.