#!/usr/bin/env python3
"""
"""
    """Print a colorized header for the CLI."""
    print(f"\n{Fore.CYAN}============================================={Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}  AI cherry_ai Mode Switcher{Style.RESET_ALL}")
    print(f"{Fore.CYAN}============================================={Style.RESET_ALL}\n")

def print_modes(manager: ModeManager, current_slug: Optional[str] = None):
    """
    """
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Available Modes:{Style.RESET_ALL}")

    for slug, mode in manager.modes.items():
        prefix = f"{Fore.YELLOW}➤ " if slug == current_slug else "  "

        # Color model names by type
        if "gemini" in mode.model.lower():
            model_color = Fore.MAGENTA
        elif "gpt" in mode.model.lower():
            model_color = Fore.BLUE
        elif "claude" in mode.model.lower():
            model_color = Fore.CYAN
        else:
            model_color = Fore.WHITE

        # Format write access
        write_access = f"{Fore.GREEN}✓" if mode.write_access else f"{Fore.RED}✗"

        # Print mode details
        print(f"{prefix}{Style.BRIGHT}{mode.name}{Style.RESET_ALL} ({Fore.WHITE}{slug}{Style.RESET_ALL})")
        print(f"   Model: {model_color}{mode.model}{Style.RESET_ALL}")
        print(f"   Write Access: {write_access}{Style.RESET_ALL}")
        print(f"   Description: {mode.description}")

        if mode.capabilities:
            print(f"   Capabilities: {', '.join(mode.capabilities)}")

        if mode.suggested_transitions:
            print(f"   Suggested Transitions: {', '.join(mode.suggested_transitions)}")

        print()

def print_workflows(manager: ModeManager, current_workflow: Optional[str] = None):
    """
    """
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Available Workflows:{Style.RESET_ALL}")

    for slug, workflow in manager.workflows.items():
        prefix = f"{Fore.YELLOW}➤ " if slug == current_workflow else "  "

        print(f"{prefix}{Style.BRIGHT}{workflow.name}{Style.RESET_ALL} ({slug})")
        print(f"   Description: {workflow.description}")
        print(f"   Steps: {len(workflow.steps)}")

        for i, step in enumerate(workflow.steps):
            status = f"{Fore.GREEN}✓ " if step.completed else ""
            print(f"     {i+1}. {status}[{step.mode}] {step.task}")

        print()

def print_current_state(manager: ModeManager):
    """
    """
        if "gemini" in manager.current_mode.model.lower():
            model_color = Fore.MAGENTA
        elif "gpt" in manager.current_mode.model.lower():
            model_color = Fore.BLUE
        elif "claude" in manager.current_mode.model.lower():
            model_color = Fore.CYAN
        else:
            model_color = Fore.WHITE

        print(
            f"\n{Fore.GREEN}{Style.BRIGHT}Current Mode:{Style.RESET_ALL} "
            f"{Style.BRIGHT}{manager.current_mode.name}{Style.RESET_ALL} "
            f"({Fore.WHITE}{manager.current_mode.slug}{Style.RESET_ALL})"
        )
        print(f"Model: {model_color}{manager.current_mode.model}{Style.RESET_ALL}")

        # If in a workflow, show current progress
        if manager.current_workflow and not manager.current_workflow.completed:
            workflow = manager.current_workflow
            current_step = workflow.current_step + 1
            total_steps = len(workflow.steps)

            print(
                f"\n{Fore.GREEN}{Style.BRIGHT}Current Workflow:{Style.RESET_ALL} "
                f"{Style.BRIGHT}{workflow.name}{Style.RESET_ALL}"
            )
            print(f"Progress: Step {current_step}/{total_steps}")

            if current_step <= total_steps:
                print(f"Current Task: {workflow.steps[workflow.current_step].task}")
    else:
        print(f"\n{Fore.YELLOW}No active mode selected{Style.RESET_ALL}")

