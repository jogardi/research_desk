def get_gemini_consultation_prompt(question: str, context: str = '') -> str:
    """Generate the prompt for consulting Gemini 2.5 Pro for advice."""
    return f"""You are being consulted as an expert advisor to provide alternative perspectives, insights, or ideas.

Context: {context}

Question: {question}

Please provide thoughtful advice, alternative approaches, or different perspectives that might be helpful."""


def get_fast_then_slow_enhancement_prompt(gemini_response: str) -> str:
    """Generate the prompt for enhancing GPT-4o response with Gemini insights."""
    return f"""Another AI model (Gemini 2.5 Pro) was consulted on this same question. Here's their response:

{gemini_response}

Tell the user everything gemini said that your previous response didn't already cover. Don't leave out any useful additional information but also
don't add redundant information from gemini's answer that is already covered in your own answer.
"""
