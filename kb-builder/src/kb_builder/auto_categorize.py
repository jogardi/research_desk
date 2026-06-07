from kb_builder.hparams_config import hpc
def summarize_txt(txt):
    import litellm
    prompt = hpc().categorize.summary_prompt.format(txt=txt)
    model = hpc().categorize.summary_model[len('litellm/'):]
    try:
        response = litellm.completion_with_retries(model=model,
                                                  messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in completion with args: model={model}, messages=[{{role: user, content: {prompt}}}]")
        raise e
