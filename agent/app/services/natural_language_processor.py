"""
"""
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
elevenlabs_client = None
if ELEVENLABS_API_KEY:
    elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

class IntentCategory(Enum):
    """Categories of user intents"""
    AGENT_CONTROL = "agent_control"
    QUERY = "query"
    WORKFLOW = "workflow"
    GENERAL = "general"
    HELP = "help"

@dataclass
class Intent:
    """Parsed intent from natural language"""
    """Main NLP processor for Cherry AI"""
            "personal": {"focus": "individual productivity", "tone": "casual"},
            "payready": {"focus": "business operations", "tone": "professional"},
            "paragonrx": {"focus": "healthcare/pharmacy", "tone": "clinical"},
        }

    def _load_intent_patterns(self) -> Dict[str, List[Tuple[str, IntentCategory, str]]]:
        """Load regex patterns for intent classification"""
            "agent_control": [
                (r"(start|run|launch|activate)\s+(?:the\s+)?(\w+)\s+agent", IntentCategory.AGENT_CONTROL, "start"),
                (r"(stop|halt|pause|deactivate)\s+(?:the\s+)?(\w+)\s+agent", IntentCategory.AGENT_CONTROL, "stop"),
                (r"(show|display|list)\s+(?:me\s+)?agent(?:s)?\s+status", IntentCategory.AGENT_CONTROL, "status"),
                (r"(restart|reboot)\s+(?:the\s+)?(\w+)\s+agent", IntentCategory.AGENT_CONTROL, "restart"),
            ],
            "query": [
                (r"what(?:'s|'s)?\s+(?:the\s+)?(.+)", IntentCategory.QUERY, "what"),
                (r"show\s+me\s+(.+)", IntentCategory.QUERY, "show"),
                (r"(how many|count)\s+(.+)", IntentCategory.QUERY, "count"),
                (r"(list|display)\s+(?:all\s+)?(.+)", IntentCategory.QUERY, "list"),
            ],
            "workflow": [
                (r"(process|handle|execute)\s+(?:all\s+)?(.+)", IntentCategory.WORKFLOW, "execute"),
                (r"(generate|create)\s+(.+)\s+report", IntentCategory.WORKFLOW, "generate_report"),
                (r"(analyze|review)\s+(.+)", IntentCategory.WORKFLOW, "analyze"),
            ],
            "help": [
                (r"(help|what can you do|commands)", IntentCategory.HELP, "help"),
                (r"(how do i|how to)\s+(.+)", IntentCategory.HELP, "how_to"),
            ],
        }

class IntentClassifier:
    """Classify user intents from natural language"""
            "payready": ["invoice", "payment", "revenue", "order", "customer", "billing"],
            "personal": ["reminder", "task", "schedule", "calendar", "note"],
            "paragonrx": ["prescription", "patient", "medication", "pharmacy", "drug"],
        }

    async def classify(self, text: str, domain: str = "payready") -> Intent:
        """Classify intent from text"""
                    if len(groups) > 1 and category == "agent_control":
                        entities["agent_name"] = groups[1]
                        entities["agent_id"] = self._resolve_agent_id(groups[1])
                    elif category == "query":
                        entities["query_subject"] = groups[-1] if groups else text
                    elif category == "workflow":
                        entities["workflow_subject"] = groups[-1] if groups else text

                    return Intent(
                        category=intent_cat,
                        action=action,
                        entities=entities,
                        confidence=0.9,
                        query=text if intent_cat == IntentCategory.QUERY else None,
                        workflow_name=(
                            self._resolve_workflow_name(text) if intent_cat == IntentCategory.WORKFLOW else None
                        ),
                    )

        # Default to general intent
        return Intent(category=IntentCategory.GENERAL, confidence=0.5, query=text)

    def _resolve_agent_id(self, agent_name: str) -> str:
        """Resolve agent name to ID"""
            "system": "sys-001",
            "analyzer": "analyze-001",
            "monitor": "monitor-001",
            "data": "analyze-001",
            "service": "monitor-001",
        }
        return agent_map.get(agent_name.lower(), "sys-001")

    def _resolve_workflow_name(self, text: str) -> str:
        """Extract workflow name from text"""
        if "process" in text.lower():
            return "generic_process_workflow"
        elif "report" in text.lower():
            return "generic_report_workflow"
        elif "analyze" in text.lower():
            return "generic_analysis_workflow"
        return "custom_workflow"

