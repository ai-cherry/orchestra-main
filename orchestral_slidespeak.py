import asyncio
import json
from typing import Dict, List, Optional
from slidespeak_portkey_integration import PortkeySlideSpeak

class OrchestralSlideSpeak:
    """
    Orchestra AI integration with SlideSpeak for persona-specific presentation creation
    Integrates with existing search APIs and business data sources
    """
    
    def __init__(self, api_keys: Dict[str, str]):
        """
        Initialize with all API keys from user's comprehensive list
        
        Args:
            api_keys: Dictionary containing all API keys
        """
        self.api_keys = api_keys
        
        # Initialize SlideSpeak + Portkey integration
        self.slidespeak_portkey = PortkeySlideSpeak(
            portkey_api_key=api_keys["PORTKEY_API_KEY"],
            slidespeak_api_key=api_keys.get("SLIDESPEAK_API_KEY", "")  # User needs to add this
        )
        
        # Search API configurations using user's existing keys
        self.search_apis = {
            "brave": {
                "api_key": api_keys["BRAVE_API_KEY"],
                "endpoint": "https://api.search.brave.com/res/v1/web/search"
            },
            "perplexity": {
                "api_key": api_keys["PERPLEXITY_API_KEY"], 
                "endpoint": "https://api.perplexity.ai/chat/completions"
            },
            "exa": {
                "api_key": api_keys["EXA_API_KEY"],
                "endpoint": "https://api.exa.ai/search"
            },
            "tavily": {
                "api_key": api_keys["TAVILY_API_KEY"],
                "endpoint": "https://api.tavily.com/search"
            },
            "apollo": {
                "api_key": api_keys["APOLLO_IO_API_KEY"],
                "endpoint": "https://api.apollo.io/v1/mixed_people/search"
            }
        }
    
    def search_with_bias(self, query: str, persona: str, search_type: str) -> Dict:
        """
        Perform persona-specific search with bias injection
        
        Args:
            query: Base search query
            persona: "sophia" or "karen"
            search_type: Type of search to perform
            
        Returns:
            Aggregated search results from multiple sources
        """
        
        # Persona-specific bias keywords
        bias_keywords = {
            "sophia": {
                "market_research": "apartment technology proptech fintech market analysis",
                "competitive_analysis": "apartment software competitors market share",
                "industry_reports": "proptech industry report residential technology",
                "technology_trends": "apartment management software trends 2025",
                "investment_intelligence": "proptech funding venture capital investment"
            },
            "karen": {
                "clinical_trials": "clinical trials pharmaceutical research FDA",
                "drug_development": "drug development pharmaceutical pipeline FDA approval",
                "medical_literature": "medical research peer reviewed clinical studies",
                "regulatory_updates": "FDA regulatory guidance pharmaceutical compliance",
                "research_methodology": "clinical research methodology study design"
            }
        }
        
        # Get bias keywords for persona and search type
        bias = bias_keywords.get(persona, {}).get(search_type, "")
        enhanced_query = f"{query} {bias}".strip()
        
        # Perform searches across multiple APIs
        results = {}
        
        try:
            # Brave Search
            import requests
            brave_response = requests.get(
                self.search_apis["brave"]["endpoint"],
                headers={"X-Subscription-Token": self.search_apis["brave"]["api_key"]},
                params={"q": enhanced_query, "count": 10}
            )
            if brave_response.status_code == 200:
                results["brave"] = brave_response.json()
        except Exception as e:
            results["brave"] = {"error": str(e)}
        
        try:
            # Perplexity Search
            perplexity_response = requests.post(
                self.search_apis["perplexity"]["endpoint"],
                headers={
                    "Authorization": f"Bearer {self.search_apis['perplexity']['api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [{"role": "user", "content": f"Research and analyze: {enhanced_query}"}]
                }
            )
            if perplexity_response.status_code == 200:
                results["perplexity"] = perplexity_response.json()
        except Exception as e:
            results["perplexity"] = {"error": str(e)}
        
        # Add Apollo.io for business data (Sophia only)
        if persona == "sophia":
            try:
                apollo_response = requests.post(
                    self.search_apis["apollo"]["endpoint"],
                    headers={
                        "Cache-Control": "no-cache",
                        "Content-Type": "application/json",
                        "X-Api-Key": self.search_apis["apollo"]["api_key"]
                    },
                    json={
                        "q_keywords": query,
                        "page": 1,
                        "per_page": 10
                    }
                )
                if apollo_response.status_code == 200:
                    results["apollo"] = apollo_response.json()
            except Exception as e:
                results["apollo"] = {"error": str(e)}
        
        return results
    
    def create_sophia_business_presentation(self, topic: str, search_type: str = "market_research") -> Dict:
        """
        Create a comprehensive business presentation for Sophia
        
        Args:
            topic: Business topic to research and present
            search_type: Type of business research to perform
            
        Returns:
            Dict with presentation generation result and download info
        """
        
        print(f"🎨 Creating Sophia business presentation on: {topic}")
        
        # Step 1: Perform persona-specific search
        print("🔍 Performing business intelligence search...")
        search_results = self.search_with_bias(topic, "sophia", search_type)
        
        # Step 2: Create presentation with SlideSpeak
        print("📊 Generating presentation with SlideSpeak...")
        presentation_result = self.slidespeak_portkey.create_sophia_presentation(
            topic=topic,
            search_data=search_results
        )
        
        # Step 3: Monitor generation progress
        if "task_id" in presentation_result:
            print(f"⏳ Monitoring presentation generation (Task ID: {presentation_result['task_id']})...")
            final_result = self.slidespeak_portkey.slidespeak.wait_for_completion(
                presentation_result["task_id"]
            )
            
            if "task_result" in final_result and final_result["task_result"]:
                download_url = final_result["task_result"].get("url", "")
                print(f"✅ Sophia presentation ready! Download: {download_url}")
                
                return {
                    "status": "success",
                    "persona": "sophia",
                    "topic": topic,
                    "search_type": search_type,
                    "download_url": download_url,
                    "task_id": presentation_result["task_id"],
                    "search_results": search_results
                }
        
        return {
            "status": "error",
            "persona": "sophia", 
            "topic": topic,
            "result": presentation_result
        }
    
    def create_karen_research_presentation(self, research_topic: str, search_type: str = "clinical_trials") -> Dict:
        """
        Create a comprehensive research presentation for Karen
        
        Args:
            research_topic: Research topic to analyze and present
            search_type: Type of clinical research to perform
            
        Returns:
            Dict with presentation generation result and download info
        """
        
        print(f"🔬 Creating Karen research presentation on: {research_topic}")
        
        # Step 1: Perform persona-specific search
        print("🔍 Performing clinical research search...")
        search_results = self.search_with_bias(research_topic, "karen", search_type)
        
        # Step 2: Create presentation with SlideSpeak
        print("📋 Generating research presentation with SlideSpeak...")
        presentation_result = self.slidespeak_portkey.create_karen_presentation(
            research_topic=research_topic,
            search_data=search_results
        )
        
        # Step 3: Monitor generation progress
        if "task_id" in presentation_result:
            print(f"⏳ Monitoring presentation generation (Task ID: {presentation_result['task_id']})...")
            final_result = self.slidespeak_portkey.slidespeak.wait_for_completion(
                presentation_result["task_id"]
            )
            
            if "task_result" in final_result and final_result["task_result"]:
                download_url = final_result["task_result"].get("url", "")
                print(f"✅ Karen presentation ready! Download: {download_url}")
                
                return {
                    "status": "success",
                    "persona": "karen",
                    "topic": research_topic,
                    "search_type": search_type,
                    "download_url": download_url,
                    "task_id": presentation_result["task_id"],
                    "search_results": search_results
                }
        
        return {
            "status": "error",
            "persona": "karen",
            "topic": research_topic,
            "result": presentation_result
        }

