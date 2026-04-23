"""
LLM Provider Abstraction Layer.

Supports multiple backends via a single interface:
  - MockLLMProvider  (free, rule-based — DEFAULT)
  - OllamaLLMProvider (free, local LLM)
  - OpenAILLMProvider (paid, production)
  - AnthropicLLMProvider (paid, alternative)

Switch providers with the LLM_PROVIDER env var.
"""
from __future__ import annotations

import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    text: str
    model: str
    provider: str
    tokens_used: int = 0
    confidence: float = 0.85


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    name: str = "base"

    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.7, max_tokens: int = 1500) -> LLMResponse:
        """Send a chat request and get a response."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and available."""
        ...


# ---------------------------------------------------------------------------
# Mock Provider (FREE — rule-based responses)
# ---------------------------------------------------------------------------

class MockLLMProvider(LLMProvider):
    """
    Rule-based "AI" that analyzes portfolio data within the prompt
    and returns structured advice. No API keys needed.
    """

    name = "mock"

    def chat(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.7, max_tokens: int = 1500) -> LLMResponse:
        # Parse portfolio values from the prompt
        ctx = self._extract_context(user_prompt)
        response = self._generate_response(user_prompt, ctx)
        return LLMResponse(text=response, model="rule-engine-v1", provider="mock")

    def is_available(self) -> bool:
        return True

    def _extract_context(self, prompt: str) -> dict:
        """Extract numeric values from the portfolio context in the prompt."""
        ctx: dict = {}
        for line in prompt.split("\n"):
            line = line.strip()
            if "Total Value:" in line:
                ctx["total_value"] = self._extract_number(line)
            elif "Cost Basis:" in line:
                ctx["cost_basis"] = self._extract_number(line)
            elif "Unrealized Gains:" in line:
                ctx["unrealized_gains"] = self._extract_number(line)
            elif "Estimated Tax Liability:" in line:
                ctx["estimated_tax"] = self._extract_number(line)
            elif "Total Income" in line:
                ctx["total_income"] = self._extract_number(line)
        return ctx

    def _extract_number(self, text: str) -> float:
        """Extract a dollar amount from text."""
        import re
        match = re.search(r'\$[\d,]+\.?\d*', text)
        if match:
            return float(match.group().replace('$', '').replace(',', ''))
        return 0.0

    def _generate_response(self, prompt: str, ctx: dict) -> str:
        """Generate rule-based advice from portfolio data."""
        total = ctx.get("total_value", 0)
        gains = ctx.get("unrealized_gains", 0)
        tax = ctx.get("estimated_tax", 0)
        income = ctx.get("total_income", 0)
        cost = ctx.get("cost_basis", 0)

        question = prompt.split("User Question:")[-1].strip() if "User Question:" in prompt else prompt
        q_lower = question.lower()

        # Tax liability questions
        if any(w in q_lower for w in ["tax", "liability", "owe", "imposto"]):
            return (
                f"📊 **Tax Analysis**\n\n"
                f"Based on your portfolio:\n"
                f"- **Total Portfolio Value**: ${total:,.2f}\n"
                f"- **Cost Basis**: ${cost:,.2f}\n"
                f"- **Unrealized Gains**: ${gains:,.2f}\n"
                f"- **Estimated Tax**: ${tax:,.2f}\n\n"
                f"**Recommendations:**\n"
                f"1. {'Consider harvesting losses to offset gains' if gains > 0 else 'You have unrealized losses that could offset future gains'}\n"
                f"2. Check holding periods — positions held > 180 days may qualify for reduced rates\n"
                f"3. Track monthly sales vs R$35,000 exemption threshold\n\n"
                f"⚠️ *This is automated analysis. Consult a tax professional for personalized advice.*"
            )

        # Sell / optimization questions
        if any(w in q_lower for w in ["sell", "optimize", "reduce", "harvest", "vender"]):
            roi_pct = ((total - cost) / max(cost, 1)) * 100 if cost > 0 else 0
            return (
                f"💡 **Optimization Opportunities**\n\n"
                f"Your portfolio ROI: **{roi_pct:+.1f}%**\n\n"
                f"**Top Actions:**\n"
                f"1. Review positions with unrealized losses for tax-loss harvesting\n"
                f"2. {'Defer sales if approaching month-end exemption limit' if total > 20000 else 'You may be within the monthly exemption'}\n"
                f"3. Consider timing — holding for 180+ days can reduce capital gains rate from 35% to 15%\n\n"
                f"**Income Events (YTD)**: ${income:,.2f}\n"
                f"Remember: Staking rewards and airdrops are taxed as income at the time of receipt.\n\n"
                f"⚠️ *Automated analysis. Not financial advice.*"
            )

        # General portfolio summary
        return (
            f"📈 **Portfolio Summary**\n\n"
            f"| Metric | Value |\n"
            f"|--------|-------|\n"
            f"| Total Value | ${total:,.2f} |\n"
            f"| Cost Basis | ${cost:,.2f} |\n"
            f"| Unrealized P&L | ${gains:,.2f} |\n"
            f"| Income (YTD) | ${income:,.2f} |\n"
            f"| Est. Tax | ${tax:,.2f} |\n\n"
            f"**Key Points:**\n"
            f"- {'Your portfolio is in profit' if gains > 0 else 'Your portfolio shows unrealized losses'}\n"
            f"- {'You have income events to report' if income > 0 else 'No income events detected'}\n"
            f"- Monitor your monthly sales volume against exemption thresholds\n\n"
            f"💬 Ask me specific questions like:\n"
            f"- *What's my tax liability if I sell everything today?*\n"
            f"- *Which positions should I harvest losses from?*\n"
            f"- *How can I optimize my tax bill?*\n\n"
            f"⚠️ *Automated analysis. Upgrade to AI-powered mode for deeper insights.*"
        )


