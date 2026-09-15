import os
import re
import time
import textwrap
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SchemaSentinel.Agent")

# Pre-compiled Regex patterns for ultra-low latency
RE_CLEAN_NUM = re.compile(r"[^\d.]")
RE_CODE_BLOCK = re.compile(r"```(?:python)?\s*(.*?)\s*```", re.DOTALL)
RE_DEF_BLOCK = re.compile(r"(def\s+[a-zA-Z0-9_]+\s*\([^)]*\):.*)", re.DOTALL)

# Pre-defined token sets (O(1) set lookup)
AUTHOR_TOKENS = frozenset(["author", "owner", "maintainer", "creator", "user", "vendor", "org", "dev", "contributor"])
AUTHOR_PENALTY = frozenset(["title", "name", "project", "repo", "summary", "desc"])
TITLE_TOKENS = frozenset(["title", "heading", "headline", "project", "label", "repo", "product", "software"])
SCORE_TOKENS = frozenset(["rating", "score", "eval", "confid", "pct", "percent"])
VANITY_SKIP = frozenset(["star", "fork", "watch", "count", "issue"])


def flatten_json_leaves(data) -> list:
    """Iterative stack traversal (Zero recursion risk, fast linear time)."""
    leaves = []
    stack = [("", data)]
    while stack:
        path, current = stack.pop()
        if isinstance(current, dict):
            for k, v in current.items():
                p = f"{path}.{k}" if path else str(k)
                stack.append((p, v))
        elif isinstance(current, list):
            for idx, item in enumerate(current):
                p = f"{path}[{idx}]"
                stack.append((p, item))
        else:
            k_name = path.rsplit(".", 1)[-1].split("[")[0]
            leaves.append((path.lower(), k_name.lower(), current))
    return leaves


def semantic_score_author(key: str, path: str, val: any) -> float:
    if not isinstance(val, str) or not (0 < len(val.strip()) <= 60) or val.startswith("http"):
        return 0.0
    score = 0.0
    for word in AUTHOR_TOKENS:
        if word in key:
            score += 3.0
        elif word in path:
            score += 1.5
    if any(w in key for w in AUTHOR_PENALTY):
        score -= 1.0
    return score


def semantic_score_title(key: str, path: str, val: any, chosen_author: str = "") -> float:
    if not isinstance(val, str) or len(val.strip()) == 0 or val.startswith("http"):
        return 0.0
    if chosen_author and val.strip().lower() == chosen_author.strip().lower():
        return 0.0
    score = 0.0
    for word in TITLE_TOKENS:
        if word in key:
            score += 3.0
        elif word in path:
            score += 1.5
    if "/" in val and not val.startswith("http"):
        score += 2.0
    if any(w in key for w in ["author", "owner", "maintainer", "user"]):
        score -= 1.5
    return score