# Chat interface integration
class SlideSpeak_ChatInterface:
    """
    Chat interface for SlideSpeak presentation creation
    Integrates with the admin website chat system
    """
    
    def __init__(self, orchestral_slidespeak: OrchestralSlideSpeak):
        self.orchestral = orchestral_slidespeak
        
        # Presentation type mappings for each persona
        self.sophia_presentation_types = {
            "market_research": "Market Research & Analysis",
            "competitive_analysis": "Competitive Analysis",
            "industry_reports": "Industry Report",
            "technology_trends": "Technology Trends",
            "investment_intelligence": "Investment Intelligence"
        }
        
        self.karen_presentation_types = {
            "clinical_trials": "Clinical Trial Analysis",
            "drug_development": "Drug Development Report", 
            "medical_literature": "Literature Review",
            "regulatory_updates": "Regulatory Analysis",
            "research_methodology": "Research Methodology"
        }
    
    def handle_presentation_request(self, message: str, persona: str) -> Dict:
        """
        Handle chat requests for presentation creation
        
        Args:
            message: User's chat message
            persona: Current active persona ("sophia" or "karen")
            
        Returns:
            Dict with response and presentation creation result
        """
        
        # Parse presentation request from message
        if "presentation" in message.lower() or "slides" in message.lower():
            
            if persona == "sophia":
                # Extract business topic and type
                topic = self.extract_topic_from_message(message)
                search_type = self.determine_sophia_search_type(message)
                
                response = f"🎨 **Sophia**: Creating a business presentation on '{topic}' with {search_type} focus..."
                
                # Create presentation
                result = self.orchestral.create_sophia_business_presentation(topic, search_type)
                
                if result["status"] == "success":
                    response += f"\n\n✅ **Presentation Ready!**\n📊 Download: {result['download_url']}\n🔍 Search Type: {search_type}\n📈 Includes business intelligence and market data"
                else:
                    response += f"\n\n❌ **Error**: Failed to create presentation. Please try again."
                
                return {
                    "response": response,
                    "result": result,
                    "persona": "sophia"
                }
            
            elif persona == "karen":
                # Extract research topic and type
                topic = self.extract_topic_from_message(message)
                search_type = self.determine_karen_search_type(message)
                
                response = f"🔬 **Karen**: Creating a research presentation on '{topic}' with {search_type} focus..."
                
                # Create presentation
                result = self.orchestral.create_karen_research_presentation(topic, search_type)
                
                if result["status"] == "success":
                    response += f"\n\n✅ **Presentation Ready!**\n📋 Download: {result['download_url']}\n🔍 Search Type: {search_type}\n📊 Includes clinical research and medical literature"
                else:
                    response += f"\n\n❌ **Error**: Failed to create presentation. Please try again."
                
                return {
                    "response": response,
                    "result": result,
                    "persona": "karen"
                }
        
        return {
            "response": f"I can help you create presentations! Just ask me to 'create a presentation about [topic]'",
            "result": None,
            "persona": persona
        }
    
    def extract_topic_from_message(self, message: str) -> str:
        """Extract the main topic from user's message"""
        # Simple extraction - can be enhanced with NLP
        words = message.lower().split()
        
        # Look for common patterns
        if "about" in words:
            about_index = words.index("about")
            topic_words = words[about_index + 1:]
        elif "on" in words:
            on_index = words.index("on")
            topic_words = words[on_index + 1:]
        else:
            # Take everything after "presentation" or "slides"
            if "presentation" in words:
                pres_index = words.index("presentation")
                topic_words = words[pres_index + 1:]
            elif "slides" in words:
                slides_index = words.index("slides")
                topic_words = words[slides_index + 1:]
            else:
                topic_words = words
        
        # Clean up and return
        topic = " ".join(topic_words).strip()
        return topic if topic else "General Topic"
    
    def determine_sophia_search_type(self, message: str) -> str:
        """Determine the type of business search based on message content"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["market", "analysis", "research"]):
            return "market_research"
        elif any(word in message_lower for word in ["competitor", "competitive", "competition"]):
            return "competitive_analysis"
        elif any(word in message_lower for word in ["industry", "report", "overview"]):
            return "industry_reports"
        elif any(word in message_lower for word in ["trend", "technology", "innovation"]):
            return "technology_trends"
        elif any(word in message_lower for word in ["investment", "funding", "venture"]):
            return "investment_intelligence"
        else:
            return "market_research"  # Default
    
    def determine_karen_search_type(self, message: str) -> str:
        """Determine the type of clinical search based on message content"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["trial", "clinical", "study"]):
            return "clinical_trials"
        elif any(word in message_lower for word in ["drug", "development", "pharmaceutical"]):
            return "drug_development"
        elif any(word in message_lower for word in ["literature", "review", "research"]):
            return "medical_literature"
        elif any(word in message_lower for word in ["regulatory", "fda", "compliance"]):
            return "regulatory_updates"
        elif any(word in message_lower for word in ["methodology", "method", "protocol"]):
            return "research_methodology"
        else:
            return "clinical_trials"  # Default

