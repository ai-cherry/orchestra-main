"""
"""
    """
    """
    agent_type = "phidata"

    def __init__(self, **kwargs):
        """
        """
        """
        """
            agent_class_name = self.agent_config.get("phidata_agent_class")
            if not agent_class_name:
                raise ValueError("phidata_agent_class not defined in agent config")

            # Dynamically import the agent class
            components = agent_class_name.split(".")
            module_name = ".".join(components[:-1])
            class_name = components[-1]
            module = __import__(module_name, fromlist=[class_name])
            agent_class = getattr(module, class_name)

            # Create an instance of the agent class, passing the agent config
            self.phidata_agent = agent_class(agent_config=self.agent_config)

            logger.info(f"Initialized Phidata agent: {agent_class_name}")

        except Exception:


            pass
            logger.error(f"Failed to initialize Phidata agent: {str(e)}")

    async def run(self, input_data: AgentInput) -> AgentOutput:
        """
        """
                "user_input": input_data.content,
                "recent_messages": recent_messages,
            }

            # 3. Call the Phidata agent's processing method
            logger.info(f"Processing input with Phidata agent: {self.name}")
            agent_response = await self.phidata_agent.process(context)

            # 4. Translate the results back to Orchestra's format
            return AgentOutput(
                response_id="phidata-response",  # Replace with actual response ID if available
                request_id=input_data.request_id,
                agent_id=self.id,
                content=str(agent_response),  # Ensure the content is a string
                status="completed",
            )

        except Exception:


            pass
            logger.error(f"Error running Phidata agent: {str(e)}")
            return AgentOutput(
                response_id="error-response",
                request_id=input_data.request_id,
                agent_id=self.id,
                content=f"Error executing Phidata agent: {str(e)}",
                status="error",
            )
