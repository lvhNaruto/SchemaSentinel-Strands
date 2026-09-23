import os
import random
import time
import re
import urllib.request
import json
from typing import Any, Dict, List, Tuple
from dotenv import load_dotenv

load_dotenv()

RE_GITHUB_REPO = re.compile(r"^https://github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)(?:[/?#]|$)")
BANNED_URL_SLUGS = frozenset(["gist", "issues", "pull", "commits", "blob", "releases", "topics", "tags", "stargazers"])

_STREAM_RESOLVER_CACHE: Dict[str, List[Tuple[str, str, str]]] = {}

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

TOPIC_CATALOG: Dict[str, List[Tuple[str, str, str]]] = {
    "trending AI agents LLM github 2026": [
        ("Significant-Gravitas/AutoGPT", "https://github.com/Significant-Gravitas/AutoGPT", "Significant-Gravitas"),
        ("langchain-ai/langgraph", "https://github.com/langchain-ai/langgraph", "langchain-ai"),
        ("joaomdmoura/crewAI", "https://github.com/joaomdmoura/crewAI", "joaomdmoura"),
        ("OpenBMB/ChatDev", "https://github.com/OpenBMB/ChatDev", "OpenBMB"),
        ("geekan/MetaGPT", "https://github.com/geekan/MetaGPT", "geekan")
    ],
    "vision language multimodal models python github": [
        ("haotian-liu/LLaVA", "https://github.com/haotian-liu/LLaVA", "haotian-liu"),
        ("QwenLM/Qwen-VL", "https://github.com/QwenLM/Qwen-VL", "QwenLM"),
        ("OpenGVLab/InternVL", "https://github.com/OpenGVLab/InternVL", "OpenGVLab"),
        ("THUDM/CogVLM", "https://github.com/THUDM/CogVLM", "THUDM")
    ],
    "vector search rag databases open source": [
        ("chroma-core/chroma", "https://github.com/chroma-core/chroma", "chroma-core"),
        ("milvus-io/milvus", "https://github.com/milvus-io/milvus", "milvus-io"),
        ("weaviate/weaviate", "https://github.com/weaviate/weaviate", "weaviate"),
        ("qdrant/qdrant", "https://github.com/qdrant/qdrant", "qdrant")
    ],
    "high throughput inference engines vllm sglang": [
        ("vllm-project/vllm", "https://github.com/vllm-project/vllm", "vllm-project"),
        ("sgl-project/sglang", "https://github.com/sgl-project/sglang", "sgl-project"),
        ("NVIDIA/TensorRT-LLM", "https://github.com/NVIDIA/TensorRT-LLM", "NVIDIA"),
        ("ollama/ollama", "https://github.com/ollama/ollama", "ollama")
    ],
    "autonomous data engineering pipeline tools python": [
        ("dbt-labs/dbt-core", "https://github.com/dbt-labs/dbt-core", "dbt-labs"),
        ("apache/airflow", "https://github.com/apache/airflow", "apache"),
        ("PrefectHQ/prefect", "https://github.com/PrefectHQ/prefect", "PrefectHQ"),
        ("dagster-io/dagster", "https://github.com/dagster-io/dagster", "dagster-io")
    ],
    "reasoning models deepseek r1 open source github": [
        ("deepseek-ai/DeepSeek-R1", "https://github.com/deepseek-ai/DeepSeek-R1", "deepseek-ai"),
        ("huggingface/open-r1", "https://github.com/huggingface/open-r1", "huggingface"),
        ("MoonshotAI/Kimi-k1.5", "https://github.com/MoonshotAI/Kimi-k1.5", "MoonshotAI")
    ],
    "code generation agents benchmark python": [
        ("princeton-nlp/SWE-agent", "https://github.com/princeton-nlp/SWE-agent", "princeton-nlp"),
        ("paul-gauthier/aider", "https://github.com/paul-gauthier/aider", "paul-gauthier"),
        ("OpenDevin/OpenDevin", "https://github.com/OpenDevin/OpenDevin", "OpenDevin")
    ],
    "embedded AI agents edge devices rust python": [
        ("edge-ai/edge-llm", "https://github.com/edge-ai/edge-llm", "edge-ai"),
        ("tracel-ai/burn", "https://github.com/tracel-ai/burn", "tracel-ai"),
        ("huggingface/candle", "https://github.com/huggingface/candle", "huggingface")
    ],
    "synthetic data generators diffusion llm github": [
        ("google/datagemma", "https://github.com/google/datagemma", "google"),
        ("argilla-io/distilabel", "https://github.com/argilla-io/distilabel", "argilla-io"),
        ("NVIDIA/Nemotron-4", "https://github.com/NVIDIA/Nemotron-4", "NVIDIA")
    ]
}


