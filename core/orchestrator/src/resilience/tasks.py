"""
"""
    """
    """
        """
        """
            f"Task Queue Manager initialized for project={project_id}, " f"location={location_id}, queue={queue_name}"
        )

    def schedule_retry(
        self,
        agent_id: str,
        operation_data: Dict[str, Any],
        retry_attempt: int = 0,
        delay_seconds: Optional[int] = None,
    ) -> str:
        """
        """
                "agent_id": agent_id,
                "operation": operation_data,
                "retry_attempt": retry_attempt + 1,
                "scheduled_time": scheduled_time.isoformat(),
            }

            payload = json.dumps(task_data).encode("utf-8")

            # Create task
            task = {
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": f"{self.service_url}/tasks/retry-agent",
                    "headers": {"Content-Type": "application/json"},
                    "body": payload,
                },
                "schedule_time": timestamp,
            }

            # Add service account if provided
            if self.service_account_email:
                task["http_request"]["oidc_token"] = {
                    "service_account_email": self.service_account_email,
                    "audience": self.service_url,
                }

            # Create the task
            response = self.client.create_task(request={"parent": self.queue_path, "task": task})

            task_name = response.name
            logger.info(
                f"Scheduled retry attempt #{retry_attempt + 1} for agent '{agent_id}' "
                f"with {delay_seconds}s delay. Task name: {task_name}"
            )

            return task_name

        except Exception:


            pass
            logger.error(f"Failed to schedule retry for agent '{agent_id}': {str(e)}")
            return None

    def cancel_retry_tasks(self, agent_id: str) -> int:
        """
        """
                    not hasattr(task, "http_request")
                    or not hasattr(task.http_request, "body")
                    or not task.http_request.body
                ):
                    continue

                # Decode task body
                try:

                    pass
                    body_str = task.http_request.body.decode("utf-8")
                    body = json.loads(body_str)

                    # Check if task belongs to this agent
                    if body.get("agent_id") == agent_id:
                        # Cancel task
                        self.client.delete_task(name=task.name)
                        cancelled_count += 1
                        logger.info(f"Cancelled retry task for agent '{agent_id}': {task.name}")
                except Exception:

                    pass
                    # Skip if we can't decode the body
                    continue

            return cancelled_count

        except Exception:


            pass
            logger.error(f"Failed to cancel retry tasks for agent '{agent_id}': {str(e)}")
            return 0

class VertexAiFallbackHandler:
    """
    """
        service_account: str = "vertex-agent@cherry-ai-project.iam.gserviceaccount.com",
    ):
        """
        """
        logger.info(f"Vertex AI Fallback Handler initialized with service account {service_account}")

    @property
    def client(self):
        """
        """
                logger.info("Initialized Vertex AI client for fallback operations")
            except Exception:

                pass
                logger.error(f"Failed to initialize Vertex AI client: {str(e)}")
                # We don't raise an exception here - will be handled when the client is used

        return self._client

    async def process(self, user_input: str) -> str:
        """
        """
                raise RuntimeError("Vertex AI client not initialized")

            # Log the fallback activation
            logger.info(f"Processing user input using Vertex AI fallback: '{user_input[:50]}...'")

            # Use the client to process the input
            # Depending on your VertexAgent implementation, you might need to adjust this
            result = await self.client.process(user_input)

            # Create incident report
            from core.orchestrator.src.resilience.monitoring import get_monitoring_client

            try:


                pass
                monitoring_client = get_monitoring_client()
                monitoring_client.create_incident_report(
                    agent_id="phidata",
                    incident_data={
                        "type": "fallback_activation",
                        "input": (user_input[:100] + "..." if len(user_input) > 100 else user_input),
                        "resolution": "processed_by_openai",
                    },
                )
            except Exception:

                pass
                logger.warning(f"Failed to create incident report: {str(log_err)}")

            return result

        except Exception:


            pass
            logger.error(f"Vertex AI fallback processing failed: {str(e)}")
            # Return a graceful error message if processing fails
            return (
                "I'm having trouble processing your request at the moment. "
                "Our systems are experiencing some issues, but the team has been notified. "
                "Please try again later or contact support if this persists."
            )

# Global instances
_task_queue_manager = None
_task_queue_lock = threading.Lock()

_fallback_handler = None
_fallback_handler_lock = threading.Lock()

def get_task_queue_manager() -> TaskQueueManager:
    """
    """
                "VULTR_PROJECT_ID",
                getattr(settings, "VULTR_PROJECT_ID", "cherry-ai-project"),
            )

            location_id = os.environ.get(
                "TASK_QUEUE_LOCATION",
                getattr(settings, "TASK_QUEUE_LOCATION", "us-west4"),
            )

            queue_name = os.environ.get(
                "TASK_QUEUE_NAME",
                getattr(settings, "TASK_QUEUE_NAME", "agent-retry-queue"),
            )

            # Get service URL - in Cloud Run this is injected as environment variable
            service_url = os.environ.get("SERVICE_URL", getattr(settings, "SERVICE_URL", "http://localhost:8000"))

            # Service account for authentication
            service_account = os.environ.get(
                "TASK_QUEUE_SERVICE_ACCOUNT",
                getattr(
                    settings,
                    "TASK_QUEUE_SERVICE_ACCOUNT",
                    "vertex-agent@cherry-ai-project.iam.gserviceaccount.com",
                ),
            )

            _task_queue_manager = TaskQueueManager(
                project_id=project_id,
                location_id=location_id,
                queue_name=queue_name,
                service_url=service_url,
                service_account_email=service_account,
            )

            logger.info(f"Created global Task Queue Manager for project {project_id}")

        return _task_queue_manager

def get_fallback_handler() -> VertexAiFallbackHandler:
    """
    """
                "OPENAI_FALLBACK_SERVICE_ACCOUNT",
                getattr(
                    settings,
                    "OPENAI_FALLBACK_SERVICE_ACCOUNT",
                    "vertex-agent@cherry-ai-project.iam.gserviceaccount.com",
                ),
            )

            _fallback_handler = VertexAiFallbackHandler(service_account=service_account)

            logger.info(f"Created global Vertex AI Fallback Handler with service account {service_account}")

        return _fallback_handler
