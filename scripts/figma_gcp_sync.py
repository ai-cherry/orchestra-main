#!/usr/bin/env python3
"""
Figma-GCP Sync Tool

This script automates the synchronization of Figma design variables with Google Cloud,
including:
- Exporting design variables from Figma
- Converting to multiple format outputs (CSS, JS, Android, iOS)
- Storing variables in GCP Secret Manager
- Validation using Vertex AI

Usage:
    python figma_gcp_sync.py --file-key YOUR_FILE_KEY [--output-dir ./styles] [--validate]
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

import requests

# Import Google Cloud libraries if available
try:
    from google.cloud import aiplatform, secretmanager

    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print(
        "Warning: Google Cloud libraries not available. Some features will be disabled."
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("figma_sync.log")],
)
logger = logging.getLogger("figma_gcp_sync")


class FigmaClient:
    """Client for interacting with the Figma API."""

    BASE_URL = "https://api.figma.com/v1"

    def __init__(self, token: str):
        self.token = token
        self.headers = {"X-Figma-Token": self.token}

    def get_file(self, file_key: str) -> Dict[str, Any]:
        """Get a Figma file."""
        url = f"{self.BASE_URL}/files/{file_key}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_file_variables(self, file_key: str) -> Dict[str, Any]:
        """Get variables from a Figma file."""
        url = f"{self.BASE_URL}/files/{file_key}/variables/local"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()


class StyleGenerator:
    """Generate style files in various formats from Figma variables."""

    def __init__(self, variables: Dict[str, Any]):
        self.variables = variables
        self.processed_variables = self._process_variables()

    def _process_variables(self) -> Dict[str, Any]:
        """Process raw Figma variables into a more usable format."""
        result = {"colors": {}, "typography": {}, "spacing": {}, "breakpoints": {}}

        # Extract collections and modes
        collections = {}
        for collection_id, collection in self.variables.get(
            "variableCollections", {}
        ).items():
            collections[collection_id] = {
                "name": collection.get("name", "Default"),
                "modes": {},
            }
            for mode_id, mode in collection.get("modes", {}).items():
                collections[collection_id]["modes"][mode_id] = mode.get(
                    "name", "Default"
                )

        # Extract variables
        for var_id, variable in self.variables.get("variables", {}).items():
            var_name = variable.get("name", "unknown")
            var_type = variable.get("resolvedType", "")
            collection_id = variable.get("variableCollectionId", "")

            # Skip if no collection found
            if collection_id not in collections:
                continue

            collection_name = collections[collection_id]["name"]

            # Process by type
            if var_type == "COLOR":
                for mode_id, mode_values in variable.get("valuesByMode", {}).items():
                    mode_name = collections[collection_id]["modes"].get(
                        mode_id, "Default"
                    )
                    key = (
                        f"{var_name}_{mode_name}"
                        if mode_name != "Default"
                        else var_name
                    )

                    # Convert RGBA to hex
                    if isinstance(mode_values, dict) and all(
                        k in mode_values for k in ["r", "g", "b"]
                    ):
                        r = int(mode_values["r"] * 255)
                        g = int(mode_values["g"] * 255)
                        b = int(mode_values["b"] * 255)
                        a = mode_values.get("a", 1)

                        if a == 1:
                            hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        else:
                            hex_color = f"#{r:02x}{g:02x}{b:02x}{int(a * 255):02x}"

                        result["colors"][key] = hex_color

            elif var_type == "STRING" and "typography" in collection_name.lower():
                for mode_id, mode_values in variable.get("valuesByMode", {}).items():
                    mode_name = collections[collection_id]["modes"].get(
                        mode_id, "Default"
                    )
                    key = (
                        f"{var_name}_{mode_name}"
                        if mode_name != "Default"
                        else var_name
                    )
                    result["typography"][key] = mode_values

            elif var_type == "FLOAT" and "spacing" in collection_name.lower():
                for mode_id, mode_values in variable.get("valuesByMode", {}).items():
                    mode_name = collections[collection_id]["modes"].get(
                        mode_id, "Default"
                    )
                    key = (
                        f"{var_name}_{mode_name}"
                        if mode_name != "Default"
                        else var_name
                    )
                    result["spacing"][key] = mode_values

            elif var_type == "FLOAT" and "breakpoint" in collection_name.lower():
                for mode_id, mode_values in variable.get("valuesByMode", {}).items():
                    mode_name = collections[collection_id]["modes"].get(
                        mode_id, "Default"
                    )
                    key = (
                        f"{var_name}_{mode_name}"
                        if mode_name != "Default"
                        else var_name
                    )
                    result["breakpoints"][key] = mode_values

        return result

    def generate_css(self, output_path: str) -> str:
        """Generate CSS variables file."""
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "variables.css"

        css = ":root {\n"

        # Add colors
        for name, value in self.processed_variables["colors"].items():
            css += f"  --color-{name}: {value};\n"

        # Add typography
        for name, value in self.processed_variables["typography"].items():
            css += f"  --font-{name}: {value};\n"

        # Add spacing
        for name, value in self.processed_variables["spacing"].items():
            css += f"  --spacing-{name}: {value}px;\n"

        # Add breakpoints
        for name, value in self.processed_variables["breakpoints"].items():
            css += f"  --breakpoint-{name}: {value}px;\n"

        css += "}\n"

        with open(output_file, "w") as f:
            f.write(css)

        logger.info(f"Generated CSS variables at {output_file}")
        return str(output_file)

    def generate_js(self, output_path: str) -> str:
        """Generate JavaScript variables file."""
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "variables.js"

        js = "// Generated from Figma variables\nexport const variables = {\n"

        # Add colors
        js += "  colors: {\n"
        for name, value in self.processed_variables["colors"].items():
            js += f"    {name}: '{value}',\n"
        js += "  },\n"

        # Add typography
        js += "  typography: {\n"
        for name, value in self.processed_variables["typography"].items():
            js += f"    {name}: '{value}',\n"
        js += "  },\n"

        # Add spacing
        js += "  spacing: {\n"
        for name, value in self.processed_variables["spacing"].items():
            js += f"    {name}: {value},\n"
        js += "  },\n"

        # Add breakpoints
        js += "  breakpoints: {\n"
        for name, value in self.processed_variables["breakpoints"].items():
            js += f"    {name}: {value},\n"
        js += "  }\n};\n"

        with open(output_file, "w") as f:
            f.write(js)

        logger.info(f"Generated JavaScript variables at {output_file}")
        return str(output_file)

    def generate_android_xml(self, output_path: str) -> str:
        """Generate Android XML colors and dimensions files."""
        output_dir = Path(output_path) / "android" / "src" / "main" / "res" / "values"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate colors.xml
        colors_file = output_dir / "colors.xml"
        colors_xml = '<?xml version="1.0" encoding="utf-8"?>\n'
        colors_xml += "<resources>\n"

        for name, value in self.processed_variables["colors"].items():
            # Convert to Android-compatible names (lowercase, underscores)
            android_name = name.lower().replace("-", "_").replace(" ", "_")
            colors_xml += f'    <color name="{android_name}">{value}</color>\n'

        colors_xml += "</resources>\n"

        with open(colors_file, "w") as f:
            f.write(colors_xml)

        # Generate dimens.xml
        dimens_file = output_dir / "dimens.xml"
        dimens_xml = '<?xml version="1.0" encoding="utf-8"?>\n'
        dimens_xml += "<resources>\n"

        # Add spacing
        for name, value in self.processed_variables["spacing"].items():
            android_name = f"spacing_{name.lower().replace('-', '_').replace(' ', '_')}"
            dimens_xml += f'    <dimen name="{android_name}">{value}dp</dimen>\n'

        dimens_xml += "</resources>\n"

        with open(dimens_file, "w") as f:
            f.write(dimens_xml)

        # Generate styles.xml
        styles_file = output_dir / "styles.xml"
        styles_xml = '<?xml version="1.0" encoding="utf-8"?>\n'
        styles_xml += "<resources>\n"
        styles_xml += '    <style name="OrchestraTheme" parent="Theme.AppCompat.Light.NoActionBar">\n'

        # Add typography styles
        for name, value in self.processed_variables["typography"].items():
            android_name = (
                f"typography_{name.lower().replace('-', '_').replace(' ', '_')}"
            )
            styles_xml += f'        <item name="{android_name}">{value}</item>\n'

        styles_xml += "    </style>\n"
        styles_xml += "</resources>\n"

        with open(styles_file, "w") as f:
            f.write(styles_xml)

        logger.info(f"Generated Android resources at {output_dir}")
        return str(output_dir)

    def generate_ios_swift(self, output_path: str) -> str:
        """Generate iOS Swift colors and design tokens file."""
        output_dir = Path(output_path) / "ios"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate Colors.swift
        colors_file = output_dir / "OrchestraColors.swift"
        swift = "import SwiftUI\n\n"
        swift += "extension Color {\n"
        swift += "    enum Orchestra {\n"

        for name, value in self.processed_variables["colors"].items():
            # Convert to Swift-compatible names (camelCase)
            swift_name = (
                name.replace("-", "_").replace("_", " ").title().replace(" ", "")
            )
            swift_name = swift_name[0].lower() + swift_name[1:]

            # Parse the hex color
            hex_color = value.lstrip("#")
            if len(hex_color) == 6:
                r = int(hex_color[0:2], 16) / 255.0
                g = int(hex_color[2:4], 16) / 255.0
                b = int(hex_color[4:6], 16) / 255.0
                swift += f"        static let {swift_name} = Color(red: {r}, green: {g}, blue: {b})\n"
            elif len(hex_color) == 8:
                r = int(hex_color[0:2], 16) / 255.0
                g = int(hex_color[2:4], 16) / 255.0
                b = int(hex_color[4:6], 16) / 255.0
                a = int(hex_color[6:8], 16) / 255.0
                swift += f"        static let {swift_name} = Color(red: {r}, green: {g}, blue: {b}, opacity: {a})\n"

        swift += "    }\n"
        swift += "}\n"

        with open(colors_file, "w") as f:
            f.write(swift)

        # Generate DesignTokens.swift
        tokens_file = output_dir / "OrchestraDesignTokens.swift"
        tokens = "import Foundation\n\n"
        tokens += "enum OrchestraDesignTokens {\n"

        # Typography
        tokens += "    enum Typography {\n"
        for name, value in self.processed_variables["typography"].items():
            swift_name = (
                name.replace("-", "_").replace("_", " ").title().replace(" ", "")
            )
            swift_name = swift_name[0].lower() + swift_name[1:]
            tokens += f'        static let {swift_name} = "{value}"\n'
        tokens += "    }\n\n"

        # Spacing
        tokens += "    enum Spacing {\n"
        for name, value in self.processed_variables["spacing"].items():
            swift_name = (
                name.replace("-", "_").replace("_", " ").title().replace(" ", "")
            )
            swift_name = swift_name[0].lower() + swift_name[1:]
            tokens += f"        static let {swift_name}: CGFloat = {value}\n"
        tokens += "    }\n\n"

        # Breakpoints
        tokens += "    enum Breakpoints {\n"
        for name, value in self.processed_variables["breakpoints"].items():
            swift_name = (
                name.replace("-", "_").replace("_", " ").title().replace(" ", "")
            )
            swift_name = swift_name[0].lower() + swift_name[1:]
            tokens += f"        static let {swift_name}: CGFloat = {value}\n"
        tokens += "    }\n"

        tokens += "}\n"

        with open(tokens_file, "w") as f:
            f.write(tokens)

        logger.info(f"Generated iOS Swift files at {output_dir}")
        return str(output_dir)

    def generate_terraform(self, output_path: str) -> str:
        """Generate Terraform variables file."""
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "figma_variables.tf"

        tf = "# Generated from Figma variables\n\n"

        # Colors
        tf += 'variable "figma_colors" {\n'
        tf += '  description = "Colors from Figma design system"\n'
        tf += "  type        = map(string)\n"
        tf += "  default     = {\n"
        for name, value in self.processed_variables["colors"].items():
            tf += f'    {name} = "{value}"\n'
        tf += "  }\n"
        tf += "}\n\n"

        # Typography
        tf += 'variable "figma_typography" {\n'
        tf += '  description = "Typography from Figma design system"\n'
        tf += "  type        = map(string)\n"
        tf += "  default     = {\n"
        for name, value in self.processed_variables["typography"].items():
            tf += f'    {name} = "{value}"\n'
        tf += "  }\n"
        tf += "}\n\n"

        # Spacing
        tf += 'variable "figma_spacing" {\n'
        tf += '  description = "Spacing values from Figma design system"\n'
        tf += "  type        = map(number)\n"
        tf += "  default     = {\n"
        for name, value in self.processed_variables["spacing"].items():
            tf += f"    {name} = {value}\n"
        tf += "  }\n"
        tf += "}\n\n"

        # Breakpoints
        tf += 'variable "figma_breakpoints" {\n'
        tf += '  description = "Breakpoints from Figma design system"\n'
        tf += "  type        = map(number)\n"
        tf += "  default     = {\n"
        for name, value in self.processed_variables["breakpoints"].items():
            tf += f"    {name} = {value}\n"
        tf += "  }\n"
        tf += "}\n"

        with open(output_file, "w") as f:
            f.write(tf)

        logger.info(f"Generated Terraform variables at {output_file}")
        return str(output_file)


class GCPManager:
    """Manage interactions with Google Cloud Platform."""

    def __init__(self, project_id: str):
        self.project_id = project_id

        if not GOOGLE_CLOUD_AVAILABLE:
            logger.warning(
                "Google Cloud libraries not available. GCP operations will be skipped."
            )
            return

        # Initialize clients
        self.secret_manager = secretmanager.SecretManagerServiceClient()

    def update_secret(self, secret_id: str, secret_data: str) -> bool:
        """Update a secret in Secret Manager."""
        if not GOOGLE_CLOUD_AVAILABLE:
            logger.warning(
                "Skipping secret update (Google Cloud libraries not available)"
            )
            return False

        try:
            # Create secret if it doesn't exist
            parent = f"projects/{self.project_id}"
            secret_path = f"{parent}/secrets/{secret_id}"

            try:
                self.secret_manager.get_secret(name=secret_path)
                logger.info(f"Secret {secret_id} already exists")
            except Exception:
                logger.info(f"Creating new secret {secret_id}")
                self.secret_manager.create_secret(
                    parent=parent,
                    secret_id=secret_id,
                    secret={"replication": {"automatic": {}}},
                )

            # Add new version
            secret_data_bytes = secret_data.encode("UTF-8")
            response = self.secret_manager.add_secret_version(
                parent=secret_path, payload={"data": secret_data_bytes}
            )

            logger.info(f"Updated secret {secret_id} with new version: {response.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update secret {secret_id}: {e}")
            return False

    def validate_with_vertex(self, design_data: Dict[str, Any]) -> bool:
        """Validate design system using Vertex AI."""
        if not GOOGLE_CLOUD_AVAILABLE:
            logger.warning("Skipping validation (Google Cloud libraries not available)")
            return False

        try:
            # Initialize Vertex AI
            aiplatform.init(project=self.project_id)

            # Use Gemini model for validation
            model = aiplatform.GenerativeModel("gemini-pro")

            # Create prompt for validation
            prompt = f"""
            Please validate the following design system variables and check for any issues:

            {json.dumps(design_data, indent=2)}

            Check for the following problems:
            1. Inconsistent naming patterns
            2. Accessibility issues with color contrast
            3. Redundant or duplicate values
            4. Missing essential variables

            Format your response as a JSON with these keys:
            - validationResult: "pass" or "fail"
            - issues: [] (array of issues found)
            - recommendations: [] (array of recommendations)
            """

            # Get response
            response = model.generate_content(prompt)

            try:
                result = json.loads(response.text)

                logger.info(
                    f"Validation result: {result.get('validationResult', 'unknown')}"
                )

                if result.get("issues"):
                    for issue in result.get("issues", []):
                        logger.warning(f"Validation issue: {issue}")

                if result.get("recommendations"):
                    for rec in result.get("recommendations", []):
                        logger.info(f"Recommendation: {rec}")

                return result.get("validationResult") == "pass"

            except json.JSONDecodeError:
                logger.warning("Could not parse validation response as JSON")
                logger.info(f"Raw response: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to validate with Vertex AI: {e}")
            return False


def sync_figma_variables(args):
    """Main function to sync Figma variables with GCP."""
    # Get Figma PAT
    figma_pat = args.token or os.getenv("FIGMA_PAT")
    if not figma_pat:
        logger.error("Figma Personal Access Token (PAT) not provided")
        return False

    # Initialize Figma client
    figma = FigmaClient(figma_pat)

    try:
        # Get variables from Figma
        logger.info(f"Fetching variables from Figma file: {args.file_key}")
        variables = figma.get_file_variables(args.file_key)

        # Create style generator
        generator = StyleGenerator(variables)

        # Generate style files
        output_dir = args.output_dir

        generator.generate_css(output_dir)
        generator.generate_js(output_dir)
        generator.generate_android_xml(output_dir)
        generator.generate_ios_swift(output_dir)
        tf_file = generator.generate_terraform(output_dir)

        logger.info("Generated all style files successfully")

        # Save full variables to JSON
        json_output = Path(output_dir) / "design_tokens.json"
        with open(json_output, "w") as f:
            json.dump(generator.processed_variables, f, indent=2)

        logger.info(f"Saved full design tokens to {json_output}")

        # Update GCP Secret Manager if enabled
        if args.update_secrets:
            project_id = args.project_id or os.getenv("GCP_PROJECT_ID")

            if not project_id:
                logger.error("GCP Project ID not provided")
                return False

            gcp = GCPManager(project_id)

            # Update design tokens secret
            gcp.update_secret(
                secret_id="figma-design-tokens",
                secret_data=json.dumps(generator.processed_variables),
            )

        # Validate with Vertex AI if enabled
        if args.validate:
            project_id = args.project_id or os.getenv("GCP_PROJECT_ID")

            if not project_id:
                logger.error("GCP Project ID not provided for validation")
                return False

            gcp = GCPManager(project_id)

            validation_result = gcp.validate_with_vertex(generator.processed_variables)
            logger.info(
                f"Validation result: {'Passed' if validation_result else 'Failed'}"
            )

        # Update Terraform if enabled
        if args.update_terraform:
            terraform_dir = args.terraform_dir or "infra/orchestra-terraform"

            # Copy the generated Terraform file
            terraform_dest = Path(terraform_dir) / "figma_variables.tf"
            terraform_dest.parent.mkdir(parents=True, exist_ok=True)

            import shutil

            shutil.copy(tf_file, terraform_dest)

            logger.info(f"Updated Terraform configuration at {terraform_dest}")

        return True

    except Exception as e:
        logger.error(f"Error syncing Figma variables: {e}", exc_info=True)
        return False


def main():
    """Script entry point."""
    parser = argparse.ArgumentParser(description="Sync Figma variables with GCP")

    parser.add_argument("--file-key", required=True, help="Figma file key (from URL)")

    parser.add_argument(
        "--token",
        help="Figma Personal Access Token (PAT) (can also use FIGMA_PAT env var)",
    )

    parser.add_argument(
        "--output-dir",
        default="./styles",
        help="Directory to output generated style files (default: ./styles)",
    )

    parser.add_argument(
        "--project-id", help="GCP Project ID (can also use GCP_PROJECT_ID env var)"
    )

    parser.add_argument(
        "--update-secrets",
        action="store_true",
        help="Update GCP Secret Manager with design tokens",
    )

    parser.add_argument(
        "--validate", action="store_true", help="Validate design tokens with Vertex AI"
    )

    parser.add_argument(
        "--update-terraform",
        action="store_true",
        help="Update Terraform configuration with design tokens",
    )

    parser.add_argument(
        "--terraform-dir",
        help="Directory containing Terraform configuration (default: infra/orchestra-terraform)",
    )

    args = parser.parse_args()

    # Run the sync process
    success = sync_figma_variables(args)

    if success:
        logger.info("Figma variables sync completed successfully")
        return 0
    else:
        logger.error("Figma variables sync failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
