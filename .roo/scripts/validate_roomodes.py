#!/usr/bin/env python3
"""Validate .roomodes file for correct configuration."""

import yaml
import sys
from pathlib import Path


def validate_roomodes():
    """Validate the .roomodes file."""
    roomodes_file = Path(".roomodes")

    if not roomodes_file.exists():
        print("❌ .roomodes file not found!")
        return False

    try:
        with open(roomodes_file) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to parse .roomodes file: {e}")
        return False

    # Expected modes
    expected_modes = [
        "architect",
        "code",
        "debug",
        "orchestrator",
        "strategy",
        "research",
        "analytics",
        "implementation",
        "quality",
        "documentation",
    ]

    # Expected model assignments
    model_assignments = {
        "architect": "anthropic/claude-opus-4",
        "code": "google/gemini-2.5-flash-preview-05-20",
        "debug": "openai/gpt-4.1",
        "orchestrator": "anthropic/claude-sonnet-4",
        "strategy": "anthropic/claude-opus-4",
        "research": "anthropic/claude-sonnet-4",
        "analytics": "google/gemini-2.5-flash-preview-05-20",
        "implementation": "google/gemini-2.5-flash-preview-05-20",
        "quality": "openai/gpt-4.1",
        "documentation": "anthropic/claude-sonnet-4",
    }

    print("🔍 Validating .roomodes file...\n")

    # Check modes section
    if "modes" not in data:
        print("❌ 'modes' section not found in .roomodes!")
        return False

    modes = data["modes"]
    all_ok = True

    # Check each expected mode
    print("📋 Checking modes:")
    for mode in expected_modes:
        if mode in modes:
            mode_data = modes[mode]
            model = mode_data.get("model")
            expected_model = model_assignments[mode]

            if model == expected_model:
                print(f"  ✅ {mode}: {model}")
            else:
                print(f"  ❌ {mode}: Found '{model}', expected '{expected_model}'")
                all_ok = False
        else:
            print(f"  ❌ {mode}: Missing from modes section")
            all_ok = False

    # Check for unexpected modes
    unexpected_modes = set(modes.keys()) - set(expected_modes)
    if unexpected_modes:
        print(f"\n⚠️  Unexpected modes found: {', '.join(unexpected_modes)}")

    # Check customModes section
    print("\n📋 Checking customModes section:")
    if "customModes" in data:
        custom_modes = data["customModes"]
        custom_mode_slugs = {m.get("slug") for m in custom_modes if isinstance(m, dict)}

        for mode in expected_modes:
            if mode in custom_mode_slugs:
                print(f"  ✅ {mode} found in customModes")
            else:
                print(f"  ⚠️  {mode} not in customModes (may use default from modes section)")

    # Check other important settings
    print("\n📋 Other settings:")
    print(f"  Default mode: {data.get('defaultMode', 'Not set')}")
    print(f"  Boomerang default: {data.get('boomerang', {}).get('defaultMode', 'Not set')}")

    print("\n" + "=" * 50)
    if all_ok:
        print("✅ All 10 modes are properly configured with correct OpenRouter models!")
    else:
        print("❌ Some issues found. Please review the configuration above.")

    return all_ok


if __name__ == "__main__":
    success = validate_roomodes()
    sys.exit(0 if success else 1)