class ChaosSchemaMutator:
    TITLE_ALIASES = ("project_heading", "repo_name", "headline", "name", "software_title")
    AUTHOR_ALIASES = ("creator", "maintainer_handle", "dev_by", "owner_login", "author_name")
    URL_ALIASES = ("web_url", "github_link", "canonical_url", "repo_endpoint", "source_link")

    @classmethod
    def mutate(cls, title: str, author: str, url: str, score: int, batch_index: int) -> Tuple[Dict[str, Any], str, str]:
        mutation_types = (
            "url_author_embedding",
            "nested_contributor_array",
            "key_alias_type_coercion",
            "deep_metadata_wrapper"
        )
        mutation_mode = mutation_types[(batch_index - 1) % len(mutation_types)]

        if mutation_mode == "url_author_embedding":
            return {
                random.choice(cls.TITLE_ALIASES): title,
                random.choice(cls.URL_ALIASES): url,
                "popularity_pct": f"{score}%"
            }, "URL Author Drift", "Regex Author Extraction & % Unpack"

        elif mutation_mode == "nested_contributor_array":
            star_rating = round((score / 100.0) * 5.0, 1)
            return {
                "repo_name": title,
                random.choice(cls.URL_ALIASES): url,
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
            return {
                random.choice(cls.TITLE_ALIASES): title,
                random.choice(cls.AUTHOR_ALIASES): author,
                random.choice(cls.URL_ALIASES): url,
                "confidence_rating": f"0.{score}"
            }, "Key Alias Drift", "Mapped Alias Headers & Normalized Float"

        else:
            return {
                "metadata": {
                    "project_label": title,
                    "maintainer": author,
                    "endpoint": url
                },
                "eval_score": score
            }, "Metadata Wrapper Drift", "Flattened Deep Metadata Hierarchy"


def resolve_live_upstream_records(query_or_user: str) -> List[Tuple[str, str, str]]:
    """Directly queries GitHub's official REST API in real time. Zero mock fallback."""
    raw_query = query_or_user.strip()
    if raw_query in _STREAM_RESOLVER_CACHE:
        return _STREAM_RESOLVER_CACHE[raw_query]

    results = []
    headers = {"User-Agent": "SchemaSentinel-Engine/2.0"}
    gh_token = os.getenv("GITHUB_TOKEN")
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    # 1. Direct GitHub Username (e.g. 'lvh_naruto')
    if "/" not in raw_query and " " not in raw_query:
        try:
            req = urllib.request.Request(f"https://api.github.com/users/{raw_query}/repos?sort=updated&per_page=10", headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                if resp.status == 200:
                    repos = json.loads(resp.read().decode())
                    for r in repos:
                        fn = r.get("full_name") or f"{raw_query}/{r.get('name')}"
                        url = r.get("html_url")
                        owner = r.get("owner", {}).get("login", raw_query)
                        if fn and url:
                            results.append((fn, url, owner))
        except Exception:
            pass

    # 2. Direct GitHub Slug (e.g. 'lvh_naruto/SchemaSentinel-Strands')
    if "/" in raw_query and not raw_query.startswith("http"):
        parts = raw_query.split("/")
        if len(parts) == 2:
            owner, repo_name = parts[0].strip(), parts[1].strip()
            results.append((f"{owner}/{repo_name}", f"https://github.com/{owner}/{repo_name}", owner))

    # 3. Direct GitHub Repo Search (e.g. 'SchemaSentinel-Strands')
    if not results:
        try:
            q_enc = raw_query.replace(" ", "+")
            req = urllib.request.Request(f"https://api.github.com/search/repositories?q={q_enc}&sort=stars&order=desc&per_page=8", headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    for item in data.get("items", []):
                        fn = item.get("full_name")
                        url = item.get("html_url")
                        owner = item.get("owner", {}).get("login", "")
                        if fn and url and owner:
                            results.append((fn, url, owner))
        except Exception:
            pass

    # 4. Tavily Live Grounding Search
    if not results:
        tavily_key = os.getenv("TAVILY_API_KEY")
        if tavily_key:
            try:
                from tavily import TavilyClient
                t_client = TavilyClient(api_key=tavily_key)
                resp = t_client.search(
                    query=f"{raw_query} site:github.com",
                    search_depth="basic",
                    include_domains=["github.com"],
                    max_results=8
                )
                for item in resp.get("results", []):
                    u = item.get("url", "")
                    m = RE_GITHUB_REPO.match(u)
                    if m and not any(b in u for b in BANNED_URL_SLUGS):
                        owner, repo = m.group(1), m.group(2)
                        slug = f"{owner}/{repo}"
                        entry = (slug, f"https://github.com/{owner}/{repo}", owner)
                        if entry not in results:
                            results.append(entry)
            except Exception:
                pass

    if results:
        _STREAM_RESOLVER_CACHE[raw_query] = results

    return results


def _build_batch_envelope(idx: int, title: str, author: str, base_url: str, now_ms: int, topic_tag: str = "") -> Dict[str, Any]:
    unique_url = f"{base_url}?stream_run={now_ms}_b{idx+1}"
    score = random.randint(86, 98)

    if idx == 0:
        mutated_rec = {
            "title": title,
            "author": author,
            "source_url": unique_url,
            "relevance_score": score
        }
        drift_title = f"{topic_tag}Clean Reference" if topic_tag else "Clean Reference"
        fix_summary = "100% Contract Match"
        batch_slug = "clean"
    else:
        mutated_rec, drift_name, fix_summary = ChaosSchemaMutator.mutate(
            title, author, unique_url, score, batch_index=idx
        )
        drift_title = f"{topic_tag}{drift_name}" if topic_tag else drift_name
        batch_slug = "drift"

    return {
        "batch_id": f"batch_{now_ms % 10000}_{batch_slug}_{idx+1}",
        "short_title": drift_title,
        "fix_summary": fix_summary,
        "records": [mutated_rec]
    }


def fetch_multi_topic_stream_batches(
    topics: List[str],
    topic_cursors: Dict[str, int],
    batch_size: int = 5
) -> Tuple[List[Dict[str, Any]], Dict[str, int], str]:
    if not topics:
        return [], topic_cursors, "No topics selected"

    now_ms = int(time.time() * 1000)
    batches = []

    # Resolve each topic live first; fall back to the offline catalog only when
    # GitHub/Tavily are unreachable or rate-limited. This keeps preset partitions
    # demo-stable while proving the engine ingests real upstream data.
    def _resolve_pool(t_name: str) -> List[Tuple[str, str, str]]:
        live = resolve_live_upstream_records(t_name)
        if live:
            return live
        return TOPIC_CATALOG.get(t_name, [])

    # CASE A: MULTIPLE PRESET PARTITIONS (round-robin)
    if len(topics) > 1:
        summary_desc = f"Round-Robin across {len(topics)} active partition(s) with live grounding"
        for i in range(batch_size):
            t_name = topics[i % len(topics)]
            pool = _resolve_pool(t_name)
            if not pool:
                continue
            offset = topic_cursors.get(t_name, 0)
            item = pool[offset % len(pool)]
            topic_cursors[t_name] = offset + 1

            tag = f"[{t_name[:18]}..] "
            batches.append(_build_batch_envelope(i, item[0], item[2], item[1], now_ms, topic_tag=tag))

        return batches, topic_cursors, summary_desc

    # CASE B: SINGLE TOPIC / REPOSITORY / USER
    single_topic = topics[0]
    pool = _resolve_pool(single_topic)

    # STRICT: NO FAKE FALLBACK DATA!
    if not pool:
        return [], topic_cursors, f"0 streams found for '{single_topic}'"

    offset = topic_cursors.get(single_topic, 0)
    topic_cursors[single_topic] = offset + batch_size

    for i in range(min(batch_size, len(pool))):
        item = pool[(offset + i) % len(pool)]
        batches.append(_build_batch_envelope(i, item[0], item[2], item[1], now_ms))

    return batches, topic_cursors, f"Live Grounded Stream for '{single_topic}' ({len(batches)} batches)"