def interactive_mode_switcher(manager: ModeManager):
    """
    """
        print(f"\n{Fore.CYAN}Choose an action:{Style.RESET_ALL}")
        print("  1. Switch mode")
        print("  2. Start workflow")
        print("  3. Advance workflow")
        print("  4. View all modes")
        print("  5. View all workflows")
        print("  6. Get suggested next steps")
        print("  7. Exit")

        choice = input(f"\n{Fore.YELLOW}Enter choice (1-7):{Style.RESET_ALL} ")

        if choice == "1":
            print_modes(manager, manager.current_mode.slug if manager.current_mode else None)
            mode_slug = input(f"\n{Fore.YELLOW}Enter mode slug to switch to:{Style.RESET_ALL} ")

            if mode_slug in manager.modes:
                success, message = manager.switch_mode(mode_slug)
                if success:
                    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Invalid mode slug{Style.RESET_ALL}")

        elif choice == "2":
            print_workflows(manager)
            workflow_slug = input(f"\n{Fore.YELLOW}Enter workflow slug to start:{Style.RESET_ALL} ")

            if workflow_slug in manager.workflows:
                success, message = manager.start_workflow(workflow_slug)
                if success:
                    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Invalid workflow slug{Style.RESET_ALL}")

        elif choice == "3":
            if not manager.current_workflow:
                print(f"{Fore.RED}✗ No active workflow{Style.RESET_ALL}")
            else:
                success, message = manager.advance_workflow()
                if success:
                    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

        elif choice == "4":
            print_modes(manager, manager.current_mode.slug if manager.current_mode else None)

        elif choice == "5":
            print_workflows(manager)

        elif choice == "6":
            suggestions = manager.suggest_next_modes()

            if suggestions:
                print(f"\n{Fore.GREEN}{Style.BRIGHT}Suggested next steps:{Style.RESET_ALL}")
                for i, suggestion in enumerate(suggestions):
                    mode = manager.modes.get(suggestion["slug"])

                    # Determine color for model name
                    if "gemini" in mode.model.lower():
                        model_color = Fore.MAGENTA
                    elif "gpt" in mode.model.lower():
                        model_color = Fore.BLUE
                    elif "claude" in mode.model.lower():
                        model_color = Fore.CYAN
                    else:
                        model_color = Fore.WHITE

                    print(
                        f"  {i+1}. Switch to {Style.BRIGHT}{suggestion['name']}{Style.RESET_ALL} "
                        f"({Fore.WHITE}{suggestion['slug']}{Style.RESET_ALL}) "
                        f"using {model_color}{mode.model}{Style.RESET_ALL}"
                    )
                    print(f"     Reason: {suggestion['reason']}")
            else:
                print(f"{Fore.YELLOW}No suggestions available{Style.RESET_ALL}")

        elif choice == "7":
            print(f"{Fore.GREEN}Exiting mode switcher.{Style.RESET_ALL}")
            # Save workflow state before exiting
            if manager.current_workflow:
                manager.save_workflow_state()
            break

        else:
            print(f"{Fore.RED}Invalid choice. Please enter a number from 1-7.{Style.RESET_ALL}")

        print("\n" + ("-" * 50))

def main():
    """Main entry point for the mode switcher CLI."""
        description="AI cherry_ai Mode Switcher - Manage 's operation modes and workflows"
    )

    parser.add_argument("--switch", "-s", help="Switch to the specified mode", metavar="MODE")

    parser.add_argument("--workflow", "-w", help="Start the specified workflow", metavar="WORKFLOW")

    parser.add_argument(
        "--advance",
        "-a",
        action="store_true",
        help="Advance to the next step in the current workflow",
    )

    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all available modes and workflows",
    )

    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")

    parser.add_argument(
        "--suggestions",
        "-g",
        action="store_true",
        help="Get suggested next steps based on current state",
    )

    parser.add_argument(
        "--check-file",
        "-c",
        help="Check if current mode can write to specified file",
        metavar="FILE",
    )

    args = parser.parse_args()

    # Get the mode manager
    manager = get_mode_manager()

    # Load previous workflow state if available
    manager.load_workflow_state()

    # Process commands
    if args.list:
        print_header()
        print_modes(manager, manager.current_mode.slug if manager.current_mode else None)
        print_workflows(manager)
        return

    if args.switch:
        if args.switch not in manager.modes:
            print(f"{Fore.RED}✗ Mode '{args.switch}' not found{Style.RESET_ALL}")
            return

        success, message = manager.switch_mode(args.switch)
        if success:
            print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
            print_current_state(manager)
        else:
            print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
        return

    if args.workflow:
        if args.workflow not in manager.workflows:
            print(f"{Fore.RED}✗ Workflow '{args.workflow}' not found{Style.RESET_ALL}")
            return

        success, message = manager.start_workflow(args.workflow)
        if success:
            print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
            print_current_state(manager)
        else:
            print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
        return

    if args.advance:
        if not manager.current_workflow:
            print(f"{Fore.RED}✗ No active workflow{Style.RESET_ALL}")
            return

        success, message = manager.advance_workflow()
        if success:
            print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
            print_current_state(manager)
        else:
            print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
        return

    if args.suggestions:
        print_header()
        print_current_state(manager)

        suggestions = manager.suggest_next_modes()
        if suggestions:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}Suggested next steps:{Style.RESET_ALL}")
            for i, suggestion in enumerate(suggestions):
                mode = manager.modes.get(suggestion["slug"])

                # Determine color for model name
                if "gemini" in mode.model.lower():
                    model_color = Fore.MAGENTA
                elif "gpt" in mode.model.lower():
                    model_color = Fore.BLUE
                elif "claude" in mode.model.lower():
                    model_color = Fore.CYAN
                else:
                    model_color = Fore.WHITE

                print(
                    f"  {i+1}. Switch to {Style.BRIGHT}{suggestion['name']}{Style.RESET_ALL} "
                    f"({Fore.WHITE}{suggestion['slug']}{Style.RESET_ALL}) "
                    f"using {model_color}{mode.model}{Style.RESET_ALL}"
                )
                print(f"     Reason: {suggestion['reason']}")
        else:
            print(f"{Fore.YELLOW}No suggestions available{Style.RESET_ALL}")
        return

    if args.check_file:
        success, message = manager.validate_file_access(args.check_file)
        print(f"{Fore.GREEN if success else Fore.RED}{message}{Style.RESET_ALL}")
        return

    # Default to interactive mode if no arguments or explicitly requested
    if args.interactive or len(sys.argv) == 1:
        interactive_mode_switcher(manager)
    else:
        # If no specific command was given, show current state
        print_header()
        print_current_state(manager)

if __name__ == "__main__":
    main()