# Example usage and testing
def test_orchestral_slidespeak():
    """
    Test the complete SlideSpeak integration with user's APIs
    """
    
    # User's API keys (from the pasted content)
    api_keys = {
        "PORTKEY_API_KEY": "hPxFZGd8AN269n4bznDf2/Onbi8I",
        "BRAVE_API_KEY": "BSApz0194z7SG6DplmVozl7ttFOi0Eo",
        "PERPLEXITY_API_KEY": "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",
        "EXA_API_KEY": "fdf07f38-34ad-44a9-ab6f-74ca2ca90fd4",
        "TAVILY_API_KEY": "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",
        "APOLLO_IO_API_KEY": "n-I9eHckqmnURzE1Zk82xg",
        "SLIDESPEAK_API_KEY": "your-slidespeak-api-key"  # User needs to add this
    }
    
    # Initialize the system
    orchestral = OrchestralSlideSpeak(api_keys)
    chat_interface = SlideSpeak_ChatInterface(orchestral)
    
    # Test Sophia presentation
    print("Testing Sophia business presentation...")
    sophia_response = chat_interface.handle_presentation_request(
        "Create a presentation about apartment technology market trends",
        "sophia"
    )
    print(f"Sophia Response: {sophia_response['response']}")
    
    # Test Karen presentation
    print("\nTesting Karen research presentation...")
    karen_response = chat_interface.handle_presentation_request(
        "Create a presentation about clinical trials for diabetes treatment",
        "karen"
    )
    print(f"Karen Response: {karen_response['response']}")

if __name__ == "__main__":
    print("🚀 Orchestra AI SlideSpeak Integration Ready!")
    print("📊 Sophia: Business presentations with market intelligence")
    print("🔬 Karen: Research presentations with clinical data")
    print("💬 Chat interface ready for presentation requests")

