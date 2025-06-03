# TODO: Consider adding connection pooling configuration
"""
"""
    """Types of queries for memory retrieval optimization."""
    FACTUAL = "factual"  # Prioritize exact matches
    CONCEPTUAL = "conceptual"  # Prioritize semantic matches
    CONVERSATIONAL = "conversational"  # Balance between exact and semantic
    UNKNOWN = "unknown"  # Default type

class QueryFeatures(BaseModel):
    """
    """
    """
    """
    """
    """
        """
        """
            "what is",
            "who is",
            "when did",
            "where is",
            "how many",
            "define",
            "explain",
            "list",
            "tell me about",
            "find",
            "show me",
            "give me",
            "name",
            "identify",
            "locate",
        ]

        self.conceptual_indicators = [
            "why",
            "how does",
            "what if",
            "compare",
            "contrast",
            "analyze",
            "evaluate",
            "similar to",
            "difference between",
            "relationship",
            "concept",
            "theory",
            "principle",
            "explain why",
            "reason for",
            "cause of",
            "effect of",
            "impact of",
            "significance of",
        ]

        self.conversational_indicators = [
            "can you",
            "could you",
            "would you",
            "i want",
            "i need",
            "help me",
            "please",
            "thanks",
            "thank you",
            "hi",
            "hello",
            "good morning",
            "good afternoon",
            "how are you",
            "nice to meet you",
        ]

        logger.info(f"QueryClassifier initialized (Vertex AI: {use_openai})")

    def _init_openai(self) -> None:
        """
        """
            project = self.openai_config.get("project", "cherry-ai-project")
            location = self.openai_config.get("location", "us-central1")

            # Initialize Vertex AI
            aiplatform.init(project=project, location=location)

            # Set up endpoint for text classification
            endpoint_name = self.openai_config.get("endpoint_name")
            if endpoint_name:
                self.openai_client = aiplatform.Endpoint(endpoint_name)
                logger.info(f"Vertex AI endpoint initialized: {endpoint_name}")
            else:
                # Use foundation model for classification
                self.openai_client = aiplatform.TextEmbeddingModel.from_pretrained("textembedding-gecko@latest")
                logger.info("Vertex AI foundation model initialized for query classification")

        except Exception:


            pass
            logger.warning("google-cloud-aiplatform package not installed. Falling back to rule-based classification.")
            self.use_openai = False
        except Exception:

            pass
            logger.error(f"Failed to initialize Vertex AI: {e}")
            self.use_openai = False

    async def classify(self, query: str) -> QueryClassificationResult:
        """
        """
                logger.error(f"Vertex AI classification failed: {e}")
                # Fall back to rule-based classification

        # Use rule-based classification
        result = self._classify_with_rules(query)
        result.processing_time_ms = (time.time() - start_time) * 1000
        return result

    async def _classify_with_openai(self, query: str) -> QueryClassificationResult:
        """
        """
            prompt = f"""
            - FACTUAL: Seeking specific information or facts (e.g., "What is X?", "Who invented Y?")
            - CONCEPTUAL: Seeking understanding of concepts, theories, or relationships (e.g., "Why does X happen?", "How does Y work?")
            - CONVERSATIONAL: General conversation, greetings, or requests (e.g., "Can you help me?", "Hello")

            Query: "{query}"

            Classification:
            """
            if hasattr(self.openai_client, "predict"):
                # Using custom endpoint
                response = await self.openai_client.predict_async(instances=[{"prompt": prompt}])

                # Parse response based on expected format
                # Note: This would need to be adjusted based on the actual model output format
                prediction = response[0]
                scores = {
                    QueryType.FACTUAL.value: prediction.get("scores", {}).get("FACTUAL", 0.0),
                    QueryType.CONCEPTUAL.value: prediction.get("scores", {}).get("CONCEPTUAL", 0.0),
                    QueryType.CONVERSATIONAL.value: prediction.get("scores", {}).get("CONVERSATIONAL", 0.0),
                    QueryType.UNKNOWN.value: 0.0,
                }

                # Determine the type with highest score
                query_type = max(scores.items(), key=lambda x: x[1])[0]
                confidence = scores[query_type]

            else:
                # Using foundation model for text classification
                # This is a simplified approach using embeddings similarity
                # In a real implementation, you would use a proper classification model

                # For now, fall back to rule-based classification
                return self._classify_with_rules(query)

            return QueryClassificationResult(
                query=query,
                query_type=QueryType(query_type),
                confidence=confidence,
                scores=scores,
                features=features,
            )

        except Exception:


            pass
            logger.error(f"Error in Vertex AI classification: {e}")
            # Fall back to rule-based classification
            return self._classify_with_rules(query)

    def _classify_with_rules(self, query: str) -> QueryClassificationResult:
        """
        """
        """
        """
        features = QueryFeatures(query_length=len(query), contains_question_mark="?" in query)

        # Count indicator terms
        features.factual_indicators = sum(1 for indicator in self.factual_indicators if indicator in query_lower)
        features.conceptual_indicators = sum(1 for indicator in self.conceptual_indicators if indicator in query_lower)
        features.conversational_indicators = sum(
            1 for indicator in self.conversational_indicators if indicator in query_lower
        )

        # Count question words
        question_words = ["what", "who", "when", "where", "why", "how"]
        features.question_words = sum(1 for word in question_words if word in query_lower.split())

        # Count greeting terms
        greeting_terms = [
            "hi",
            "hello",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
        ]
        features.greeting_terms = sum(1 for term in greeting_terms if term in query_lower)

        # Check for personal pronouns
        personal_pronouns = [
            "i",
            "me",
            "my",
            "mine",
            "you",
            "your",
            "yours",
            "we",
            "us",
            "our",
        ]
        features.has_personal_pronouns = any(pronoun in query_lower.split() for pronoun in personal_pronouns)

        # Simple check for technical terms (could be enhanced with a domain-specific vocabulary)
        technical_indicators = [
            "algorithm",
            "system",
            "database",
            "function",
            "api",
            "interface",
            "protocol",
            "architecture",
        ]
        features.has_technical_terms = any(term in query_lower for term in technical_indicators)

        return features
