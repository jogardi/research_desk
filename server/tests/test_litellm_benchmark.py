import os
import re
import time
from pathlib import Path
from typing import List, Optional

import dotenv
import pytest

# Load .env so provider API keys are available if configured
dotenv.load_dotenv()


def _read_models_yml_values(models_yml_path: str) -> List[str]:
    """Parse a limited subset of models.yml to extract litellm model values that are active.

    Avoids adding a YAML dependency by using a simple state machine on the file's structure.
    Returns model values like 'litellm/gemini/gemini-2.5-pro'.
    """
    if not os.path.exists(models_yml_path):
        return []

    active_values: List[str] = []

    # First, try to capture the defaultModel.value if present and active (assumed active if present)
    with open(models_yml_path, "r", encoding="utf-8") as f:
        text = f.read()

    default_match = re.search(r"^defaultModel:[\s\S]*?^\s*value:\s*\"([^\"]+)\"", text, re.M)
    if default_match:
        active_values.append(default_match.group(1).strip())

    # Then, capture models under 'models:' list with active: true
    # We scan line-by-line and detect blocks starting with '- id:'
    in_block = False
    cur_value: Optional[str] = None
    cur_active: Optional[bool] = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if raw_line.startswith("  - ") or raw_line.startswith("- "):
            # starting a new block; commit previous
            if cur_value and cur_active is True:
                active_values.append(cur_value)
            # reset for new block
            in_block = True
            cur_value = None
            cur_active = None
            continue

        if not in_block:
            continue

        if line.startswith("value:"):
            # value: "litellm/..."
            m = re.search(r'value:\s*"([^"]+)"', line)
            if m:
                cur_value = m.group(1).strip()
        elif line.startswith("active:"):
            cur_active = line.split(":", 1)[1].strip().lower() == "true"

    # commit last block
    if cur_value and cur_active is True:
        active_values.append(cur_value)

    # Deduplicate while preserving order
    seen = set()
    unique_values: List[str] = []
    for v in active_values:
        if v not in seen:
            unique_values.append(v)
            seen.add(v)

    return unique_values


def _provider_for(litellm_model_value: str) -> Optional[str]:
    """Return provider token from a 'litellm/<provider>/...'."""
    parts = litellm_model_value.split("/")
    if len(parts) < 2:
        return None
    if parts[0] != "litellm":
        return None
    return parts[1]

def _discover_models_to_benchmark() -> List[str]:
    # Allow explicit override via env (comma-separated list of litellm/<provider>/<model>)
    override = os.getenv("RUN_LLM_BENCHMARK_MODELS")
    if override:
        return [m.strip() for m in override.split(",") if m.strip()]

    # Otherwise, read from models.yml and take up to 3 active entries to keep runtime bounded
    models_yml_path = Path(__file__).resolve().parents[1] / "models.yml"
    values = _read_models_yml_values(models_yml_path)
    print("values", values)
    # Keep to a small, representative set
    return values[:3]


MODELS_TO_BENCH = _discover_models_to_benchmark()


@pytest.mark.parametrize("litellm_value", MODELS_TO_BENCH)
def test_litellm_completion_timing(litellm_value: str):
    import litellm

    # Require 'litellm/<provider>/model'
    assert litellm_value.startswith("litellm/"), (
        f"Unexpected model value (expected 'litellm/...'): {litellm_value}"
    )

    provider = _provider_for(litellm_value)
    assert provider is not None, f"Could not determine provider for {litellm_value}"

    # Convert to litellm's model name by stripping the 'litellm/' prefix
    model_name = "/".join(litellm_value.split("/")[1:])

    messages = [
        {"role": "user", "content": """Create a succinct title for the following text. The title must be at least three words long, concise, descriptive, and no longer than 10 words. Return only the title without any additional text or labels (like "Title: \”). Remember, some title MUST be provided even if the text seems complex or unclear. Also make the title explain why the document is relevant to the user query provided.

User query: drug

<p>A draft guideline for industry (August 2002) from the U.S. Department of Health and Human Service, Food and Drug Administration, and Center for Drug Evaluation and Research with the title "Liposome drug products. Chemistry, manufacturing, and controls; human pharmacokinetics and bioavailability; and labeling documentation" (224) (<a target="_blank" href="https://www.fdafda.gov/cder/guidance">www.fda.gov/cder/guidance</a>) summarizes the current thinking of the FDA on this topic. </p>This draft guidance gives recommendations on the unique aspects of liposome drug products. <span class="hilite-sentence">Liposome drug products are defined in this case as "drug products containing drug substances (active pharmaceutical ingredients) encapsulated in liposomes. </span>A liposome is a microvesicle composed of a bilayer of lipid amphipathic molecules enclosing an aqueous compartment. Liposome drug products are formed when a liposome is used to encapsulate a drug substance within the lipid bilayer or in the interior aqueous space of the liposome" (224).<p></p>

<p>Because the liposomes were proposed as drug delivery systems, questions have been raised about the stability of liposomes as pharmaceutical formulations. </p>Liposome stability and shelf life depend on a number of factors such as size and chemical composition. Liposomal drug products have to be stable for over two years at a minimum. Both in physical and chemical terms, little deviation from the specifications of the fresh product are tolerated. <span class="hilite-sentence">More information on the view of Food and Drug Administration on liposome drug products can be found in the "Guidance for Industry, Liposome Drug Products" issued August 2002 (28). </span>It suffices to say that over<p></p>"""}
    ]

    start = time.perf_counter()
    try:
        resp = litellm.completion_with_retries(
            model=model_name,
            messages=messages,
        )
    except Exception as e:
        # Record provider + model for easier debugging
        raise AssertionError(f"litellm completion failed for {model_name}: {e}")
    duration = time.perf_counter() - start

    # Basic sanity of response
    content = resp.choices[0].message.content
    assert isinstance(content, str) and len(content.strip()) > 0

    # Emit timing result for visibility in CI logs
    print(f"Model: {model_name} | Duration: {duration:.2f}s | Tokens: ~N/A")
