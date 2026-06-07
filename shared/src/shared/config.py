import argparse
import datetime
import os
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List

import dotenv
import yaml


class KnowledgebaseDict:
    """Dict-like access to configured knowledge bases by short name."""

    def __init__(self, knowledgebases: List[SimpleNamespace]):
        self._knowledgebases = {kb.SHORT_NAME: kb for kb in knowledgebases}

    def __getitem__(self, key):
        return self._knowledgebases[key]

    def __contains__(self, key):
        return key in self._knowledgebases

    def keys(self):
        return self._knowledgebases.keys()

    def values(self):
        return self._knowledgebases.values()

    def items(self):
        return self._knowledgebases.items()

    def get(self, key, default=None):
        return self._knowledgebases.get(key, default)


def _recursive_merge(base: Dict, override: Dict) -> Dict:
    merged = dict(base)
    for key, value in (override or {}).items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _recursive_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_profile_yaml(path: Path, profile: str) -> Dict:
    if not path.exists():
        return {}
    with path.open(mode="r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}
    if profile in config:
        return config[profile] or {}
    return config.get("default", {}) or {}


def _format_templates(config: Dict) -> Dict:
    formatted = dict(config)
    for key, value in list(formatted.items()):
        if isinstance(value, str):
            try:
                formatted[key] = value.format(**formatted)
            except Exception:
                formatted[key] = value
    return formatted


class Config:
    _config: Dict = {}

    @classmethod
    def load_config(cls, args: argparse.Namespace):
        dotenv.load_dotenv()
        profile = os.getenv("PROFILE") or getattr(args, "profile", "default")
        org = os.getenv("ORG") or getattr(args, "org", "DEV")

        cls._config["ARGV_PARAM1"] = getattr(args, "param1", None)
        cls._config["ARGV_PARAM2"] = getattr(args, "param2", None)
        cls._config["ARGV_PARAM3"] = getattr(args, "param3", None)

        cls.load_config_with_profile(org=org, profile=profile)

    @classmethod
    def load_config_with_profile(cls, org: str = "DEV", profile: str = "default"):
        print(f"\n*** Using configuration profile: {org}:{profile}\n")
        os.environ["LITELLM_LOG"] = "WARN"

        project_root = cls.get_project_root()
        data_root = Path(os.getenv("RESEARCH_DESK_DATA_ROOT", project_root / "data")).resolve()

        config = {
            "FORMATTED_DATETIME": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "ORG": org,
            "ORG_NAME": org,
            "PROFILE": profile,
            "WORKSPACE_DIR": str(project_root.parent),
            "ALL_ROOT": str(project_root.parent),
            "IS_PROD": False,
            "LOG_LEVEL": "info",
            "ROOT_FOLDER": str(data_root),
            "KNOWLEDGEBASE_FOLDER": "{ROOT_FOLDER}/knowledgebase",
            "DB_FOLDER": "{ROOT_FOLDER}/database",
            "LOG_FOLDER": "{ROOT_FOLDER}/logs",
            "WORK_FOLDER_LEAF": "work",
            "STAGING_FOLDER_LEAF": "staging",
            "FAILED_FOLDER_LEAF": "failed",
            "STAGING_FOLDER": "{ROOT_FOLDER}/{STAGING_FOLDER_LEAF}",
            "WORK_FOLDER": "{ROOT_FOLDER}/{WORK_FOLDER_LEAF}",
            "FAILED_FOLDER": "{ROOT_FOLDER}/{FAILED_FOLDER_LEAF}",
            "AUDIO_FILE_EXTENSIONS": ".mp3,.flac,.m4a,.wma,.ogg,.wav,.aac",
            "VIDEO_FILE_EXTENSIONS": ".mpeg,.wmv,.webm,.mov,.mpg,.flv,.mkv,.m4v,.mp4,.avi",
            "TEXT_FILE_EXTENSIONS": ".txt,.xls,.csv,.xml,.htm,.rtf,.json,.html",
            "PDF_FILE_EXTENSIONS": ".pdf",
            "DOCX_FILE_EXTENSIONS": ".docx",
            "IGNORE_FILE_EXTENSIONS": ".log,.DS_Store,.tmp,.lock",
            "KB_FTP_ENABLED": "0",
            "TITLING_ENABLED": "0",
            "HOST": "localhost",
            "PORT": 5000,
            "DEBUG_MODE": True,
            "SSL_ENABLED": False,
            "SSL_CERT_PATH": "",
            "SSL_KEY_PATH": "",
            "USER_IDLE_TIMEOUT": 900,
            "SESSION_TIMEOUT": 1800,
            "DISK_CACHE_DIR": str(project_root / "disk_cache"),
            "DISK_CACHE_SIZE_LIMIT": 1_000_000_000,
            "RESEARCH_DESK_URL": "http://localhost:9000",
            "RATE_LIMIT_GLOBAL": "2000 per second",
            "RATE_LIMIT_SEARCH": "10000 per day; 10000 per hour",
            "RATE_LIMIT_SEARCH_LLM_ANSWER": "10000 per month; 10 per minute",
            "RATE_LIMIT_DOCUMENT": "500 per day",
            "RATE_LIMIT_LLM": "300 per day; 50 per hour",
            "RATE_LIMIT_CONTRIBUTE": "50 per day",
            "RATE_LIMIT_FLAG": "50 per day",
            "ENABLE_RATE_LIMIT": True,
            "LLM_MODEL_CONCISE": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "LLM_MODEL_SUMMARY": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "LLM_MODEL_ANSWER": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "BACKENDLESS_SERVER": "https://api.backendless.com",
            "DOCUMENT_SERVER": "http://localhost:5000",
            "DOCUMENT_SERVER_API_SERVER": "http://localhost:5000",
            "MAX_FTS_RESULTS": 500,
            "RERANK_TOGETHER_MODEL": "Salesforce/Llama-Rank-V1",
            "RERANK_METHOD": "flashrank",
            "SENTENCE_BEFORE_OFFSET": 10,
            "SENTENCE_AFTER_OFFSET": 10,
            "ENABLE_EXACT_SEARCH": False,
            "PROMPT_INSIGHTS": "Summarize the key insights from the selected search results.",
            "PROMPT_CONCEPTS": "Summarize the key concepts from the selected search results.",
            "PROMPT_QUESTIONS": "Suggest focused questions that the selected search results can answer.",
            "PROMPT_SEARCH_QUERIES": "Generate related search queries for: {search_query}",
            "PROMPT_SUGGEST_QUERIES": "Generate concise related search queries from the selected text.",
            "EXCLUDE_LLM_TRAINING_DATA_INSTRUCTIONS": (
                "Use only the provided context when the user asks for grounded answers."
            ),
            "SEMANTIC_SEARCH_SCORE_THRESHOLD": 0,
            "BM25_WEIGHT": 0.3,
            "USE_QUERY_FOR_TITLE": True,
            "ENABLE_LUCENE": False,
            "BEFORE_SENTENCE_WEIGHT": 0,
            "AFTER_SENTENCE_WEIGHT": 0,
            "ENABLE_SEMANTIC": True,
            "INCLUDE_ENTIRE_BLOCK_OF_ADJ_SENTENCES": True,
            "REMOVE_LINEBREAKS": True,
            "REMOVE_LI_TAGS": True,
            "KNOWLEDGEBASES_DATA": [
                {
                    "SHORT_NAME": "demo",
                    "DISPLAY_NAME": "Demo Knowledge Base",
                    "EMBED_MODEL": "flag/BAAI/bge-m3",
                    "MAX_TOKENS_IN_CHUNK": 2048,
                    "HNSWLIB_MAX_ELEMENTS": 100_000,
                    "HNSWLIB_EF_CONSTRUCTION": 100,
                    "HNSWLIB_M": 16,
                    "LATE_CHUNKING": False,
                    "LATE_CHUNKING_BATCH_SIZE": 16,
                    "PDF_RESOLUTION": 80,
                }
            ],
        }

        if os.getenv("RESEARCH_DESK_CONFIG_BACKEND") == "backendless":
            from shared.db_support.config_backendless import ConfigBackendless

            config = _recursive_merge(config, ConfigBackendless.get_config(org, profile))

        config = _recursive_merge(config, _read_profile_yaml(project_root / "config.yml", profile))
        config = _recursive_merge(config, _read_profile_yaml(project_root / "config_override.yml", profile))
        config = _format_templates(config)

        cls._config = config
        for key, value in cls._config.items():
            setattr(cls, key, value)

        knowledgebases_list = [SimpleNamespace(**kb) for kb in cls._config["KNOWLEDGEBASES_DATA"]]
        cls._config["knowledgebases"] = knowledgebases_list
        cls._config["knowledgebase"] = KnowledgebaseDict(knowledgebases_list)
        setattr(cls, "knowledgebases", knowledgebases_list)
        setattr(cls, "knowledgebase", cls._config["knowledgebase"])

    @classmethod
    def get_project_root(cls) -> Path:
        current_dir = Path.cwd().resolve()
        for candidate in [current_dir, *current_dir.parents]:
            if (candidate / "pyproject.toml").exists() or (candidate / "config.yml").exists():
                cls._config["WORKSPACE_DIR"] = candidate.parent
                cls._config["ALL_ROOT"] = candidate.parent
                return candidate
        cls._config["WORKSPACE_DIR"] = current_dir
        cls._config["ALL_ROOT"] = current_dir
        return current_dir

    @classmethod
    def get_config(cls) -> Dict:
        return cls._config

    @classmethod
    def __getitem__(cls, item):
        return cls._config.get(item)


def _read_cli_arguments():
    arg_parser = argparse.ArgumentParser()
    if os.getenv("PROFILE") is None:
        arg_parser.add_argument("--profile", default="default", action="store", help="Profile to run in")
        arg_parser.add_argument("--org", default="DEV", action="store", help="Organization identifier")
    else:
        arg_parser.add_argument("-c")

    arg_parser.add_argument("--param1", action="store")
    arg_parser.add_argument("--param2", action="store")
    arg_parser.add_argument("--param3", action="store")

    return arg_parser.parse_args()


def load_cli_args():
    try:
        args = _read_cli_arguments()
        Config.load_config(args)
    except SystemExit as e:
        print(f"Error occurred while loading arguments. Error: {e}")


@lru_cache()
def cfg():
    if "PROFILE" in Config._config:
        return Config
    profile = os.getenv("PROFILE") or "default"
    org = os.getenv("ORG") or "DEV"
    Config.load_config_with_profile(org=org, profile=profile)
    return Config
