"""
AI Consultant - LLM-Powered Portfolio Q&A

Enables users to ask natural language questions about their portfolio:
- "Should I sell my Bitcoin now?"
- "What's my largest tax liability?"
- "Which positions are at a loss?"
- "What are my staking rewards?"
- "How much in unrealized taxes?"

Uses OpenAI GPT-4 (or Claude) with context about the user's portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import json

import pandas as pd


@dataclass
class PortfolioContext:
    """User's portfolio data for AI context."""
    
    total_usd_value: float
    total_cost_basis: float
    unrealized_gains: float
    
    positions: list[dict]  # [{"asset": "BTC", "qty": 1.0, "price": 50000, ...}]
    transactions: list[dict]  # Recent transactions for context
    
    income_events: list[dict]  # Staking, airdrops, lending income
    tax_loss_harvesting_opportunities: list[dict]  # Suggested loss harvesting
    
    total_income: float
    estimated_tax_liability: float
    
    def to_llm_context(self) -> str:
        """Format portfolio as context for LLM."""
        positions_text = "\n".join([
            f"- {p['asset']}: {p['qty']} units @ ${p['price']:,.2f} = ${p['total_value']:,.2f} "
            f"({'gain' if p['unrealized_gain'] > 0 else 'loss'}: "
            f"${abs(p['unrealized_gain']):,.2f})"
            for p in self.positions
        ])
        
        context = f"""
Portfolio Summary:
- Total Value: ${self.total_usd_value:,.2f}
- Cost Basis: ${self.total_cost_basis:,.2f}
- Unrealized Gains: ${self.unrealized_gains:,.2f}
- Estimated Tax Liability: ${self.estimated_tax_liability:,.2f}
- Total Income (staking, airdrops, etc.): ${self.total_income:,.2f}

Top Positions:
{positions_text}

Income Events (YTD):
{self._format_income_events()}

Tax Optimization Opportunities:
{self._format_opportunities()}
"""
        return context
    
    def _format_income_events(self) -> str:
        """Format income events for LLM context."""
        if not self.income_events:
            return "- No income events recorded"
        
        by_type = {}
        for event in self.income_events:
            event_type = event.get("type", "UNKNOWN")
            by_type[event_type] = by_type.get(event_type, 0) + event.get("amount", 0)
        
        return "\n".join([
            f"- {k}: ${v:,.2f}"
            for k, v in by_type.items()
        ])
    
    def _format_opportunities(self) -> str:
        """Format tax optimization opportunities for LLM."""
        if not self.tax_loss_harvesting_opportunities:
            return "- No immediate opportunities detected"
        
        return "\n".join([
            f"- {opp['asset']}: Realize ${opp['loss']:,.2f} loss to offset gains"
            for opp in self.tax_loss_harvesting_opportunities[:5]  # Top 5
        ])


class AIConsultantPrompts:
    """Pre-built prompts for common portfolio questions."""
    
    @staticmethod
    def system_prompt() -> str:
        """System prompt for AI consultant."""
        return """You are an expert crypto tax and portfolio management consultant. 
You have deep knowledge of:
- Cryptocurrency taxation (US, EU, Brazil, etc.)
- Capital gains optimization strategies
- Risk management and diversification
- DeFi protocols and their tax implications
- Exchange rates and FX considerations

Your role is to provide accurate, actionable advice based on the user's portfolio data.
Always:
1. Cite specific numbers from their portfolio
2. Explain the tax implications clearly
3. Suggest 2-3 concrete action items
4. Warn about potential risks or wash sale rules
5. Consider their holding periods (long-term vs short-term)

Be concise but thorough. Use emoji for clarity. Always include specific USD amounts."""
    
    @staticmethod
    def make_question_prompt(question: str, portfolio_context: PortfolioContext) -> str:
        """Create user prompt with question + portfolio context."""
        return f"""{portfolio_context.to_llm_context()}

User Question: {question}

Please answer based on their specific portfolio and provide actionable recommendations."""
    
    @staticmethod
    def analyze_tax_liability_prompt(portfolio: PortfolioContext) -> str:
        """Prompt to analyze total tax liability."""
        return f"""{portfolio.to_llm_context()}

Analyze this portfolio's total tax liability. Consider:
1. Unrealized capital gains (if sold today): ${portfolio.unrealized_gains:,.2f}
2. Recent income (staking, airdrops, etc.): ${portfolio.total_income:,.2f}
3. Long-term vs short-term status

Provide:
- Estimated tax breakdown (federal, state if applicable)
- Ways to optimize the tax bill
- Timeline for tax-deferred strategies"""
    
    @staticmethod
    def identify_opportunities_prompt(portfolio: PortfolioContext) -> str:
        """Prompt to identify tax optimization opportunities."""
        return f"""{portfolio.to_llm_context()}

What are the top 3 tax optimization opportunities for this portfolio?
Rank by impact (potential tax savings).
For each, explain:
1. The strategy
2. Tax savings potential
3. Implementation steps
4. Any risks or considerations"""