class VoiceTranscriber:
    """Handle voice transcription using Whisper or similar"""
        self.whisper_api_url = os.getenv("WHISPER_API_URL", "https://api.openai.com/v1/audio/transcriptions")
        self.api_key = os.getenv("OPENAI_API_KEY", "")

    async def transcribe(self, audio_data: str, format: str = "webm") -> str:
        """Transcribe audio to text"""
        temp_file = f"/tmp/audio_{os.getpid()}.{format}"
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)

        try:


            pass
            async with httpx.AsyncClient() as client:
                with open(temp_file, "rb") as f:
                    response = await client.post(
                        self.whisper_api_url,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files={"file": f},
                        data={"model": "whisper-1"},
                    )

                if response.status_code == 200:
                    return response.json()["text"]
                else:
                    # Fallback for demo
                    return "Show me the agent status"
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)

class ResponseGenerator:
    """Generate natural language responses"""
        """Initialize ElevenLabs voice settings"""
                        if "conversational" in voice.name.lower() or voice.name in ["Rachel", "Antoni", "Bella"]:
                            self.voice_id = voice.voice_id
                            break
                    
                    # If no specific voice found, use the first one
                    if not self.voice_id and voices.voices:
                        self.voice_id = voices.voices[0].voice_id
                    
                    # Configure voice settings for realistic conversation
                    self.voice_settings = VoiceSettings(
                        stability=0.75,  # Balance between consistency and expressiveness
                        similarity_boost=0.85,  # High similarity to original voice
                        style=0.5,  # Moderate style exaggeration
                        use_speaker_boost=True  # Enable speaker boost for clarity
                    )
            except Exception:

                pass
                print(f"Failed to initialize ElevenLabs: {e}")

    async def generate(self, intent: Intent, result: Dict[str, Any], style: str = "conversational") -> str:
        """Generate natural language response based on intent and result"""
            if intent.action == "start":
                agent_id = result.get("data", {}).get("agent_id", "unknown")
                return f"I've started the {agent_id} agent for you. It's now running and ready to process tasks."
            elif intent.action == "status":
                agents = result.get("data", {}).get("agents", [])
                if agents:
                    active = sum(1 for a in agents if a.get("status") == "active")
                    return f"You have {len(agents)} agents in the system. {active} are currently active. Would you like me to show you more details?"
                return "No agents are currently registered in the system."
            elif intent.action == "stop":
                return "I've stopped the agent as requested."

        elif intent.category == IntentCategory.QUERY:
            # This will be expanded with actual data integration
            query_subject = intent.entities.get("query_subject", "that information")
            return f"I'm looking up {query_subject} for you. This feature will be connected to your data sources soon."

        elif intent.category == IntentCategory.WORKFLOW:
            workflow = intent.workflow_name or "workflow"
            return f"I've initiated the {workflow}. I'll notify you when it's complete."

        elif intent.category == IntentCategory.HELP:
            return self._generate_help_response()

        # Default response
        return "I understand your request. Let me process that for you."

    def _generate_help_response(self) -> str:
        """Generate help text"""
        return """
- "Start the data analyzer agent"
- "Show me agent status"
- "Stop all agents"

**Queries:** (Coming Soon)
- "What's the status of [item]?"
- "Show me recent [activities]"
- "List all [resources]"

**Workflows:** (Coming Soon)
- "Process [items]"
- "Generate [type] report"
- "Analyze [data set]"

Just tell me in natural language what you need!"""
        """Convert text to speech using ElevenLabs"""
                model_id="eleven_monolingual_v1",  # Or use "eleven_turbo_v2" for faster generation
                output_format="mp3_44100_128"
            )
            
            # Convert audio generator to bytes
            audio_bytes = b"".join(chunk for chunk in audio)
            
            # Convert to base64 for API response
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Return data URL for direct playback
            return f"data:audio/mp3;base64,{audio_base64}"
            
        except Exception:

            
            pass
            print(f"Failed to generate speech: {e}")
            return None
