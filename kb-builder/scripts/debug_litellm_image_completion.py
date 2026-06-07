#!/usr/bin/env python3
"""
Quick debug script to call a VLM completion with an image and pickle the response.

Example:
    # From an image file
    PROFILE=default poetry run python scripts/debug_litellm_image_completion.py \
        --image /path/to/image.png \
        --out /tmp/litellm_image_response.pkl \
        --prompt "Say hello and describe the image briefly."

    # From the first page of a PDF
    PROFILE=default poetry run python scripts/debug_litellm_image_completion.py \
        --pdf /path/to/sample.pdf \
        --out /tmp/litellm_image_response.pkl \
        --prompt "Say hello and describe the image briefly."

Notes:
- Loads API keys from dotenv automatically if present.
- Defaults to the model configured in kb-builder hparams_config (agentic_chunk_llm).
- Saves both a pickle of the response and a JSON dump alongside it for easy inspection.
"""

from __future__ import annotations
import dotenv
dotenv.load_dotenv()

import argparse
import base64
import json
import os
import pickle
import sys
from pathlib import Path
import io

import dotenv

# Ensure environment variables are loaded (API keys, etc.)
dotenv.load_dotenv()

try:
    # Use the same helper the main pipeline uses
    from litellm import completion_with_retries
except Exception as e:  # pragma: no cover
    print("Failed to import litellm.completion_with_retries:", e, file=sys.stderr)
    sys.exit(1)


def encode_image_to_data_url(image_path: Path) -> str:
    """Read an image file and return a data URL for inline image sending."""
    suffix = image_path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".png":
        mime = "image/png"
    elif suffix == ".webp":
        mime = "image/webp"
    else:
        # Default to PNG if unknown
        mime = "image/png"

    data = image_path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Call litellm VLM with an image and pickle the response.")

    parser.add_argument("--pdf", type=Path, help="Path to a PDF file; the first page will be used")

    parser.add_argument("--pdf-page", type=int, default=1, help="Page number to extract (1-based), default 1")
    parser.add_argument("--pdf-resolution", type=int, default=164, help="Rendering DPI for PDF to image")
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (defaults to kb-builder hparams_config agentic_chunk_llm)",
    )
    parser.add_argument(
        "--prompt",
        default="Please describe the image briefly.",
        help="Text prompt to send along with the image.",
    )
    parser.add_argument(
        "--out",
        default="/tmp/litellm_image_response.pkl",
        type=Path,
        help="Where to write the pickled response.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Optional request timeout in seconds.",
    )
    args = parser.parse_args()

    # Expand user (~) for paths
    if args.pdf:
        args.pdf = args.pdf.expanduser()

    # Prepare data URL either from image or from first page of PDF
    data_url: str

    # PDF path is provided
    if not args.pdf.exists():
        print(f"PDF does not exist: {args.pdf}", file=sys.stderr)
        return 2
    try:
        import pdfplumber
    except Exception as e:  # pragma: no cover
        print("Failed to import pdfplumber:", e, file=sys.stderr)
        return 2

    page_index = max(1, args.pdf_page) - 1
    with pdfplumber.open(args.pdf) as pdf:
        if page_index >= len(pdf.pages):
            print(
                f"PDF has only {len(pdf.pages)} pages; cannot extract page {args.pdf_page}",
                file=sys.stderr,
            )
            return 2
        page = pdf.pages[page_index]
        page_image = page.to_image(resolution=args.pdf_resolution)
        buffer = io.BytesIO()
        page_image.save(buffer, format="PNG")
        buffer.seek(0)
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        data_url = f"data:image/png;base64,{b64}"

    # Determine model
    model_name = args.model
    if not model_name:
        try:
            from kb_builder.hparams_config import hpc

            # Stored as "litellm/<provider:model>" in our config; strip prefix for litellm
            model_name = hpc().agentic_chunk_llm
            if model_name.startswith("litellm/"):
                model_name = model_name[len("litellm/") :]
        except Exception as e:  # pragma: no cover
            print(
                "Could not load model from hparams_config; please pass --model. Error:",
                e,
                file=sys.stderr,
            )
            return 2

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": args.prompt},
            ],
        }
    ]

    print(f"Calling model: {model_name}")
    print(f"PDF: {args.pdf} (page {args.pdf_page}, resolution {args.pdf_resolution} DPI)")
    try:
        response = completion_with_retries(
            messages=messages,
            model=model_name,
            reasoning_effort="disable",
            timeout=args.timeout,
        )
    except Exception as e:  # pragma: no cover
        print("API call failed:", e, file=sys.stderr)
        return 1

    # Print a concise summary of usage fields, guarding for providers that omit details
    try:
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        prompt_details = getattr(usage, "prompt_tokens_details", None)
        image_tokens = getattr(prompt_details, "image_tokens", None) if prompt_details else None
        print(
            "Usage:",
            json.dumps(
                {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "image_tokens": image_tokens,
                },
                indent=2,
            ),
        )
    except Exception as e:  # pragma: no cover
        print("Failed to print usage:", e, file=sys.stderr)

    # Persist the raw response (pickle), and also write a JSON dump next to it
    args.out.parent.mkdir(parents=True, exist_ok=True)

    # 1) Try to pickle the whole object
    try:
        with args.out.open("wb") as f:
            pickle.dump(response, f)
        print(f"Pickled response written to: {args.out}")
    except Exception as e:
        print("Pickling full object failed, falling back to dict dump:", e, file=sys.stderr)
        fallback_path = args.out.with_suffix(".fallback.pkl")
        try:
            as_dict = getattr(response, "model_dump", None)
            if callable(as_dict):
                payload = as_dict()
            else:
                # Best-effort conversion
                payload = json.loads(json.dumps(response, default=str))
            with fallback_path.open("wb") as f:
                pickle.dump(payload, f)
            print(f"Pickled dict fallback written to: {fallback_path}")
        except Exception as e2:  # pragma: no cover
            print("Pickling dict fallback also failed:", e2, file=sys.stderr)

    # 2) Write JSON for quick inspection
    json_path = args.out.with_suffix(".json")
    try:
        # Prefer pydantic model_dump if present for stable structure
        if hasattr(response, "model_dump") and callable(response.model_dump):
            data = response.model_dump()
        else:
            data = json.loads(json.dumps(response, default=str))
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"JSON response written to: {json_path}")
    except Exception as e:  # pragma: no cover
        print("Failed to write JSON:", e, file=sys.stderr)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