class AIConsultant:
    """Main AI consultant interface."""
    
    def __init__(self, api_provider: str = "openai", api_key: Optional[str] = None):
        """Initialize AI consultant.
        
        Args:
            api_provider: "openai" or "anthropic"
            api_key: API key for the provider
        """
        self.api_provider = api_provider
        self.api_key = api_key
        self.model = self._select_model()
    
    def _select_model(self) -> str:
        """Select appropriate model based on provider."""
        if self.api_provider == "openai":
            return "gpt-4-turbo-preview"  # Or gpt-4, gpt-3.5-turbo
        elif self.api_provider == "anthropic":
            return "claude-3-opus-20240229"
        else:
            return "gpt-4-turbo-preview"  # Default
    
    def ask_question(
        self,
        question: str,
        portfolio_context: PortfolioContext,
    ) -> dict:
        """Ask AI consultant a question about the portfolio.
        
        Returns:
            {
                "question": "...",
                "answer": "...",
                "confidence": 0.95,
                "citations": ["Position XYZ", "Tax rule...", ...],
                "action_items": ["Sell position ABC", ...],
            }
        """
        
        # Build prompt
        user_prompt = AIConsultantPrompts.make_question_prompt(question, portfolio_context)
        
        # Call LLM (placeholder - actual implementation uses API)
        response = self._call_llm(
            system_prompt=AIConsultantPrompts.system_prompt(),
            user_prompt=user_prompt,
        )
        
        # Parse response
        return {
            "question": question,
            "answer": response.get("text", ""),
            "confidence": response.get("confidence", 0.85),
            "citations": self._extract_citations(response.get("text", "")),
            "action_items": self._extract_action_items(response.get("text", "")),
        }
    
    def analyze_tax_liability(self, portfolio: PortfolioContext) -> dict:
        """Analyze total tax liability with optimization recommendations."""
        
        prompt = AIConsultantPrompts.analyze_tax_liability_prompt(portfolio)
        
        response = self._call_llm(
            system_prompt=AIConsultantPrompts.system_prompt(),
            user_prompt=prompt,
        )
        
        return {
            "analysis": response.get("text", ""),
            "estimated_total_tax": portfolio.estimated_tax_liability,
            "long_term_rate": 0.15,
            "short_term_rate": 0.35,
            "optimization_strategies": self._extract_strategies(
                response.get("text", "")
            ),
        }
    
    def identify_opportunities(self, portfolio: PortfolioContext) -> dict:
        """Identify top tax optimization opportunities."""
        
        prompt = AIConsultantPrompts.identify_opportunities_prompt(portfolio)
        
        response = self._call_llm(
            system_prompt=AIConsultantPrompts.system_prompt(),
            user_prompt=prompt,
        )
        
        opportunities = self._parse_opportunities(response.get("text", ""))
        
        return {
            "opportunities": opportunities,
            "total_potential_savings": self._estimate_savings(opportunities),
            "recommended_priority_order": [o["title"] for o in opportunities],
        }
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> dict:
        """Call the LLM API.
        
        This is a placeholder - actual implementation would use:
        - openai.ChatCompletion.create()
        - anthropic.Anthropic().messages.create()
        """
        
        # TODO: Implement actual API calls
        # For now, return mock response
        
        if self.api_provider == "openai":
            # import openai
            # response = openai.ChatCompletion.create(
            #     model=self.model,
            #     messages=[
            #         {"role": "system", "content": system_prompt},
            #         {"role": "user", "content": user_prompt}
            #     ],
            #     temperature=0.7,
            #     max_tokens=1500,
            # )
            pass
        elif self.api_provider == "anthropic":
            # import anthropic
            # client = anthropic.Anthropic(api_key=self.api_key)
            # response = client.messages.create(
            #     model=self.model,
            #     max_tokens=1500,
            #     system=system_prompt,
            #     messages=[{"role": "user", "content": user_prompt}]
            # )
            pass
        
        # Mock response for development
        return {
            "text": "Based on your portfolio, I recommend...",
            "confidence": 0.85,
        }
    
    @staticmethod
    def _extract_citations(text: str) -> list[str]:
        """Extract citations/references from response."""
        # Simple heuristic: lines starting with numbers or bullets
        lines = text.split("\n")
        citations = [
            line.strip() for line in lines
            if line.strip() and (line.strip()[0].isdigit() or line.strip()[0] in "•-*")
        ]
        return citations[:5]  # Top 5 citations
    
    @staticmethod
    def _extract_action_items(text: str) -> list[str]:
        """Extract recommended action items."""
        # Look for patterns like "You should...", "Consider...", "Execute..."
        action_keywords = ["execute", "sell", "buy", "hold", "realize", "harvest"]
        
        lines = text.split(".")
        actions = [
            line.strip() + "."
            for line in lines
            if any(keyword in line.lower() for keyword in action_keywords)
        ]
        return actions[:3]  # Top 3 actions
    
    @staticmethod
    def _extract_strategies(text: str) -> list[dict]:
        """Extract tax optimization strategies."""
        # This would parse numbered/bulleted strategies from the response
        strategies = []
        
        # Simple parsing: look for numbered items
        lines = text.split("\n")
        for line in lines:
            if line.strip() and line.strip()[0].isdigit():
                strategies.append({
                    "description": line.strip(),
                    "priority": "high" if "immediately" in line.lower() else "medium"
                })
        
        return strategies[:5]
    
    @staticmethod
    def _parse_opportunities(text: str) -> list[dict]:
        """Parse opportunities from response."""
        # Structure: [{"title": "Strategy X", "savings": 5000, ...}]
        
        opportunities = []
        sections = text.split("\n\n")
        
        for i, section in enumerate(sections, 1):
            if section.strip():
                opportunities.append({
                    "rank": i,
                    "title": section.split("\n")[0].strip(),
                    "description": section.strip(),
                    "estimated_savings": 0,  # Would parse from text
                })
        
        return opportunities[:5]
    
    @staticmethod
    def _estimate_savings(opportunities: list[dict]) -> float:
        """Estimate total potential tax savings."""
        # Sum up savings from all opportunities
        return sum(o.get("estimated_savings", 0) for o in opportunities)


