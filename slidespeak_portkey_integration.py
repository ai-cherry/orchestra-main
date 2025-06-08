import requests
import json
import time
from typing import Dict, List, Optional

class SlideSpeak:
    """
    SlideSpeak API integration for Orchestra AI
    Handles presentation creation with persona-specific features
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.slidespeak.co/api/v1"
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
    
    def generate_presentation(self, 
                            plain_text: str,
                            length: int = 6,
                            template: str = "default",
                            language: str = "ORIGINAL",
                            tone: str = "professional",
                            fetch_images: bool = True,
                            verbosity: str = "default") -> Dict:
        """
        Generate a presentation from plain text
        
        Args:
            plain_text: Content to generate presentation about
            length: Number of slides (default: 6)
            template: Template to use (default, business, scientific, etc.)
            language: Language for presentation (ORIGINAL, French, etc.)
            tone: Tone of presentation (default, casual, professional, funny, educational, sales_pitch)
            fetch_images: Whether to include stock images
            verbosity: How verbose the text should be (default, short, long)
        
        Returns:
            Dict with task_id for tracking generation progress
        """
        
        endpoint = f"{self.base_url}/presentation/generate"
        
        payload = {
            "plain_text": plain_text,
            "length": length,
            "template": template,
            "language": language,
            "tone": tone,
            "fetch_images": fetch_images,
            "verbosity": verbosity
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
    
    def check_task_status(self, task_id: str) -> Dict:
        """
        Check the status of a presentation generation task
        
        Args:
            task_id: The task ID returned from generate_presentation
            
        Returns:
            Dict with task status and result URL when complete
        """
        
        endpoint = f"{self.base_url}/task_status/{task_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Status check failed: {str(e)}"}
    
    def wait_for_completion(self, task_id: str, max_wait: int = 300, poll_interval: int = 5) -> Dict:
        """
        Wait for presentation generation to complete
        
        Args:
            task_id: The task ID to monitor
            max_wait: Maximum time to wait in seconds (default: 5 minutes)
            poll_interval: How often to check status in seconds (default: 5 seconds)
            
        Returns:
            Dict with final result or timeout error
        """
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = self.check_task_status(task_id)
            
            if "error" in status:
                return status
            
            if status.get("task_status") == "SUCCESS":
                return status
            elif status.get("task_status") == "FAILED":
                return {"error": "Presentation generation failed"}
            
            time.sleep(poll_interval)
        
        return {"error": "Timeout waiting for presentation completion"}

class PortkeySlideSpeak:
    """
    Integration between Portkey and SlideSpeak for persona-specific presentations
    """
    
    def __init__(self, portkey_api_key: str, slidespeak_api_key: str):
        self.portkey_api_key = portkey_api_key
        self.slidespeak = SlideSpeak(slidespeak_api_key)
        
        # Portkey configuration for different personas
        self.portkey_configs = {
            "sophia": {
                "url": "https://api.portkey.ai/v1/chat/completions",
                "headers": {
                    "Content-Type": "application/json",
                    "x-portkey-api-key": portkey_api_key,
                    "x-portkey-config": "pc-sophia-business-123"  # Your Sophia config
                }
            },
            "karen": {
                "url": "https://api.portkey.ai/v1/chat/completions", 
                "headers": {
                    "Content-Type": "application/json",
                    "x-portkey-api-key": portkey_api_key,
                    "x-portkey-config": "pc-karen-clinical-456"  # Your Karen config
                }
            }
        }
    
    def enhance_content_with_ai(self, content: str, persona: str, presentation_type: str) -> str:
        """
        Use Portkey to enhance content with persona-specific AI
        
        Args:
            content: Raw content to enhance
            persona: "sophia" or "karen"
            presentation_type: Type of presentation to create
            
        Returns:
            Enhanced content optimized for presentation
        """
        
        if persona not in self.portkey_configs:
            return content
        
        # Persona-specific prompts
        prompts = {
            "sophia": f"""
            As Sophia, a business intelligence expert specializing in apartment technology, fintech, and debt recovery, 
            enhance this content for a {presentation_type} presentation:
            
            Focus on:
            - Business metrics and KPIs
            - Market analysis and trends
            - Competitive positioning
            - ROI and financial impact
            - Strategic recommendations
            
            Content: {content}
            
            Provide enhanced content that's professional, data-driven, and business-focused.
            """,
            
            "karen": f"""
            As Karen, a clinical research expert specializing in pharmaceutical research and medical studies,
            enhance this content for a {presentation_type} presentation:
            
            Focus on:
            - Scientific methodology
            - Clinical evidence and data
            - Regulatory compliance
            - Research findings and conclusions
            - Medical terminology and accuracy
            
            Content: {content}
            
            Provide enhanced content that's scientifically accurate, evidence-based, and professionally structured.
            """
        }
        
        config = self.portkey_configs[persona]
        
        payload = {
            "model": "claude-3-5-sonnet-20241022",  # Will be routed by Portkey
            "messages": [
                {"role": "user", "content": prompts[persona]}
            ],
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(config["url"], headers=config["headers"], json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"AI enhancement failed: {e}")
            return content
    
    def create_sophia_presentation(self, topic: str, search_data: Optional[Dict] = None) -> Dict:
        """
        Create a business presentation for Sophia persona
        
        Args:
            topic: Presentation topic
            search_data: Optional search results to include
            
        Returns:
            Dict with presentation generation result
        """
        
        # Combine topic with search data if available
        content = f"Business Analysis: {topic}"
        if search_data:
            content += f"\n\nMarket Data: {json.dumps(search_data, indent=2)}"
        
        # Enhance with Sophia's AI
        enhanced_content = self.enhance_content_with_ai(content, "sophia", "business")
        
        # Generate presentation with business template
        result = self.slidespeak.generate_presentation(
            plain_text=enhanced_content,
            length=8,  # Business presentations tend to be longer
            template="business",
            tone="professional",
            fetch_images=True,
            verbosity="default"
        )
        
        return result
    
    def create_karen_presentation(self, research_topic: str, search_data: Optional[Dict] = None) -> Dict:
        """
        Create a research presentation for Karen persona
        
        Args:
            research_topic: Research topic
            search_data: Optional research data to include
            
        Returns:
            Dict with presentation generation result
        """
        
        # Combine topic with research data if available
        content = f"Clinical Research: {research_topic}"
        if search_data:
            content += f"\n\nResearch Data: {json.dumps(search_data, indent=2)}"
        
        # Enhance with Karen's AI
        enhanced_content = self.enhance_content_with_ai(content, "karen", "research")
        
        # Generate presentation with scientific template
        result = self.slidespeak.generate_presentation(
            plain_text=enhanced_content,
            length=10,  # Research presentations tend to be detailed
            template="scientific",
            tone="educational",
            fetch_images=True,
            verbosity="long"
        )
        
        return result

# Test the integration
def test_slidespeak_integration():
    """
    Test SlideSpeak API integration
    Note: Requires actual API key to run
    """
    
    # You'll need to get a SlideSpeak API key
    SLIDESPEAK_API_KEY = "your-slidespeak-api-key"
    PORTKEY_API_KEY = "hPxFZGd8AN269n4bznDf2/Onbi8I"
    
    # Initialize the integration
    portkey_slidespeak = PortkeySlideSpeak(PORTKEY_API_KEY, SLIDESPEAK_API_KEY)
    
    # Test Sophia business presentation
    print("Testing Sophia business presentation...")
    sophia_result = portkey_slidespeak.create_sophia_presentation(
        "Apartment Technology Market Analysis 2025",
        {"market_size": "$2.5B", "growth_rate": "15%", "key_players": ["RentSpree", "AppFolio", "Buildium"]}
    )
    print(f"Sophia result: {sophia_result}")
    
    # Test Karen research presentation  
    print("Testing Karen research presentation...")
    karen_result = portkey_slidespeak.create_karen_presentation(
        "Clinical Trial Results for Novel Diabetes Treatment",
        {"participants": 500, "efficacy": "78%", "side_effects": "minimal"}
    )
    print(f"Karen result: {karen_result}")

if __name__ == "__main__":
    print("SlideSpeak + Portkey Integration Ready!")
    print("To test, add your SlideSpeak API key and run test_slidespeak_integration()")

