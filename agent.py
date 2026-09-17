import os
import re
import json
import logging
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("SchemaSentinel.Agent")

RE_CODE_BLOCK = re.compile(r"```(?:python)?\s*(.*?)\s*```", re.DOTALL)
RE_DEF_BLOCK = re.compile(r"(def\s+[a-zA-Z0-9_]+\s*\([^)]*\):.*)", re.DOTALL)


class SchemaHealingAgent:
    """
    Autonomous Schema Healing Agent:
    Monitors upstream schema mutations and dynamically synthesizes Python 
    transformation functions to adapt breaking payloads into target warehouse contracts.
    
    Architecture:
    1. Primary Ingress Engine: AWS Bedrock Mantle / Runtime
    2. Resilient Fallback Engine: Nebius Studio SOTA LLM (Zero hardcoded rules)
    3. Failure Defense: Direct routing to Dead Letter Queue (DLQ)
    """

    def __init__(self):
        # 1. AWS Bedrock Mantle Configuration
        self.bedrock_api_key = os.getenv("BEDROCK_API_KEY", "")
        self.aws_region = os.getenv("AWS_REGION", "us-west-2")
        self.bedrock_base_url = os.getenv(
            "BEDROCK_BASE_URL",
            f"https://bedrock-mantle.{self.aws_region}.api.aws/v1"
        )
        self.bedrock_model = os.getenv("BEDROCK_MODEL", "xai.grok-4.6")

        self.bedrock_client = OpenAI(
            base_url=self.bedrock_base_url,
            api_key=self.bedrock_api_key or "sk-bedrock-mantle-placeholder",
        )

        # 2. Nebius Studio LLM Fallback Configuration
        self.nebius_api_key = os.getenv("NEBIUS_API_KEY", "")
        self.nebius_base_url = "https://api.studio.nebius.ai/v1"
        self.nebius_model = os.getenv("NEBIUS_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507")

        self.nebius_client = None
        if self.nebius_api_key:
            self.nebius_client = OpenAI(
                base_url=self.nebius_base_url,
                api_key=self.nebius_api_key
            )

    def _build_prompt(self, failing_records: list, target_schema: str, error_trace: str) -> tuple:
        system_prompt = """You are an Autonomous Data Reliability Engineer for streaming pipelines.
Your mission is to analyze drifted JSON payloads and synthesize a pure, memory-isolated Python transformation function:
`def transform_record(record: dict) -> dict:`

Target Database Contract Requirements:
- 'title' (TEXT NOT NULL): Project name, repo identifier, or clean headline.
- 'author' (TEXT NOT NULL): Maintainer, organization login, creator, or parsed from github URL.
- 'source_url' (TEXT UNIQUE NOT NULL): Valid URL starting with http:// or https://.
- 'relevance_score' (INTEGER NOT NULL): Scaled integer from 0 to 100 (coerce floats, strings, percentages like '95%').

Constraints:
1. Return ONLY executable Python code inside a ```python ``` markdown codeblock.
2. AST Isolation: Do NOT import os, sys, subprocess, or call eval/exec."""

        user_content = f"""Target SQLite Schema Contract:
{target_schema}

Sample Drifting Payloads:
{json.dumps(failing_records[:2], indent=2)}

Ingress Validation Error:
{error_trace}

Generate the transform_record function to heal this schema drift:"""

        return system_prompt, user_content

    def synthesize_transformation_patch(
        self,
        failing_records: list,
        target_schema: str,
        error_trace: str
    ) -> str:
        """
        Synthesizes code via Primary Engine (Bedrock).
        If Bedrock encounters quota/auth errors, delegates directly to Nebius LLM.
        """
        system_prompt, user_content = self._build_prompt(failing_records, target_schema, error_trace)

        # Primary Attempt: AWS Bedrock Mantle
        try:
            logger.info(f"Synthesizing patch via Primary Engine (Bedrock Mantle - {self.bedrock_model})...")
            response = self.bedrock_client.chat.completions.create(
                model=self.bedrock_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0,
                max_tokens=900,
            )
            patch = response.choices[0].message.content or ""
            if patch.strip():
                return patch
        except Exception as bedrock_err:
            logger.warning(f"Primary Bedrock invocation failed: {bedrock_err}")

        # Secondary Resilient Attempt: Nebius Studio LLM
        if self.nebius_client:
            try:
                logger.info(f"Delegating synthesis to Secondary Engine (Nebius - {self.nebius_model})...")
                response = self.nebius_client.chat.completions.create(
                    model=self.nebius_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.1,
                    max_tokens=900,
                )
                patch = response.choices[0].message.content or ""
                if patch.strip():
                    return patch
            except Exception as nebius_err:
                logger.error(f"Secondary Nebius invocation failed: {nebius_err}")

        # If both LLMs are unreachable, route to Dead Letter Queue (Zero fake mocking)
        raise RuntimeError("Agentic Synthesis Failure: Both AWS Bedrock and Nebius LLMs failed to respond. Payload routed to DLQ.")

    def extract_pure_code(self, raw_patch: str) -> str:
        """Extracts and verifies Python function definition from LLM markdown response."""
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

        return text.strip()