# ==================== PRESET QUESTIONS ====================

PRESET_QUESTIONS = {
    "portfolio_summary": "What's my overall portfolio status? What should I focus on?",
    "tax_liability": "What's my total tax liability if I liquidate today?",
    "loss_harvest": "Which positions should I harvest losses from?",
    "long_term_gains": "Which of my positions qualify for long-term capital gains?",
    "income_tax": "What's my estimated income tax from staking/airdrops/lending?",
    "optimization": "What's the single most impactful thing I can do to reduce my tax bill?",
    "timeline": "If I wait 3 more months before selling, how would that affect my taxes?",
    "diversification": "Is my portfolio properly diversified? Am I too concentrated?",
    "risk_assessment": "What positions are at greatest risk? Should I be concerned?",
    "strategy": "What's your recommended trading/holding strategy for the next quarter?",
}


# ==================== API INTEGRATION ====================
"""
Add to your FastAPI app:

from app.tax.ai_consultant import (
    AIConsultant,
    PortfolioContext,
    PRESET_QUESTIONS
)
from decimal import Decimal

@app.post("/ai/ask-question")
def ask_consultant(
    question: str,
    run_id: int,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Ask AI consultant a question about your portfolio.'''
    
    # Get analysis run
    run = db.query(AnalysisRun).filter(
        AnalysisRun.id == run_id,
        AnalysisRun.user_id == current_user.id
    ).first()
    if not run:
        raise HTTPException(status_code=404)
    
    # Load portfolio data from analysis results
    analysis_data = json.load(open(run.analysis_json_path))
    
    # Create portfolio context
    portfolio_context = PortfolioContext(
        total_usd_value=float(analysis_data.get("total_value", 0)),
        total_cost_basis=float(analysis_data.get("cost_basis", 0)),
        unrealized_gains=float(analysis_data.get("unrealized_gains", 0)),
        positions=analysis_data.get("positions", []),
        transactions=analysis_data.get("recent_transactions", []),
        income_events=analysis_data.get("income_events", []),
        tax_loss_harvesting_opportunities=analysis_data.get("tax_loss_harvesting", []),
        total_income=float(analysis_data.get("total_income", 0)),
        estimated_tax_liability=float(analysis_data.get("estimated_tax", 0)),
    )
    
    # Initialize consultant (set API keys from env)
    consultant = AIConsultant(
        api_provider="openai",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Get answer
    response = consultant.ask_question(question, portfolio_context)
    
    return response


@app.get("/ai/presets")
def get_preset_questions():
    '''Get list of preset questions users can ask.'''
    return {
        "presets": [
            {"id": key, "question": value}
            for key, value in PRESET_QUESTIONS.items()
        ]
    }


@app.post("/ai/analyze-taxes")
def analyze_taxes(
    run_id: int,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Get AI analysis of your total tax liability and optimization strategies.'''
    
    # [Load portfolio context - same as above]
    
    consultant = AIConsultant(
        api_provider="openai",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    analysis = consultant.analyze_tax_liability(portfolio_context)
    
    return analysis


@app.post("/ai/opportunities")
def find_opportunities(
    run_id: int,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Identify top tax optimization opportunities ranked by impact.'''
    
    # [Load portfolio context]
    
    consultant = AIConsultant(
        api_provider="openai",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    opportunities = consultant.identify_opportunities(portfolio_context)
    
    return opportunities
"""
