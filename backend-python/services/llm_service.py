import json
import re
import logging
import time
from typing import Optional
from models import HealingDecision
from config import settings

logger = logging.getLogger(__name__)

# Load the system prompt from prompts/system-prompt.md, falling back to inline if not found
def _load_system_prompt() -> str:
    """Load system prompt from file, fallback to inline version."""
    import os
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "system-prompt.md")
    # Also try parent directory (when running from backend-python/)
    if not os.path.exists(prompt_path):
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "system-prompt.md")
    
    try:
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"Loaded system prompt from {prompt_path}")
            return content
    except Exception as e:
        logger.warning(f"Failed to load system prompt file: {e}")
    
    # Inline fallback (aligned with prompts/system-prompt.md JSON Schema)
    return """你是一个顶级 Kubernetes SRE 专家 KubeSentinel。
你的任务是根据收到的告警与上下文观测数据，分析问题并给出自动化自愈决策。
你必须严格按照以下 JSON 格式输出，不要包含任何 markdown 符号或额外文本。

所需 JSON 输出结构:
{
  "analysis": "<故障分析（中文，不超过200字）>",
  "root_cause": "<根本原因判断>",
  "confidence": 0.0 to 1.0,
  "action": "rolling_restart" | "scale_up" | "scale_down" | "rollback" | "cordon_node" | "evict_pods" | "delete_pod" | "adjust_hpa" | "investigate" | "no_action",
  "target": {
    "resource_type": "deployment" | "pod" | "node" | "hpa",
    "name": "resource-name",
    "namespace": "namespace-name"
  },
  "fallback": "fallback-action 或 null",
  "params": {},
  "risk_level": "low" | "medium" | "high",
  "human_approval_required": true | false,
  "notify": true | false,
  "summary_for_notification": "<推送到飞书/钉钉的简短摘要（不超过100字）>"
}

安全决策约束:
- 置信度 < 0.6: 必须 action="investigate", human_approval_required=true
- 置信度 0.6-0.75: 可执行操作, 但 human_approval_required=true
- 置信度 > 0.75: 允许自动执行
- risk_level="high": 无论置信度多高, human_approval_required=true
- 严禁在 JSON 外输出任何文字
"""


SYSTEM_PROMPT = _load_system_prompt()


def _extract_json_from_text(text: str) -> dict:
    """
    Extract JSON object from text that may contain markdown code blocks or extra text.
    Uses multiple strategies for robustness.
    """
    # Strategy 1: Try direct parse
    text_stripped = text.strip()
    try:
        return json.loads(text_stripped)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip markdown code blocks
    clean = re.sub(r'```(?:json)?\s*', '', text_stripped)
    clean = clean.replace('```', '').strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Find the first { ... } block using brace matching
    brace_depth = 0
    start_idx = -1
    for i, ch in enumerate(text_stripped):
        if ch == '{':
            if brace_depth == 0:
                start_idx = i
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
            if brace_depth == 0 and start_idx != -1:
                candidate = text_stripped[start_idx:i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    start_idx = -1
                    continue

    raise json.JSONDecodeError("No valid JSON object found in LLM output", text_stripped, 0)


class LLMService:
    """AI diagnosis service that calls LLM to analyze alerts and produce healing decisions."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        logger.info(f"LLMService initialized with provider: {self.provider}, model: {self._get_model_name()}")

    def _get_model_name(self) -> str:
        if self.provider == "openai":
            return settings.OPENAI_MODEL
        return settings.LLM_MODEL

    def _call_dashscope(self, messages: list) -> str:
        """Call DashScope (通义千问) API."""
        import dashscope
        from dashscope import Generation

        dashscope.api_key = settings.DASHSCOPE_API_KEY
        response = Generation.call(
            model=settings.LLM_MODEL,
            messages=messages,
            result_format='message',
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
        )
        if response.status_code == 200:
            return response.output.choices[0]['message']['content']
        else:
            raise Exception(f"DashScope API Error (status={response.status_code}): {response.message}")

    def _call_openai_compatible(self, messages: list) -> str:
        """Call OpenAI-compatible API (supports DeepSeek, GPT-4, etc.)."""
        import requests as http_requests

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "max_tokens": settings.LLM_MAX_TOKENS,
            "temperature": settings.LLM_TEMPERATURE,
        }
        resp = http_requests.post(
            f"{settings.OPENAI_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _call_llm(self, messages: list) -> str:
        """Route to the correct LLM provider."""
        if self.provider == "openai":
            return self._call_openai_compatible(messages)
        else:
            return self._call_dashscope(messages)

    def analyze_alert(
        self,
        alert_summary: str,
        metrics_context: str,
        logs_context: str,
        max_retries: int = 3,
    ) -> HealingDecision:
        """
        Call LLM to analyze the alert and return a structured HealingDecision.
        Includes retry logic and robust JSON extraction.
        """
        user_prompt = f"""【告警信息】
{alert_summary}

【上下文指标数据】
{metrics_context}

【上下文日志摘要】
{logs_context}

请分析上述情况，决定是否需要执行自愈操作，以及对哪个目标执行操作。严格按 JSON 格式输出。"""

        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_prompt}
        ]

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Calling LLM API (attempt {attempt}/{max_retries}), provider: {self.provider}")
                content = self._call_llm(messages)
                logger.info(f"LLM Raw Output: {content[:500]}")

                result_dict = _extract_json_from_text(content)
                decision = HealingDecision(**result_dict)
                logger.info(
                    f"LLM Decision: action={decision.action}, target={decision.target.name}, "
                    f"confidence={decision.confidence}, risk={decision.risk_level}"
                )
                return decision

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"Attempt {attempt}: Failed to parse LLM JSON output: {e}")
                if attempt < max_retries:
                    time.sleep(1)
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt}: LLM API error: {e}")
                if attempt < max_retries:
                    time.sleep(2)

        logger.error(f"All {max_retries} LLM attempts failed. Last error: {last_error}")
        # Return a safe fallback decision
        return HealingDecision(
            analysis=f"LLM 分析失败（{max_retries}次重试后仍无法获取有效响应）: {str(last_error)}",
            root_cause="LLM 服务异常",
            confidence=0.0,
            action="investigate",
            target={"resource_type": "unknown", "name": "unknown", "namespace": "default"},
            risk_level="high",
            human_approval_required=True,
            notify=True,
            summary_for_notification="⚠️ AI 诊断引擎暂时不可用，请人工排查",
        )
