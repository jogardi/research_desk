import chat_gpt

def main():
    messages = [
        {"role": "system", "content": "You are a helpful, witty and funny AI assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]

    reply = chat_gpt.chat(messages)   
    print(f'\n{reply}\n') 

if __name__ == '__main__':
    main()