# ---------------------------------------------------------------------------
# Ollama Provider (FREE — local LLM)
# ---------------------------------------------------------------------------

class OllamaLLMProvider(LLMProvider):
    """Local LLM via Ollama. Free but requires Ollama running locally."""

    name = "ollama"

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1")

    def chat(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.7, max_tokens: int = 1500) -> LLMResponse:
        import httpx

        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        return LLMResponse(
            text=data.get("message", {}).get("content", ""),
            model=self.model,
            provider="ollama",
            tokens_used=data.get("eval_count", 0),
        )

    def is_available(self) -> bool:
        try:
            import httpx
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False


# ---------------------------------------------------------------------------
# OpenAI Provider (PAID — production upgrade)
# ---------------------------------------------------------------------------

class OpenAILLMProvider(LLMProvider):
    """OpenAI GPT-4 / GPT-3.5. Requires OPENAI_API_KEY."""

    name = "openai"

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    def chat(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.7, max_tokens: int = 1500) -> LLMResponse:
        import httpx

        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            text=choice,
            model=self.model,
            provider="openai",
            tokens_used=usage.get("total_tokens", 0),
        )

    def is_available(self) -> bool:
        return bool(self.api_key)


# ---------------------------------------------------------------------------
# Anthropic Provider (PAID — alternative upgrade)
# ---------------------------------------------------------------------------

class AnthropicLLMProvider(LLMProvider):
    """Anthropic Claude. Requires ANTHROPIC_API_KEY."""

    name = "anthropic"

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    def chat(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.7, max_tokens: int = 1500) -> LLMResponse:
        import httpx

        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        text = data["content"][0]["text"]
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            model=self.model,
            provider="anthropic",
            tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        )

    def is_available(self) -> bool:
        return bool(self.api_key)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PROVIDERS = {
    "mock": MockLLMProvider,
    "ollama": OllamaLLMProvider,
    "openai": OpenAILLMProvider,
    "anthropic": AnthropicLLMProvider,
}


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    """
    Get an LLM provider instance.

    Priority:
      1. Explicit provider_name argument
      2. LLM_PROVIDER env var
      3. Fallback to "mock" (always free)
    """
    name = (provider_name or os.getenv("LLM_PROVIDER", "mock")).lower()
    cls = _PROVIDERS.get(name, MockLLMProvider)
    return cls()
