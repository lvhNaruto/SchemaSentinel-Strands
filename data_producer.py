import os
import random
import time
from typing import Any, Dict, List, Tuple
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

DEFAULT_DISCOVERY_TOPICS = [
    "trending AI agents LLM github 2026",
    "vision language multimodal models python github",
    "vector search rag databases open source",
    "high throughput inference engines vllm sglang",
    "autonomous data engineering pipeline tools python",
    "reasoning models deepseek r1 open source github",
    "code generation agents benchmark python",
    "embedded AI agents edge devices rust python",
    "synthetic data generators diffusion llm github"
]

TOPIC_CATALOG = {
    "trending AI agents LLM github 2026": [
        ("Significant-Gravitas/AutoGPT", "https://github.com/Significant-Gravitas/AutoGPT", "Significant-Gravitas"),
        ("langchain-ai/langgraph", "https://github.com/langchain-ai/langgraph", "langchain-ai"),
        ("joaomdmoura/crewAI", "https://github.com/joaomdmoura/crewAI", "joaomdmoura"),
        ("OpenBMB/ChatDev", "https://github.com/OpenBMB/ChatDev", "OpenBMB"),
        ("geekan/MetaGPT", "https://github.com/geekan/MetaGPT", "geekan"),
        ("run-llama/llama_index", "https://github.com/run-llama/llama_index", "run-llama"),
        ("BerriAI/litellm", "https://github.com/BerriAI/litellm", "BerriAI"),
        ("mem0ai/mem0", "https://github.com/mem0ai/mem0", "mem0ai"),
        ("jxnl/instructor", "https://github.com/jxnl/instructor", "jxnl"),
        ("stanfordnlp/dspy", "https://github.com/stanfordnlp/dspy", "stanfordnlp")
    ],
    "vision language multimodal models python github": [
        ("haotian-liu/LLaVA", "https://github.com/haotian-liu/LLaVA", "haotian-liu"),
        ("QwenLM/Qwen-VL", "https://github.com/QwenLM/Qwen-VL", "QwenLM"),
        ("OpenGVLab/InternVL", "https://github.com/OpenGVLab/InternVL", "OpenGVLab"),
        ("THUDM/CogVLM", "https://github.com/THUDM/CogVLM", "THUDM"),
        ("google-research/big_vision", "https://github.com/google-research/big_vision", "google-research"),
        ("huggingface/transformers", "https://github.com/huggingface/transformers", "huggingface"),
        ("salesforce/LAVIS", "https://github.com/salesforce/LAVIS", "salesforce"),
        ("microsoft/Florence-2", "https://github.com/microsoft/Florence-2", "microsoft")
    ],
    "vector search rag databases open source": [
        ("chroma-core/chroma", "https://github.com/chroma-core/chroma", "chroma-core"),
        ("milvus-io/milvus", "https://github.com/milvus-io/milvus", "milvus-io"),
        ("weaviate/weaviate", "https://github.com/weaviate/weaviate", "weaviate"),
        ("qdrant/qdrant", "https://github.com/qdrant/qdrant", "qdrant"),
        ("facebookresearch/faiss", "https://github.com/facebookresearch/faiss", "facebookresearch"),
        ("pgvector/pgvector", "https://github.com/pgvector/pgvector", "pgvector"),
        ("infiniflow/infinity", "https://github.com/infiniflow/infinity", "infiniflow")
    ],
    "high throughput inference engines vllm sglang": [
        ("vllm-project/vllm", "https://github.com/vllm-project/vllm", "vllm-project"),
        ("sgl-project/sglang", "https://github.com/sgl-project/sglang", "sgl-project"),
        ("NVIDIA/TensorRT-LLM", "https://github.com/NVIDIA/TensorRT-LLM", "NVIDIA"),
        ("huggingface/text-generation-inference", "https://github.com/huggingface/text-generation-inference", "huggingface"),
        ("ollama/ollama", "https://github.com/ollama/ollama", "ollama"),
        ("ggerganov/llama.cpp", "https://github.com/ggerganov/llama.cpp", "ggerganov")
    ],
    "autonomous data engineering pipeline tools python": [
        ("dbt-labs/dbt-core", "https://github.com/dbt-labs/dbt-core", "dbt-labs"),
        ("apache/airflow", "https://github.com/apache/airflow", "apache"),
        ("PrefectHQ/prefect", "https://github.com/PrefectHQ/prefect", "PrefectHQ"),
        ("dagster-io/dagster", "https://github.com/dagster-io/dagster", "dagster-io"),
        ("mage-ai/mage-ai", "https://github.com/mage-ai/mage-ai", "mage-ai"),
        ("great-expectations/great_expectations", "https://github.com/great-expectations/great_expectations", "great-expectations")
    ],
    "reasoning models deepseek r1 open source github": [
        ("deepseek-ai/DeepSeek-R1", "https://github.com/deepseek-ai/DeepSeek-R1", "deepseek-ai"),
        ("huggingface/open-r1", "https://github.com/huggingface/open-r1", "huggingface"),
        ("MoonshotAI/Kimi-k1.5", "https://github.com/MoonshotAI/Kimi-k1.5", "MoonshotAI"),
        ("willccbb/DeepSeek-R1-GRPO", "https://github.com/willccbb/DeepSeek-R1-GRPO", "willccbb"),
        ("deepseek-ai/DeepSeek-R1-Distill-Qwen", "https://github.com/deepseek-ai/DeepSeek-R1-Distill-Qwen", "deepseek-ai"),
        ("Skywork/Skywork-Reward-Models", "https://github.com/Skywork/Skywork-Reward-Models", "Skywork")
    ],
    "code generation agents benchmark python": [
        ("princeton-nlp/SWE-agent", "https://github.com/princeton-nlp/SWE-agent", "princeton-nlp"),
        ("paul-gauthier/aider", "https://github.com/paul-gauthier/aider", "paul-gauthier"),
        ("OpenCodeInterpreter/OpenCodeInterpreter", "https://github.com/OpenCodeInterpreter/OpenCodeInterpreter", "OpenCodeInterpreter"),
        ("OpenDevin/OpenDevin", "https://github.com/OpenDevin/OpenDevin", "OpenDevin"),
        ("QwenLM/Qwen2.5-Coder", "https://github.com/QwenLM/Qwen2.5-Coder", "QwenLM"),
        ("starcoder-org/starcoder2", "https://github.com/starcoder-org/starcoder2", "starcoder-org")
    ],
    "embedded AI agents edge devices rust python": [
        ("edge-ai/edge-llm", "https://github.com/edge-ai/edge-llm", "edge-ai"),
        ("tracel-ai/burn", "https://github.com/tracel-ai/burn", "tracel-ai"),
        ("huggingface/candle", "https://github.com/huggingface/candle", "huggingface"),
        ("mit-han-lab/llm-awq", "https://github.com/mit-han-lab/llm-awq", "mit-han-lab"),
        ("apache/tvm", "https://github.com/apache/tvm", "apache"),
        ("onnx/onnxruntime", "https://github.com/microsoft/onnxruntime", "microsoft")
    ],
    "synthetic data generators diffusion llm github": [
        ("google/datagemma", "https://github.com/google/datagemma", "google"),
        ("synthetic-ai/synth-llm", "https://github.com/synthetic-ai/synth-llm", "synthetic-ai"),
        ("argilla-io/distilabel", "https://github.com/argilla-io/distilabel", "argilla-io"),
        ("huggingface/cosmopedia", "https://github.com/huggingface/cosmopedia", "huggingface"),
        ("NVIDIA/Nemotron-4", "https://github.com/NVIDIA/Nemotron-4", "NVIDIA"),
        ("gretelai/gretel-synthetics", "https://github.com/gretelai/gretel-synthetics", "gretelai")
    ]
}

