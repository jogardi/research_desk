from functools import lru_cache
from shared.logger import Logger
from shared.config import cfg
from types import SimpleNamespace as Sn

@lru_cache()
def hpc():
    from shared.utils import dict2obj
    default_hparams = dict(
        CHUNK_SIZE=1500,
        CHUNK_OVERLAP_SIZE=300,
        CHUNK_SENTENCE_SIZE=1,

        CHUNKING_TYPE="sentence",

        DEFAULT_PDF_PROCESSOR="marker_json",
        GEMINI_MODEL="gemini-2.0-flash-exp",
        ENABLE_MPS=True,
        mini_run=False,
        gemini_pdf=dict(
            model="litellm/gemini/gemini-exp-1206",
            prompt="Translate this image of a page of a PDF to markdown. The markdown supports LaTeX. "
                  "Translate tables to JSON. Translate figures to a description of the figure contents "
                  "including estimations of any numerical data represented by the figure."
                  "If there is a references section don't include it."
        ),
        litellm_pdf=dict(
            model="litellm/together_ai/meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
            prompt="""You convert images of pages to markdown. If you have any thought or explanation that does not belong in the markdown text enclose it in <think></think>. Your output only the markdown with no explanation or description. The markdown supports LaTeX. Preserve bolding. If there are tables or figures, write a description of them inside <table id="..."></table> or <figure id="..."></figure> respectively. If there are no tables or figures then don't use those tags. The id will usually be some name specified by the document such as "Figure-4" with spaces replaced by dashes . If there is no name make one. If there is a caption it should be transcribed inside of the table/figure tags. If there is a reference to a figure make it a link like [Figure 4](Figure-4). Convert this one."""
        ),
        marker_endpoint_params=dict(use_llm=True, force_ocr=True),
        categorize=dict(
              summary_model="litellm/together_ai/deepseek-ai/DeepSeek-V3",
              summary_prompt="Summarize this text in 100 words or less: {txt}"
        ),
        enable_lucene=True,
        sentence_splitter='spacy',
        merge_threshold=None,
        # post_correct_llm='litellm/claude-3-5-sonnet-20240620'
        post_correct_llm='litellm/anthropic/claude-sonnet-4-20250514',
        json_converter_llm='litellm/together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo',
        enable_marker_describe_image=True,
        enable_post_correction=True,
        post_correct_strategy='per_page',
        enable_agentic_chunking=True,
        # agentic_chunk_llm='litellm/anthropic/claude-sonnet-4-20250514',
        agentic_chunk_llm='litellm/gemini/gemini-3-flash-preview',
    )

    if cfg().PROFILE == 'default':
        return dict2obj(default_hparams)
    else:
        profiles = dict(
            benchmark=lambda: dict(
                CHUNK_SENTENCE_SIZE=1,
                DEFAULT_PDF_PROCESSOR="pymupdf"
            ),
            prod = lambda: dict(
                DEFAULT_PDF_PROCESSOR="pdfplumber"
            ),
            dev = lambda: dict(
                DEFAULT_PDF_PROCESSOR="pdfplumber",
                GEMINI_MODEL="gemini-1.5-flash-002"
            )
        )
        if (profile := profiles.get(cfg().PROFILE)):
            default_hparams.update(profile())

        # merge default_hparams and profile_params
        Logger.info(f"hpc: {default_hparams}")
        return dict2obj(default_hparams)
