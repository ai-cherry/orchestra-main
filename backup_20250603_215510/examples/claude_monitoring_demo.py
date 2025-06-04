#!/usr/bin/env python3
"""
"""
setup_logging(level="INFO", json_format=False)
logger = get_logger(__name__)

async def demo_basic_monitoring():
    """Demonstrate basic monitoring functionality"""
    logger.info("Starting basic monitoring demo...")

    # Create a monitor with default settings
    monitor = ClaudeMonitor(
        log_responses=True,
        log_prompts=True,
        alert_threshold_cost=1.0,  # Alert at $1 for demo
        alert_threshold_errors=3,  # Alert after 3 errors
    )

    # Create a monitored LiteLLM client
    client = MonitoredLiteLLMClient(
        monitor=monitor,
        monitor_all_models=False,  # Only monitor Claude models
        api_key_anthropic=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Make some API calls
    messages = [
        LLMMessage(role="system", content="You are a helpful assistant."),
        LLMMessage(role="user", content="What is the capital of France?"),
    ]

    try:


        pass
        # Test with Claude 3 Sonnet
        logger.info("Making API call to Claude 3 Sonnet...")
        response = await client.chat_completion(
            messages=messages,
            model="claude-3-sonnet",
            max_tokens=100,
            session_id="demo_session_1",
            metadata={"demo": True, "test_type": "basic"},
        )
        logger.info(f"Response: {response.content}")

        # Test with Claude 3 Haiku (cheaper model)
        logger.info("Making API call to Claude 3 Haiku...")
        response = await client.chat_completion(
            messages=messages,
            model="claude-3-haiku",
            max_tokens=50,
            session_id="demo_session_1",
            metadata={"demo": True, "test_type": "basic"},
        )
        logger.info(f"Response: {response.content}")

    except Exception:


        pass
        logger.error(f"API call failed: {str(e)}")

    # Get monitoring summary
    summary = client.get_monitoring_summary()
    logger.info("\nMonitoring Summary:")
    logger.info(f"Total calls: {summary['total_calls']}")
    logger.info(f"Successful calls: {summary['successful_calls']}")
    logger.info(f"Failed calls: {summary['failed_calls']}")
    logger.info(f"Total cost: ${summary['total_cost_usd']:.4f}")
    logger.info(f"Average latency: {summary['average_latency_ms']:.0f}ms")
    logger.info(f"Calls by model: {summary['calls_by_model']}")
    logger.info(f"Cost by model: {summary['cost_by_model']}")

async def demo_error_handling():
    """Demonstrate error monitoring"""
    logger.info("\nStarting error handling demo...")

    monitor = ClaudeMonitor(alert_threshold_errors=2)
    client = MonitoredLiteLLMClient(monitor=monitor)

    # Simulate errors with invalid API key
    client.api_keys["anthropic"] = "invalid_key"

    messages = [LLMMessage(role="user", content="Test message")]

    # Try multiple calls to trigger error alert
    for i in range(3):
        try:

            pass
            await client.chat_completion(messages=messages, model="claude-3-sonnet", session_id="error_demo")
        except Exception:

            pass
            logger.error(f"Expected error {i+1}: {str(e)}")

    # Check error metrics
    summary = client.get_monitoring_summary()
    logger.info(f"\nError summary: {summary['errors_by_type']}")

async def demo_cost_tracking():
    """Demonstrate cost tracking across sessions"""
    logger.info("\nStarting cost tracking demo...")

    monitor = ClaudeMonitor(alert_threshold_cost=0.1)  # Low threshold for demo
    client = MonitoredLiteLLMClient(monitor=monitor, api_key_anthropic=os.getenv("ANTHROPIC_API_KEY"))

    # Simulate multiple users/sessions
    sessions = [
        {"session_id": "user_1_session", "user_id": "user_1"},
        {"session_id": "user_2_session", "user_id": "user_2"},
        {"session_id": "user_3_session", "user_id": "user_3"},
    ]

    for session in sessions:
        messages = [
            LLMMessage(
                role="user",
                content=f"Generate a 50-word story for {session['user_id']}",
            )
        ]

        try:


            pass
            await client.chat_completion(
                messages=messages,
                model="claude-3-haiku",
                max_tokens=100,
                **session,  # Use cheaper model
            )
            logger.info(f"Generated story for {session['user_id']}")
        except Exception:

            pass
            logger.error(f"Failed for {session['user_id']}: {str(e)}")

    # Get cost breakdown
    summary = monitor.get_metrics_summary()
    logger.info("\nCost tracking summary:")
    logger.info(f"Total cost: ${summary.total_cost_usd:.4f}")

    # Session costs
    logger.info("\nCosts by session:")
    for session_id, cost in monitor.session_costs.items():
        logger.info(f"  {session_id}: ${cost:.4f}")

async def demo_export_data():
    """Demonstrate data export functionality"""
    logger.info("\nStarting data export demo...")

    monitor = ClaudeMonitor()
    client = MonitoredLiteLLMClient(monitor=monitor, api_key_anthropic=os.getenv("ANTHROPIC_API_KEY"))

    # Make a few calls to generate data
    messages = [LLMMessage(role="user", content="Count from 1 to 5")]

    for i in range(3):
        try:

            pass
            await client.chat_completion(
                messages=messages,
                model="claude-3-haiku",
                max_tokens=20,
                user_id=f"test_user_{i}",
                metadata={"test_run": i},
            )
        except Exception:

            pass
            logger.error(f"Call {i} failed: {str(e)}")

    # Export data in different formats
    json_export = client.export_monitoring_data(format="json")
    logger.info(f"\nJSON export preview: {json_export[:200]}...")

    csv_export = client.export_monitoring_data(format="csv")
    logger.info(f"\nCSV export preview:\n{csv_export.split(chr(10))[:3]}")

async def demo_performance_monitoring():
    """Demonstrate performance monitoring"""
    logger.info("\nStarting performance monitoring demo...")

    monitor = ClaudeMonitor()
    client = MonitoredLiteLLMClient(monitor=monitor, api_key_anthropic=os.getenv("ANTHROPIC_API_KEY"))

    # Test different models for performance comparison
    models = ["claude-3-haiku", "claude-3-sonnet"]
    messages = [LLMMessage(role="user", content="What is 2+2?")]

    for model in models:
        logger.info(f"\nTesting {model}...")

        for i in range(3):
            try:

                pass
                await client.chat_completion(
                    messages=messages,
                    model=model,
                    max_tokens=10,
                    metadata={"test": "performance", "iteration": i},
                )
            except Exception:

                pass
                logger.error(f"Error with {model}: {str(e)}")

    # Analyze performance by model
    monitor.get_metrics_summary()
    logger.info("\nPerformance comparison:")

    for model in models:
        model_metrics = [m for m in monitor.metrics if m.model == model]
        if model_metrics:
            avg_latency = sum(m.latency_ms for m in model_metrics) / len(model_metrics)
            logger.info(f"{model}: avg latency = {avg_latency:.0f}ms")

async def main():
    """Run all demos"""
    logger.info("Claude API Monitoring System Demo\n" + "=" * 40)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning("No ANTHROPIC_API_KEY found. Some demos will fail.")
        logger.warning("Set your API key: export ANTHROPIC_API_KEY='your-key-here'")

    # Run demos
    await demo_basic_monitoring()
    await demo_error_handling()
    await demo_cost_tracking()
    await demo_export_data()
    await demo_performance_monitoring()

    logger.info("\nDemo completed!")

if __name__ == "__main__":
    asyncio.run(main())