# General Fallback Pool to guarantee at least 5 records
FALLBACK_CORPUS = [
    ("Significant-Gravitas/AutoGPT", "https://github.com/Significant-Gravitas/AutoGPT", "Significant-Gravitas"),
    ("deepseek-ai/DeepSeek-R1", "https://github.com/deepseek-ai/DeepSeek-R1", "deepseek-ai"),
    ("vllm-project/vllm", "https://github.com/vllm-project/vllm", "vllm-project"),
    ("QwenLM/Qwen2.5-Coder", "https://github.com/QwenLM/Qwen2.5-Coder", "QwenLM"),
    ("chroma-core/chroma", "https://github.com/chroma-core/chroma", "chroma-core"),
    ("sgl-project/sglang", "https://github.com/sgl-project/sglang", "sgl-project"),
    ("tiangolo/fastapi", "https://github.com/tiangolo/fastapi", "tiangolo"),
    ("huggingface/transformers", "https://github.com/huggingface/transformers", "huggingface"),
    ("langchain-ai/langgraph", "https://github.com/langchain-ai/langgraph", "langchain-ai"),
    ("joaomdmoura/crewAI", "https://github.com/joaomdmoura/crewAI", "joaomdmoura")
]


class ChaosSchemaMutator:
    TITLE_ALIASES = ["project_heading", "repo_name", "headline", "name", "software_title"]
    AUTHOR_ALIASES = ["creator", "maintainer_handle", "dev_by", "owner_login", "author_name"]
    URL_ALIASES = ["web_url", "github_link", "canonical_url", "repo_endpoint", "source_link"]

    @classmethod
    def mutate(cls, title: str, author: str, url: str, score: int, batch_index: int) -> Tuple[Dict[str, Any], str, str]:
        mutation_types = [
            "url_author_embedding",
            "nested_contributor_array",
            "key_alias_type_coercion",
            "deep_metadata_wrapper"
        ]
        mutation_mode = mutation_types[(batch_index - 1) % len(mutation_types)]

        if mutation_mode == "url_author_embedding":
            renamed_title = random.choice(cls.TITLE_ALIASES)
            renamed_url = random.choice(cls.URL_ALIASES)
            return {
                renamed_title: title,
                renamed_url: url,
                "popularity_pct": f"{score}%"
            }, "URL Author Drift", "Regex Author Extraction & % Unpack"

        elif mutation_mode == "nested_contributor_array":
            renamed_url = random.choice(cls.URL_ALIASES)
            star_rating = round((score / 100.0) * 5.0, 1)
            return {
                "repo_name": title,
                renamed_url: url,
                "contributors_data": [
                    {"username": author, "is_owner": True},
                    {"username": "automated_sync_bot", "is_owner": False}
                ],
                "raw_metrics": {
                    "stars": f"{round(random.uniform(5.0, 99.0), 1)}k",
                    "rating_out_of_5": f"{star_rating}"
                }
            }, "Nested Array Drift", "Normalized Contributor List & Star Metric"

        elif mutation_mode == "key_alias_type_coercion":
            k_title = random.choice(cls.TITLE_ALIASES)
            k_author = random.choice(cls.AUTHOR_ALIASES)
            k_url = random.choice(cls.URL_ALIASES)
            return {
                k_title: title,
                k_author: author,
                k_url: url,
                "confidence_rating": f"0.{score}"
            }, "Key Alias Drift", "Mapped Alias Headers & Normalized Float"

        else: # deep_metadata_wrapper
            return {
                "metadata": {
                    "project_label": title,
                    "maintainer": author,
                    "endpoint": url
                },
                "eval_score": score
            }, "Metadata Wrapper Drift", "Flattened Deep Metadata Hierarchy"


