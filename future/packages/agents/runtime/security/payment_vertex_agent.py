"""
Secure Vertex AI Agent Manager for Payment Processing.

This module provides a restricted, purpose-specific implementation for
interacting with Vertex AI Agents for payment data analysis and processing.
It follows security best practices including:
1. No hardcoded credentials
2. Least privilege principles
3. Audit logging for all operations
4. Explicit scope limitation
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union

# Google Cloud imports
try:
    import vertexai
    from vertexai.preview import agent_builder
    from google.cloud import aiplatform
    from google.cloud import pubsub_v1
    from google.cloud import secretmanager
    from google.cloud import logging as cloud_logging
except ImportError:
    logging.warning(
        "Google Cloud libraries not found. Install with: "
        "pip install google-cloud-aiplatform google-cloud-pubsub google-cloud-secretmanager google-cloud-logging"
    )

# Configure logging
logger = logging.getLogger(__name__)


class PaymentVertexAgentManager:
    """
    Secure manager for interacting with Vertex AI Agents for payment processing.

    This class provides restricted methods for payment-specific analysis through
    Vertex AI Agents, with proper security controls and audit logging.
    """

    # List of allowed operations for this agent
    ALLOWED_OPERATIONS = [
        "payment_pattern_analysis",
        "fraud_detection",
        "transaction_categorization",
        "payment_trend_analysis",
    ]

    # API methods that are allowed to be used
    ALLOWED_API_METHODS = [
        "get_agent",
        "list_agents",
        "search_embeddings",
        "analyze_content",
    ]

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        agent_id: Optional[str] = None,
        pubsub_topic: Optional[str] = None,
        payment_data_project_id: Optional[str] = None,
    ):
        """
        Initialize the Payment Vertex Agent Manager with minimal, explicit permissions.

        Args:
            project_id: Google Cloud project ID (defaults to environment variable)
            location: Google Cloud region (defaults to environment variable)
            agent_id: Specific agent ID to use (if None, will use default)
            pubsub_topic: Pub/Sub topic for notifications (must be for payment events)
            payment_data_project_id: Separate project ID for payment data (if applicable)
        """
        # Verify and use environment variables if parameters not provided
        self.project_id = (
            project_id
            or os.environ.get("PAYMENT_VERTEX_PROJECT_ID")
            or os.environ.get("GOOGLE_CLOUD_PROJECT")
        )
        self.location = (
            location
            or os.environ.get("PAYMENT_VERTEX_LOCATION")
            or os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
        )
        self.agent_id = agent_id

        # Verify Pub/Sub topic is payment-specific
        if pubsub_topic:
            if not (pubsub_topic.startswith("payment-") or "payment" in pubsub_topic):
                raise ValueError(
                    "Pub/Sub topic must be payment-specific for security isolation"
                )
            self.pubsub_topic = pubsub_topic
        else:
            self.pubsub_topic = os.environ.get("PAYMENT_PUBSUB_TOPIC", "payment-events")

        # Use separate project for payment data if provided
        self.payment_data_project_id = payment_data_project_id or self.project_id

        # Validate configuration
        if not self.project_id:
            raise ValueError(
                "Project ID must be provided either directly or via environment variable"
            )

        # Configure audit logging
        self.setup_audit_logging()

        # Initialize Vertex AI with explicit project and location
        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.log_audit_event(
                "vertex_manager_initialized",
                {"project_id": self.project_id, "location": self.location},
            )
        except Exception as e:
            logger.error(f"Error initializing Vertex AI: {e}")
            raise

        # Initialize limited Pub/Sub publisher for payment events only
        try:
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(
                self.project_id, self.pubsub_topic
            )
        except Exception as e:
            logger.error(f"Error initializing Pub/Sub client: {e}")
            raise

    def setup_audit_logging(self):
        """
        Setup dedicated audit logging for payment operations.
        """
        try:
            # Create a client for cloud logging
            self.logging_client = cloud_logging.Client(project=self.project_id)

            # Setup a dedicated logger for payment operations
            self.audit_logger = self.logging_client.logger("payment-vertex-operations")

            logger.info("Audit logging configured for payment operations")
        except Exception as e:
            logger.error(f"Error setting up audit logging: {e}")
            # Continue without audit logging, but log the error
            self.audit_logger = None

    def log_audit_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Log an audit event with structured data.

        Args:
            event_type: Type of event being audited
            payload: Structured data about the event
        """
        if not self.audit_logger:
            logger.warning(f"Audit logging not available for event: {event_type}")
            return

        try:
            # Add standard metadata to all audit logs
            audit_data = {
                "event_type": event_type,
                "timestamp": time.time(),
                "project_id": self.project_id,
                "payment_data_project": self.payment_data_project_id,
                "user_id": os.environ.get("USER", "system"),
                "service_account": os.environ.get(
                    "GOOGLE_APPLICATION_CREDENTIALS", "default"
                ),
                **payload,
            }

            # Redact any potentially sensitive information
            if "content" in audit_data:
                audit_data["content"] = "[REDACTED]"
            if "embeddings" in audit_data:
                audit_data["embeddings"] = "[EMBEDDINGS REDACTED]"

            # Log the audit event
            self.audit_logger.log_struct(audit_data, severity="INFO")
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")

    def validate_operation(self, operation: str) -> bool:
        """
        Validate that an operation is permitted for payment processing.

        Args:
            operation: The operation to validate

        Returns:
            True if the operation is allowed, False otherwise
        """
        if operation not in self.ALLOWED_OPERATIONS:
            logger.warning(f"Attempted unauthorized operation: {operation}")
            self.log_audit_event(
                "unauthorized_operation_attempt",
                {"operation": operation, "allowed": False},
            )
            return False

        return True

    def get_payment_agent(
        self, agent_type: str = "payment_analysis"
    ) -> Optional[agent_builder.Agent]:
        """
        Get a payment-specific Vertex AI Agent.

        Args:
            agent_type: Type of payment agent to retrieve

        Returns:
            Vertex AI Agent instance or None if not found
        """
        if not agent_type.startswith("payment_"):
            agent_type = f"payment_{agent_type}"

        self.log_audit_event("get_payment_agent", {"agent_type": agent_type})

        try:
            # Try to get existing agent by ID if provided
            if self.agent_id:
                agent = agent_builder.Agent.get(agent_id=self.agent_id)
                logger.info(f"Retrieved agent by ID: {self.agent_id}")
                return agent

            # List agents and find payment-specific ones
            agents = agent_builder.Agent.list()

            # Filter to payment-specific agents only
            payment_agents = [
                agent
                for agent in agents
                if (
                    agent.display_name.startswith("payment-")
                    or "payment" in agent.display_name.lower()
                )
            ]

            # Find the requested agent type
            for agent in payment_agents:
                if agent_type.lower() in agent.display_name.lower():
                    self.agent_id = agent.id
                    logger.info(
                        f"Found payment agent: {agent.display_name} (ID: {agent.id})"
                    )
                    return agent

            logger.warning(f"No payment agent found for type: {agent_type}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving payment agent: {e}")
            self.log_audit_event(
                "agent_retrieval_error", {"agent_type": agent_type, "error": str(e)}
            )
            return None

    def analyze_payment_patterns(
        self, transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze payment patterns using Vertex AI.

        Args:
            transaction_data: Transaction data to analyze

        Returns:
            Dictionary with analysis results
        """
        if not self.validate_operation("payment_pattern_analysis"):
            return {"status": "error", "message": "Unauthorized operation"}

        logger.info("Analyzing payment patterns")
        self.log_audit_event(
            "payment_pattern_analysis_started",
            {
                "transaction_count": len(transaction_data.get("transactions", [])),
                "date_range": transaction_data.get("date_range", "unknown"),
            },
        )

        try:
            # Get the appropriate payment analysis agent
            agent = self.get_payment_agent("payment_pattern_analysis")
            if not agent:
                return {
                    "status": "error",
                    "message": "Payment pattern analysis agent not found",
                }

            # Prepare data for analysis (with PII redaction)
            prepared_data = self._prepare_transaction_data(transaction_data)

            # Execute the analysis
            response = agent.execute(prompt=json.dumps(prepared_data))

            # Parse and structure the response
            result = {
                "status": "success",
                "patterns_detected": self._extract_patterns(response),
                "analysis_timestamp": time.time(),
            }

            # Log success without including actual results
            self.log_audit_event(
                "payment_pattern_analysis_completed",
                {
                    "transaction_count": len(transaction_data.get("transactions", [])),
                    "patterns_count": len(result.get("patterns_detected", [])),
                    "agent_id": self.agent_id,
                },
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing payment patterns: {e}")
            self.log_audit_event("payment_pattern_analysis_error", {"error": str(e)})
            return {"status": "error", "message": str(e)}

    def detect_payment_fraud(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect potential fraud in payment transactions.

        Args:
            transaction_data: Transaction data to analyze

        Returns:
            Dictionary with fraud detection results
        """
        if not self.validate_operation("fraud_detection"):
            return {"status": "error", "message": "Unauthorized operation"}

        logger.info("Detecting payment fraud")
        self.log_audit_event(
            "fraud_detection_started",
            {
                "transaction_count": len(transaction_data.get("transactions", [])),
                "date_range": transaction_data.get("date_range", "unknown"),
            },
        )

        try:
            # Get the fraud detection agent
            agent = self.get_payment_agent("fraud_detection")
            if not agent:
                return {"status": "error", "message": "Fraud detection agent not found"}

            # Prepare data for analysis (with PII redaction)
            prepared_data = self._prepare_transaction_data(transaction_data)

            # Execute the analysis
            response = agent.execute(prompt=json.dumps(prepared_data))

            # Parse and structure the response
            result = {
                "status": "success",
                "fraud_indicators": self._extract_fraud_indicators(response),
                "analysis_timestamp": time.time(),
            }

            # Publish alert to Pub/Sub if high-risk indicators found
            if any(
                indicator.get("risk_level", "low") == "high"
                for indicator in result.get("fraud_indicators", [])
            ):
                self._publish_fraud_alert(result["fraud_indicators"])

            # Log success without including actual results
            self.log_audit_event(
                "fraud_detection_completed",
                {
                    "transaction_count": len(transaction_data.get("transactions", [])),
                    "indicators_count": len(result.get("fraud_indicators", [])),
                    "high_risk_count": len(
                        [
                            i
                            for i in result.get("fraud_indicators", [])
                            if i.get("risk_level") == "high"
                        ]
                    ),
                    "agent_id": self.agent_id,
                },
            )

            return result

        except Exception as e:
            logger.error(f"Error detecting payment fraud: {e}")
            self.log_audit_event("fraud_detection_error", {"error": str(e)})
            return {"status": "error", "message": str(e)}

    def categorize_transactions(
        self, transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Categorize payment transactions using Vertex AI.

        Args:
            transactions: List of transactions to categorize

        Returns:
            Dictionary with categorization results
        """
        if not self.validate_operation("transaction_categorization"):
            return {"status": "error", "message": "Unauthorized operation"}

        logger.info(f"Categorizing {len(transactions)} transactions")
        self.log_audit_event(
            "transaction_categorization_started",
            {"transaction_count": len(transactions)},
        )

        try:
            # Get the appropriate agent
            agent = self.get_payment_agent("transaction_categorization")
            if not agent:
                return {
                    "status": "error",
                    "message": "Transaction categorization agent not found",
                }

            # Process in batches to avoid overloading the API
            batch_size = 50
            categorized_transactions = []

            for i in range(0, len(transactions), batch_size):
                batch = transactions[i : i + batch_size]

                # Prepare data for analysis (with PII redaction)
                prepared_data = {
                    "transactions": self._redact_pii_from_transactions(batch),
                    "categorization_request": True,
                }

                # Execute the categorization
                response = agent.execute(prompt=json.dumps(prepared_data))

                # Parse and merge results
                batch_results = self._extract_categorized_transactions(response, batch)
                categorized_transactions.extend(batch_results)

                logger.info(
                    f"Processed batch {i//batch_size + 1} of {(len(transactions) + batch_size - 1)//batch_size}"
                )

            result = {
                "status": "success",
                "categorized_transactions": categorized_transactions,
                "categories_summary": self._summarize_categories(
                    categorized_transactions
                ),
                "analysis_timestamp": time.time(),
            }

            # Log success without including actual transactions
            self.log_audit_event(
                "transaction_categorization_completed",
                {
                    "transaction_count": len(transactions),
                    "categories_count": len(result.get("categories_summary", {})),
                    "agent_id": self.agent_id,
                },
            )

            return result

        except Exception as e:
            logger.error(f"Error categorizing transactions: {e}")
            self.log_audit_event("transaction_categorization_error", {"error": str(e)})
            return {"status": "error", "message": str(e)}

    def analyze_payment_trends(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze payment trends over time.

        Args:
            history_data: Historical payment data to analyze

        Returns:
            Dictionary with trend analysis results
        """
        if not self.validate_operation("payment_trend_analysis"):
            return {"status": "error", "message": "Unauthorized operation"}

        logger.info("Analyzing payment trends")
        self.log_audit_event(
            "payment_trend_analysis_started",
            {
                "data_points": len(history_data.get("data_points", [])),
                "date_range": history_data.get("date_range", "unknown"),
                "metrics": list(history_data.get("metrics", {}).keys()),
            },
        )

        try:
            # Get the trend analysis agent
            agent = self.get_payment_agent("trend_analysis")
            if not agent:
                return {
                    "status": "error",
                    "message": "Payment trend analysis agent not found",
                }

            # Prepare data for analysis (with PII redaction if needed)
            prepared_data = self._prepare_trend_data(history_data)

            # Execute the analysis
            response = agent.execute(prompt=json.dumps(prepared_data))

            # Parse and structure the response
            result = {
                "status": "success",
                "trends": self._extract_trends(response),
                "recommendations": self._extract_recommendations(response),
                "analysis_timestamp": time.time(),
            }

            # Log success without including actual results
            self.log_audit_event(
                "payment_trend_analysis_completed",
                {
                    "data_points": len(history_data.get("data_points", [])),
                    "trends_count": len(result.get("trends", [])),
                    "recommendations_count": len(result.get("recommendations", [])),
                    "agent_id": self.agent_id,
                },
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing payment trends: {e}")
            self.log_audit_event("payment_trend_analysis_error", {"error": str(e)})
            return {"status": "error", "message": str(e)}

    def search_payment_embeddings(
        self, query_embedding: List[float], index_name: str
    ) -> Dict[str, Any]:
        """
        Search for similar payment patterns using vector embeddings.

        Args:
            query_embedding: Vector embedding to search for
            index_name: Name of the vector index to search

        Returns:
            Dictionary with search results
        """
        logger.info(f"Searching payment embeddings in index: {index_name}")

        # Verify the index is payment-specific
        if not (index_name.startswith("payment-") or "payment" in index_name):
            logger.warning(
                f"Attempted to access non-payment vector index: {index_name}"
            )
            return {
                "status": "error",
                "message": "Access denied for non-payment vector index",
            }

        self.log_audit_event(
            "payment_embedding_search_started", {"index_name": index_name}
        )

        try:
            # Get the index endpoint
            index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
                index_endpoint_name=f"projects/{self.payment_data_project_id}/locations/{self.location}/indexEndpoints/{index_name}"
            )

            # Perform a search query
            search_results = index_endpoint.find_neighbors(
                queries=[query_embedding], num_neighbors=5
            )

            result_summary = []
            for idx, neighbors in enumerate(search_results):
                for neighbor in neighbors:
                    result_summary.append(
                        {"id": neighbor.id, "distance": neighbor.distance}
                    )

            logger.info(f"Found {len(result_summary)} similar payment patterns")

            # Log the search without embedding details
            self.log_audit_event(
                "payment_embedding_search_completed",
                {"index_name": index_name, "results_count": len(result_summary)},
            )

            return {
                "status": "success",
                "index": index_name,
                "search_results": result_summary,
            }
        except Exception as e:
            logger.error(f"Error searching payment embeddings: {e}")
            self.log_audit_event(
                "payment_embedding_search_error",
                {"index_name": index_name, "error": str(e)},
            )
            return {"status": "failed", "index": index_name, "error": str(e)}

    def _prepare_transaction_data(
        self, transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare transaction data for analysis, including PII redaction.

        Args:
            transaction_data: Raw transaction data

        Returns:
            Prepared data safe for analysis
        """
        # Create a copy to avoid modifying the original
        prepared_data = transaction_data.copy()

        # Redact PII from transactions
        if "transactions" in prepared_data:
            prepared_data["transactions"] = self._redact_pii_from_transactions(
                prepared_data["transactions"]
            )

        return prepared_data

    def _redact_pii_from_transactions(
        self, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Redact personally identifiable information from transactions.

        Args:
            transactions: List of transaction records

        Returns:
            Transactions with PII redacted
        """
        redacted_transactions = []

        # Define fields that may contain PII
        pii_fields = [
            "customer_name",
            "email",
            "phone",
            "address",
            "card_number",
            "account_number",
            "ssn",
            "tax_id",
            "personal_id",
        ]

        # Fields to partially redact
        partial_redact_fields = ["ip_address", "device_id", "payment_token"]

        for transaction in transactions:
            redacted_tx = transaction.copy()

            # Fully redact PII fields
            for field in pii_fields:
                if field in redacted_tx:
                    redacted_tx[field] = "[REDACTED]"

            # Partially redact some fields (show only part of the data)
            for field in partial_redact_fields:
                if field in redacted_tx and isinstance(redacted_tx[field], str):
                    value = redacted_tx[field]
                    # Keep first and last character, replace rest with *
                    if len(value) > 2:
                        redacted_tx[field] = (
                            value[0] + "*" * (len(value) - 2) + value[-1]
                        )

            # Special handling for card numbers (keep last 4 digits)
            if "card_number" in redacted_tx and isinstance(
                redacted_tx["card_number"], str
            ):
                value = redacted_tx["card_number"].replace(" ", "").replace("-", "")
                if len(value) >= 4:
                    redacted_tx["card_number"] = "****" + value[-4:]

            redacted_transactions.append(redacted_tx)

        return redacted_transactions

    def _prepare_trend_data(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare trend data for analysis.

        Args:
            history_data: Historical data for trend analysis

        Returns:
            Prepared data safe for analysis
        """
        # Create a copy to avoid modifying the original
        prepared_data = history_data.copy()

        # Redact any customer-specific identifiers if present
        if "customer_segments" in prepared_data:
            segments = prepared_data["customer_segments"]
            for segment in segments:
                if "customers" in segment:
                    # Remove specific customer identifiers, keep only counts
                    segment["customer_count"] = len(segment["customers"])
                    del segment["customers"]

        return prepared_data

    def _extract_patterns(self, response: Any) -> List[Dict[str, Any]]:
        """
        Extract payment patterns from agent response.

        Args:
            response: Agent response object

        Returns:
            List of identified patterns
        """
        try:
            # Parse the response content
            if hasattr(response, "text"):
                content = response.text
            else:
                content = str(response)

            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "patterns" in parsed:
                    return parsed["patterns"]
                elif isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # If not valid JSON, parse text response
                pass

            # Simple text parsing as fallback
            patterns = []
            current_pattern = None

            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("Pattern ") or line.startswith("- Pattern"):
                    if current_pattern:
                        patterns.append(current_pattern)
                    current_pattern = {"name": line, "description": ""}
                elif current_pattern and line:
                    current_pattern["description"] += line + " "

            if current_pattern:
                patterns.append(current_pattern)

            return patterns
        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return []

    def _extract_fraud_indicators(self, response: Any) -> List[Dict[str, Any]]:
        """
        Extract fraud indicators from agent response.

        Args:
            response: Agent response object

        Returns:
            List of fraud indicators with risk levels
        """
        try:
            # Parse the response content
            if hasattr(response, "text"):
                content = response.text
            else:
                content = str(response)

            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "indicators" in parsed:
                    return parsed["indicators"]
                elif isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # If not valid JSON, parse text response
                pass

            # Simple text parsing as fallback
            indicators = []
            risk_levels = ["low", "medium", "high"]

            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # Try to identify risk level
                risk_level = "medium"  # default
                for level in risk_levels:
                    if level.lower() in line.lower():
                        risk_level = level
                        break

                indicators.append({"description": line, "risk_level": risk_level})

            return indicators
        except Exception as e:
            logger.error(f"Error extracting fraud indicators: {e}")
            return []

    def _extract_categorized_transactions(
        self, response: Any, original_transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract categorized transactions from agent response.

        Args:
            response: Agent response object
            original_transactions: Original transaction data

        Returns:
            List of transactions with categories added
        """
        try:
            # Parse the response content
            if hasattr(response, "text"):
                content = response.text
            else:
                content = str(response)

            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "categorized_transactions" in parsed:
                    categories = parsed["categorized_transactions"]

                    # Match categories back to original transactions
                    result = []
                    for i, tx in enumerate(original_transactions):
                        if i < len(categories):
                            tx_copy = tx.copy()
                            tx_copy["category"] = categories[i].get(
                                "category", "Uncategorized"
                            )
                            tx_copy["subcategory"] = categories[i].get(
                                "subcategory", ""
                            )
                            result.append(tx_copy)
                        else:
                            # If we have more transactions than categories, use default
                            tx_copy = tx.copy()
                            tx_copy["category"] = "Uncategorized"
                            tx_copy["subcategory"] = ""
                            result.append(tx_copy)

                    return result
            except json.JSONDecodeError:
                # If not valid JSON, use a simpler approach
                pass

            # If we can't parse the response well, just add a basic category
            return [
                {**tx, "category": "Uncategorized", "subcategory": ""}
                for tx in original_transactions
            ]
        except Exception as e:
            logger.error(f"Error extracting categorized transactions: {e}")
            return original_transactions

    def _summarize_categories(
        self, categorized_transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a summary of transaction categories.

        Args:
            categorized_transactions: Transactions with categories

        Returns:
            Summary of categories with counts and amounts
        """
        summary = {}

        for tx in categorized_transactions:
            category = tx.get("category", "Uncategorized")

            if category not in summary:
                summary[category] = {"count": 0, "total_amount": 0, "subcategories": {}}

            summary[category]["count"] += 1
            summary[category]["total_amount"] += float(tx.get("amount", 0))

            subcategory = tx.get("subcategory", "")
            if subcategory:
                if subcategory not in summary[category]["subcategories"]:
                    summary[category]["subcategories"][subcategory] = {
                        "count": 0,
                        "total_amount": 0,
                    }

                summary[category]["subcategories"][subcategory]["count"] += 1
                summary[category]["subcategories"][subcategory][
                    "total_amount"
                ] += float(tx.get("amount", 0))

        return summary

    def _extract_trends(self, response: Any) -> List[Dict[str, Any]]:
        """
        Extract payment trends from agent response.

        Args:
            response: Agent response object

        Returns:
            List of identified trends
        """
        try:
            # Parse the response content
            if hasattr(response, "text"):
                content = response.text
            else:
                content = str(response)

            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "trends" in parsed:
                    return parsed["trends"]
                elif isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # If not valid JSON, parse text response
                pass

            # Simple text parsing as fallback
            trends = []
            current_trend = None

            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("Trend ") or line.startswith("- Trend"):
                    if current_trend:
                        trends.append(current_trend)
                    current_trend = {"name": line, "description": ""}
                elif current_trend and line:
                    current_trend["description"] += line + " "

            if current_trend:
                trends.append(current_trend)

            return trends
        except Exception as e:
            logger.error(f"Error extracting trends: {e}")
