def apply_model_sampling_params(model_name: str, sampling_params: dict, payload: dict) -> None:
    """
    Apply model specific sample parameters to the sample_parameters dictionary.
    """
    if model_name == "litellm/openai/gpt-5-2025-08-07":
        sampling_params["temperature"] = 1
        # remove the "top_p" parameter
        sampling_params.pop("top_p", None)
    elif model_name == "litellm/anthropic/claude-opus-4-1-20250805":
        # remove the "top_p" parameter
        sampling_params.pop("top_p", None)
    