def is_pure_github_repo(url: str) -> bool:
    if not url.startswith("https://github.com/"):
        return False
    banned = ["gist.github.com", "/issues", "/pull", "/commits", "/blob", "/releases", "/topics", "/tags", "/stargazers"]
    if any(b in url for b in banned):
        return False
    path_parts = [p for p in url.replace("https://github.com/", "").split("?")[0].split("/") if p]
    return len(path_parts) >= 2


def fetch_multi_topic_stream_batches(
    topics: List[str],
    topic_cursors: Dict[str, int],
    batch_size: int = 5
) -> Tuple[List[Dict[str, Any]], Dict[str, int], str]:
    if not topics:
        return [], topic_cursors, "No topics selected"

    now_ms = int(time.time() * 1000)
    batches = []

    # CASE A: MULTIPLE OR ALL TOPICS SELECTED
    if len(topics) > 1:
        summary_desc = f"Round-Robin across {len(topics)} active partitions"
        # Always pick 5 topics for 5 distinct batches
        chosen_5 = []
        for i in range(batch_size):
            chosen_5.append(topics[i % len(topics)])

        for i, t_name in enumerate(chosen_5):
            catalog = TOPIC_CATALOG.get(t_name, FALLBACK_CORPUS)
            offset = topic_cursors.get(t_name, 0)
            item_idx = offset % len(catalog)
            topic_cursors[t_name] = offset + 1

            title, raw_url, author = catalog[item_idx]
            # Ensure unique URL per batch to guarantee no SQLite duplicate drop
            unique_url = f"{raw_url}?stream_run={now_ms}_b{i+1}"
            score = random.randint(86, 98)

            if i == 0:
                mutated_rec, drift_name, fix_desc = {
                    "title": title,
                    "author": author,
                    "source_url": unique_url,
                    "relevance_score": score
                }, f"[{t_name[:18]}..] Clean Reference", "100% Contract Match"
                batch_slug = "clean"
            else:
                mutated_rec, drift_name, fix_desc = ChaosSchemaMutator.mutate(
                    title, author, unique_url, score, batch_index=i
                )
                drift_name = f"[{t_name[:18]}..] {drift_name}"
                batch_slug = "drift"

            batches.append({
                "batch_id": f"batch_{now_ms % 10000}_{batch_slug}_{i+1}",
                "short_title": drift_name,
                "fix_summary": fix_desc,
                "records": [mutated_rec]
            })

        return batches, topic_cursors, summary_desc

    # CASE B: SINGLE TOPIC
    single_topic = topics[0]
    catalog = TOPIC_CATALOG.get(single_topic, [])
    
    # Try Tavily if available
    tavily_key = os.getenv("TAVILY_API_KEY")
    client = TavilyClient(api_key=tavily_key) if tavily_key else None
    web_records = []

    if client:
        try:
            search_response = client.search(
                query=f"{single_topic} site:github.com",
                search_depth="basic",
                include_domains=["github.com"],
                max_results=15
            )
            for r in search_response.get("results", []):
                u = r.get("url", "")
                if is_pure_github_repo(u):
                    parts = u.replace("https://github.com/", "").split("?")[0].split("/")
                    owner, repo = parts[0], parts[1]
                    clean_repo_url = f"https://github.com/{owner}/{repo}"
                    clean_t = f"{owner}/{repo}"
                    if (clean_t, clean_repo_url, owner) not in web_records:
                        web_records.append((clean_t, clean_repo_url, owner))
        except Exception:
            pass

    # Merge with catalog to guarantee AT LEAST 5 records
    for item in catalog:
        if item not in web_records:
            web_records.append(item)

    # If still fewer than 5, backfill from fallback corpus
    if len(web_records) < batch_size:
        for item in FALLBACK_CORPUS:
            if item not in web_records:
                web_records.append(item)

    offset = topic_cursors.get(single_topic, 0)
    # Loop over if offset exceeds items
    start_idx = offset % len(web_records)
    window = []
    for k in range(batch_size):
        window.append(web_records[(start_idx + k) % len(web_records)])

    topic_cursors[single_topic] = offset + batch_size

    for i, (title, base_url, author) in enumerate(window):
        # Strict unique URL with timestamp and batch number
        unique_url = f"{base_url}?stream_run={now_ms}_b{i+1}"
        score = random.randint(85, 98)

        if i == 0:
            mutated_rec, drift_name, fix_desc = {
                "title": title,
                "author": author,
                "source_url": unique_url,
                "relevance_score": score
            }, "Clean Reference", "100% Contract Match"
            batch_slug = "clean"
        else:
            mutated_rec, drift_name, fix_desc = ChaosSchemaMutator.mutate(
                title, author, unique_url, score, batch_index=i
            )
            batch_slug = "drift"

        batches.append({
            "batch_id": f"batch_{now_ms % 10000}_{batch_slug}_{i+1}",
            "short_title": drift_name,
            "fix_summary": fix_desc,
            "records": [mutated_rec]
        })

    return batches, topic_cursors, f"Items {offset+1} to {offset+batch_size} for {single_topic[:25]}"


def fetch_paginated_stream_batches(topic: str, offset: int = 0, batch_size: int = 5):
    cursors = {topic: offset}
    batches, updated_cursors, _ = fetch_multi_topic_stream_batches(
        topics=[topic],
        topic_cursors=cursors,
        batch_size=batch_size
    )
    return batches, False, updated_cursors.get(topic, offset + batch_size)


def get_complex_drift_stream():
    batches, _, _ = fetch_paginated_stream_batches(
        topic="trending AI agents LLM github 2026",
        offset=0,
        batch_size=5
    )
    for b in batches:
        yield b