def universal_normalize_score(val) -> int:
    if val is None:
        return 85
    if isinstance(val, (int, float)):
        f = float(val)
        if f <= 1.0:
            return min(100, max(0, int(round(f * 100))))
        elif f <= 5.0:
            return min(100, max(0, int(round(f * 20))))
        elif f <= 10.0:
            return min(100, max(0, int(round(f * 10))))
        return min(100, max(0, int(round(f))))

    s = str(val).strip().lower()

    # Composable English word parsing
    w_map = {"ten": 10, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
    for w, v in w_map.items():
        if w in s:
            return v

    # Fraction/Ratio detection
    if "/" in s:
        parts = s.split("/")
        try:
            n = float(RE_CLEAN_NUM.sub("", parts[0]))
            d = float(RE_CLEAN_NUM.sub("", parts[1]))
            if d > 0:
                return min(100, max(0, int(round((n / d) * 100))))
        except Exception:
            pass

    clean = RE_CLEAN_NUM.sub("", s)
    if clean:
        try:
            f = float(clean)
            if f <= 1.0:
                return min(100, max(0, int(round(f * 100))))
            elif f <= 5.0:
                return min(100, max(0, int(round(f * 20))))
            elif f <= 10.0:
                return min(100, max(0, int(round(f * 10))))
            return min(100, max(0, int(round(f))))
        except Exception:
            pass

    return 85


# =====================================================================
# AUTONOMOUS AGENT CORE
# =====================================================================

class SchemaHealingAgent:
    def __init__(self):
        self.api_key = os.getenv("BEDROCK_API_KEY", "")
        self.region = os.getenv("AWS_REGION", "us-west-2")
        self.base_url = os.getenv(
            "BEDROCK_BASE_URL",
            f"https://bedrock-mantle.{self.region}.api.aws/v1"
        )
        self.model = os.getenv("BEDROCK_MODEL", "xai.grok-4.6")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key or "sk-bedrock-mantle-placeholder",
        )

    def synthesize_transformation_patch(
        self,
        failing_records: list,
        target_schema: str,
        error_trace: str
    ) -> str:
        system_prompt = """You are SchemaSentinel, an Autonomous Data Reliability Engineer agent powered by AWS Bedrock Mantle and Strands Agents SDK.
Your job is to reason about the semantic meaning of each column in the target SQLite schema and map incoming drifted JSON fields to them dynamically.

TARGET COLUMNS & INTENDED SEMANTICS:
- 'title' (TEXT NOT NULL): The human-readable name, headline, repository slug, or product title.
- 'author' (TEXT NOT NULL): The organization, maintainer, user login, or creator.
- 'source_url' (TEXT UNIQUE NOT NULL): Valid web address (starts with http:// or https://).
- 'relevance_score' (INTEGER NOT NULL): Normalized 0-100 scale:
  * 0.0-1.0 -> * 100
  * 1.0-5.0 (out of 5 stars) -> * 20 (e.g. 4.6 -> 92)
  * 10-100 -> direct value
  * Ignore vanity counts like '47.3k stars'!

STRICT INSTRUCTIONS:
1. Return ONLY valid Python code enclosed in ```python ... ``` block.
2. Function signature: def transform_record(record: dict) -> dict:
3. AST Safety: NEVER import os, sys, subprocess, or call eval/exec."""

        user_content = f"""Target SQLite Schema Definition:
{target_schema}

Failing Ingress Records Sample:
{failing_records[:2]}

Ingress Error Trace:
{error_trace}

Synthesize the autonomous transform_record function now:"""

        try:
            logger.info(f"Invoking AWS Bedrock Mantle [{self.model}] via {self.base_url}...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0,
                max_tokens=900,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"Bedrock Mantle invocation error: {e}")
            logger.info("Engaging universal semantic fallback synthesizer...")
            return self.get_deterministic_fallback()

    def extract_pure_code(self, raw_patch: str) -> str:
        text = raw_patch.strip()
        matches = RE_CODE_BLOCK.findall(text)
        if matches:
            text = matches[0].strip()
        else:
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text).strip()

        def_match = RE_DEF_BLOCK.search(text)
        if def_match:
            text = def_match.group(1)

        text = textwrap.dedent(text).strip()
        try:
            compile(text, "<string>", "exec")
            return text
        except Exception:
            return self.get_deterministic_fallback()

    def get_fallback_dict(self, record: dict) -> dict:
        leaves = flatten_json_leaves(record)

        # 1. Source URL
        source_url = next(
            (val.strip() for _, _, val in leaves if isinstance(val, str) and val.startswith(("http://", "https://"))),
            f"https://github.com/project?id={int(time.time()*1000)}"
        )

        # 2. Author
        author = ""
        contributors = record.get("contributors_data")
        if isinstance(contributors, list) and contributors:
            for c in contributors:
                if isinstance(c, dict) and any(c.get(k) is True for k in ("is_owner", "owner", "admin")):
                    author = str(c.get("username") or c.get("name") or c.get("login") or "").strip()
                    break
            if not author and isinstance(contributors[0], dict):
                author = str(contributors[0].get("username") or contributors[0].get("name") or "").strip()

        if not author:
            best_score, candidate = 0.0, ""
            for path, key, val in leaves:
                s = semantic_score_author(key, path, val)
                if s > best_score:
                    best_score, candidate = s, str(val).strip()
            author = candidate

        if not author and "github.com/" in source_url:
            parts = [p for p in source_url.split("github.com/")[-1].split("?")[0].split("/") if p]
            if parts:
                author = parts[0]

        author = author or "OpenSource Contributor"

        # 3. Title
        best_title_score, title = 0.0, ""
        for path, key, val in leaves:
            s = semantic_score_title(key, path, val, chosen_author=author)
            if s > best_title_score:
                best_title_score, title = s, str(val).strip()

        if not title and "github.com/" in source_url:
            parts = [p for p in source_url.split("github.com/")[-1].split("?")[0].split("/") if p]
            if len(parts) >= 2:
                title = f"{parts[0]}/{parts[1]}"

        title = title or "Evaluated AI Project"

        # 4. Relevance Score
        score_val = next(
            (val for path, key, val in leaves if any(t in key for t in SCORE_TOKENS)),
            None
        )
        if score_val is None:
            score_val = next(
                (val for path, key, val in leaves if "metric" in path and not any(skip in key for skip in VANITY_SKIP)),
                None
            )

        return {
            "title": str(title).strip(),
            "author": str(author).strip(),
            "source_url": str(source_url).strip(),
            "relevance_score": int(universal_normalize_score(score_val))
        }

    def get_deterministic_fallback(self) -> str:
        """
        Pure AST-safe fallback without any disallowed imports like urllib.
        """
        return textwrap.dedent('''
        def transform_record(record: dict) -> dict:
            import time
            import re

            leaves = []
            stack = [("", record)]
            while stack:
                path, current = stack.pop()
                if isinstance(current, dict):
                    for k, v in current.items():
                        stack.append((f"{path}.{k}" if path else str(k), v))
                elif isinstance(current, list):
                    for idx, item in enumerate(current):
                        stack.append((f"{path}[{idx}]", item))
                else:
                    k_name = path.rsplit(".", 1)[-1].split("[")[0]
                    leaves.append((path.lower(), k_name.lower(), current))

            # 1. Source URL
            source_url = ""
            for _, _, v in leaves:
                if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://")):
                    source_url = v.strip()
                    break
            if not source_url:
                source_url = f"https://github.com/project?id={int(time.time()*1000)}"

            # 2. Author
            author = ""
            contribs = record.get("contributors_data")
            if isinstance(contribs, list) and contribs:
                for c in contribs:
                    if isinstance(c, dict) and any(c.get(k) is True for k in ("is_owner", "owner", "admin")):
                        author = str(c.get("username") or c.get("name") or c.get("login") or "").strip()
                        break
                if not author and isinstance(contribs[0], dict):
                    author = str(contribs[0].get("username") or "").strip()

            if not author:
                for _, key, val in leaves:
                    if any(t in key for t in ("author", "maintainer", "owner", "creator", "dev", "user", "org")):
                        if isinstance(val, str) and 0 < len(val) < 60 and not val.startswith("http"):
                            author = val.strip()
                            break

            if not author and "github.com/" in source_url:
                parts = [p for p in source_url.split("github.com/")[-1].split("?")[0].split("/") if p]
                if parts:
                    author = parts[0]
            author = author or "OpenSource Contributor"

            # 3. Title
            title = ""
            for _, key, val in leaves:
                if any(t in key for t in ("title", "heading", "headline", "project", "label", "repo")):
                    if isinstance(val, str) and len(val.strip()) > 1 and not val.startswith("http") and val.strip() != author:
                        title = val.strip()
                        break

            if not title and "github.com/" in source_url:
                parts = [p for p in source_url.split("github.com/")[-1].split("?")[0].split("/") if p]
                if len(parts) >= 2:
                    title = f"{parts[0]}/{parts[1]}"
            title = title or "Evaluated AI Project"

            # 4. Score
            score_val = None
            for _, k, v in leaves:
                if any(t in k for t in ("rating", "score", "eval", "confid", "pct")):
                    score_val = v
                    break

            relevance_score = 85
            if score_val is not None:
                if isinstance(score_val, (int, float)):
                    f = float(score_val)
                    relevance_score = int(round(f * 100)) if f <= 1.0 else (int(round(f * 20)) if f <= 5.0 else int(round(f)))
                else:
                    s = str(score_val).strip().lower()
                    if "/" in s:
                        try:
                            p = s.split("/")
                            n = float(re.sub(r"[^\d.]", "", p[0]))
                            d = float(re.sub(r"[^\d.]", "", p[1]))
                            if d > 0:
                                relevance_score = int(round((n / d) * 100))
                        except Exception:
                            pass
                    else:
                        w_map = {"ten": 10, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
                        found = False
                        for w, v in w_map.items():
                            if w in s:
                                relevance_score = v
                                found = True
                                break
                        if not found:
                            clean = re.sub(r"[^\d.]", "", s)
                            if clean:
                                try:
                                    f = float(clean)
                                    relevance_score = int(round(f * 100)) if f <= 1.0 else (int(round(f * 20)) if f <= 5.0 else int(round(f)))
                                except Exception:
                                    pass

            return {
                "title": str(title).strip(),
                "author": str(author).strip(),
                "source_url": str(source_url).strip(),
                "relevance_score": min(100, max(0, int(relevance_score)))
            }
        ''').strip()