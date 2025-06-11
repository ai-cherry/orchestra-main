#!/usr/bin/env python3
"""
"""
    """
    """
    parser = argparse.ArgumentParser(description="MCP Memory System")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()

    exit_code = asyncio.run(main_async(args.config))
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
