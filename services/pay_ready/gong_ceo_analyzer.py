"""
Pay Ready CEO Business Intelligence - Gong Deep Analysis
Specialized module for extracting sales coaching insights and competitive intelligence
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass

from shared.logger.logging_config import logger
from shared.llm.custom_llm import CustomLLM, get_llm_factory


@dataclass
class SalesCoachingInsight:
    """Sales coaching analysis result"""
    rep_name: str
    call_id: str
    strengths: List[str]
    improvement_areas: List[str]
    talk_time_ratio: float
    question_quality_score: float
    objection_handling_score: float
    next_actions: List[str]


@dataclass
class CompetitiveIntelligence:
    """Competitive intelligence from calls"""
    call_id: str
    competitor_mentioned: str
    context: str
    client_sentiment: str
    our_position: str
    action_items: List[str]


@dataclass
class ClientHealthSignal:
    """Client health indicators from interactions"""
    client_name: str
    health_score: float  # 0-100
    sentiment_trend: str  # improving, declining, stable
    risk_factors: List[str]
    engagement_level: str
    renewal_likelihood: float


class GongCEOAnalyzer:
    """Advanced Gong analysis for CEO business intelligence"""
    
    def __init__(self):
        self.gong_api_key = os.getenv("GONG_API_KEY")
        self.gong_base_url = "https://api.gong.io/v2"
        self.llm = get_llm_factory().get_llm("gpt-4")
        self.session = None
        
    async def initialize(self):
        """Initialize HTTP session and validate API access"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.gong_api_key}",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=300)
        )
        logger.info("Gong CEO Analyzer initialized")
        
    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            
    async def analyze_recent_calls_for_ceo(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Comprehensive CEO analysis of recent sales calls
        """
        logger.info(f"Starting CEO analysis for calls from last {days_back} days")
        
        # Get recent calls
        calls = await self._get_recent_calls(days_back)
        
        results = {
            "analysis_period": f"Last {days_back} days",
            "total_calls_analyzed": len(calls),
            "sales_coaching_insights": [],
            "competitive_intelligence": [],
            "client_health_signals": [],
            "key_metrics": {},
            "executive_summary": ""
        }
        
        for call in calls:
            # Get detailed call data
            call_details = await self._get_call_details(call["id"])
            
            if call_details and call_details.get("transcript"):
                # Sales coaching analysis
                coaching_insight = await self._analyze_sales_performance(call_details)
                if coaching_insight:
                    results["sales_coaching_insights"].append(coaching_insight)
                
                # Competitive intelligence
                competitive_intel = await self._extract_competitive_intelligence(call_details)
                if competitive_intel:
                    results["competitive_intelligence"].extend(competitive_intel)
                
                # Client health signals
                client_health = await self._assess_client_health(call_details)
                if client_health:
                    results["client_health_signals"].append(client_health)
        
        # Generate executive metrics and summary
        results["key_metrics"] = await self._calculate_ceo_metrics(results)
        results["executive_summary"] = await self._generate_executive_summary(results)
        
        logger.info(f"CEO analysis complete: {len(results['sales_coaching_insights'])} coaching insights, "
                   f"{len(results['competitive_intelligence'])} competitive mentions")
        
        return results
    
    async def _get_recent_calls(self, days_back: int) -> List[Dict]:
        """Get calls from the specified time period"""
        from_date = datetime.now() - timedelta(days=days_back)
        
        params = {
            "fromDateTime": from_date.isoformat(),
            "toDateTime": datetime.now().isoformat(),
            "cursor": None,
            "limit": 100
        }
        
        all_calls = []
        
        try:
            while True:
                async with self.session.get(f"{self.gong_base_url}/calls", params=params) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch calls: {response.status}")
                        break
                        
                    data = await response.json()
                    calls = data.get("calls", [])
                    all_calls.extend(calls)
                    
                    # Check for more pages
                    cursor = data.get("records", {}).get("cursor")
                    if not cursor:
                        break
                    params["cursor"] = cursor
                    
        except Exception as e:
            logger.error(f"Error fetching calls: {e}")
            
        return all_calls
    
    async def _get_call_details(self, call_id: str) -> Optional[Dict]:
        """Get detailed call information including transcript"""
        try:
            async with self.session.get(f"{self.gong_base_url}/calls/{call_id}/transcript") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Could not fetch transcript for call {call_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching call details for {call_id}: {e}")
            return None
    
    async def _analyze_sales_performance(self, call_details: Dict) -> Optional[SalesCoachingInsight]:
        """AI-powered sales performance analysis"""
        try:
            transcript = call_details.get("transcript", "")
            participants = call_details.get("participants", [])
            
            # Find sales rep (internal participant)
            sales_rep = None
            for participant in participants:
                if participant.get("emailAddress", "").endswith("@payready.com"):
                    sales_rep = participant.get("name", "Unknown Rep")
                    break
            
            if not sales_rep or not transcript:
                return None
            
            # Calculate talk time ratio
            talk_time_ratio = await self._calculate_talk_time_ratio(transcript, sales_rep)
            
            # AI analysis prompt
            analysis_prompt = f"""
            Analyze this sales call transcript for coaching insights:
            
            Sales Rep: {sales_rep}
            Transcript: {transcript[:4000]}...
            
            Provide analysis in JSON format:
            {{
                "strengths": ["strength1", "strength2"],
                "improvement_areas": ["area1", "area2"], 
                "question_quality_score": 0-100,
                "objection_handling_score": 0-100,
                "next_actions": ["action1", "action2"]
            }}
            
            Focus on:
            - Discovery question quality
            - Value proposition delivery
            - Objection handling
            - Closing techniques
            - Overall professionalism
            """
            
            analysis_response = await self.llm.achat(analysis_prompt)
            analysis_data = json.loads(analysis_response.message.content)
            
            return SalesCoachingInsight(
                rep_name=sales_rep,
                call_id=call_details.get("id"),
                strengths=analysis_data.get("strengths", []),
                improvement_areas=analysis_data.get("improvement_areas", []),
                talk_time_ratio=talk_time_ratio,
                question_quality_score=analysis_data.get("question_quality_score", 0),
                objection_handling_score=analysis_data.get("objection_handling_score", 0),
                next_actions=analysis_data.get("next_actions", [])
            )
            
        except Exception as e:
            logger.error(f"Error analyzing sales performance: {e}")
            return None
    
    async def _extract_competitive_intelligence(self, call_details: Dict) -> List[CompetitiveIntelligence]:
        """Extract competitive mentions and intelligence"""
        try:
            transcript = call_details.get("transcript", "")
            
            # Common competitors (update with actual Pay Ready competitors)
            competitors = ["stripe", "square", "paypal", "adyen", "braintree", "authorize.net"]
            
            competitive_intel = []
            
            for competitor in competitors:
                if competitor.lower() in transcript.lower():
                    # AI analysis for context
                    context_prompt = f"""
                    Analyze this mention of competitor "{competitor}" in our sales call:
                    
                    Transcript excerpt: {transcript[:3000]}...
                    
                    Provide analysis in JSON format:
                    {{
                        "context": "brief description of how competitor was mentioned",
                        "client_sentiment": "positive/negative/neutral towards competitor",
                        "our_position": "how we compare based on client comments",
                        "action_items": ["specific actions we should take"]
                    }}
                    """
                    
                    analysis_response = await self.llm.achat(context_prompt)
                    analysis_data = json.loads(analysis_response.message.content)
                    
                    competitive_intel.append(CompetitiveIntelligence(
                        call_id=call_details.get("id"),
                        competitor_mentioned=competitor,
                        context=analysis_data.get("context", ""),
                        client_sentiment=analysis_data.get("client_sentiment", "neutral"),
                        our_position=analysis_data.get("our_position", ""),
                        action_items=analysis_data.get("action_items", [])
                    ))
            
            return competitive_intel
            
        except Exception as e:
            logger.error(f"Error extracting competitive intelligence: {e}")
            return []
    
    async def _assess_client_health(self, call_details: Dict) -> Optional[ClientHealthSignal]:
        """Assess client health from call sentiment and engagement"""
        try:
            transcript = call_details.get("transcript", "")
            participants = call_details.get("participants", [])
            
            # Find client participants
            client_participants = [p for p in participants if not p.get("emailAddress", "").endswith("@payready.com")]
            
            if not client_participants or not transcript:
                return None
            
            client_name = client_participants[0].get("name", "Unknown Client")
            
            # AI health assessment
            health_prompt = f"""
            Assess client health from this call:
            
            Client: {client_name}
            Transcript: {transcript[:3000]}...
            
            Provide assessment in JSON format:
            {{
                "health_score": 0-100,
                "sentiment_trend": "improving/declining/stable",
                "risk_factors": ["factor1", "factor2"],
                "engagement_level": "high/medium/low",
                "renewal_likelihood": 0-100
            }}
            
            Consider:
            - Client enthusiasm and engagement
            - Pain points and concerns raised
            - Adoption and usage discussions
            - Future planning mentions
            - Overall satisfaction indicators
            """
            
            assessment_response = await self.llm.achat(health_prompt)
            assessment_data = json.loads(assessment_response.message.content)
            
            return ClientHealthSignal(
                client_name=client_name,
                health_score=assessment_data.get("health_score", 50),
                sentiment_trend=assessment_data.get("sentiment_trend", "stable"),
                risk_factors=assessment_data.get("risk_factors", []),
                engagement_level=assessment_data.get("engagement_level", "medium"),
                renewal_likelihood=assessment_data.get("renewal_likelihood", 50)
            )
            
        except Exception as e:
            logger.error(f"Error assessing client health: {e}")
            return None
    
    async def _calculate_talk_time_ratio(self, transcript: str, sales_rep: str) -> float:
        """Calculate sales rep talk time vs. client talk time"""
        # Simple implementation - count words by speaker
        # In production, use Gong's actual speaker timestamps
        rep_words = transcript.lower().count(sales_rep.lower().split()[0])
        total_words = len(transcript.split())
        
        return min(rep_words / total_words if total_words > 0 else 0.5, 1.0)
    
    async def _calculate_ceo_metrics(self, analysis_results: Dict) -> Dict[str, Any]:
        """Calculate key CEO metrics from analysis"""
        coaching_insights = analysis_results.get("sales_coaching_insights", [])
        competitive_intel = analysis_results.get("competitive_intelligence", [])
        client_health = analysis_results.get("client_health_signals", [])
        
        metrics = {
            "average_question_quality": sum(c.question_quality_score for c in coaching_insights) / len(coaching_insights) if coaching_insights else 0,
            "average_objection_handling": sum(c.objection_handling_score for c in coaching_insights) / len(coaching_insights) if coaching_insights else 0,
            "competitive_mentions_count": len(competitive_intel),
            "at_risk_clients": len([c for c in client_health if c.health_score < 60]),
            "high_value_prospects": len([c for c in client_health if c.renewal_likelihood > 80]),
            "average_client_health": sum(c.health_score for c in client_health) / len(client_health) if client_health else 0
        }
        
        return metrics
    
    async def _generate_executive_summary(self, analysis_results: Dict) -> str:
        """Generate executive summary for CEO"""
        summary_prompt = f"""
        Generate a concise executive summary for the CEO based on this sales analysis:
        
        Analysis Results: {json.dumps(analysis_results, default=str, indent=2)}
        
        Provide a 3-paragraph executive summary covering:
        1. Sales team performance highlights and areas for improvement
        2. Competitive landscape insights and threats/opportunities
        3. Client health overview and recommended actions
        
        Keep it strategic and actionable for CEO decision-making.
        """
        
        try:
            summary_response = await self.llm.achat(summary_prompt)
            return summary_response.message.content
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return "Executive summary generation failed - see detailed analysis above."


# CEO-focused analysis endpoint
async def analyze_for_ceo_dashboard(days_back: int = 7) -> Dict[str, Any]:
    """Main entry point for CEO business intelligence analysis"""
    analyzer = GongCEOAnalyzer()
    
    try:
        await analyzer.initialize()
        results = await analyzer.analyze_recent_calls_for_ceo(days_back)
        return results
    finally:
        await analyzer.close() 