"""
"""
    """
    """
    markdown = f"## {title}\n\n" if title else ""

    # Format each key-value pair
    for key, value in data.items():
        # Format key as heading
        key_display = key.replace("_", " ").title()

        # Handle different value types
        if isinstance(value, dict):
            # Nested dictionary
            markdown += f"### {key_display}\n\n"
            for sub_key, sub_value in value.items():
                sub_key_display = sub_key.replace("_", " ").title()
                if isinstance(sub_value, (dict, list)):
                    markdown += f"**{sub_key_display}**: \n```json\n{json.dumps(sub_value, indent=2)}\n```\n\n"
                else:
                    markdown += f"**{sub_key_display}**: {sub_value}\n\n"
        elif isinstance(value, list):
            # List of items
            markdown += f"### {key_display}\n\n"

            # Check if list contains dictionaries
            if value and isinstance(value[0], dict):
                # Create a table if all dicts have common keys
                if all(set(value[0].keys()) == set(item.keys()) for item in value):
                    # Table header
                    headers = list(value[0].keys())
                    markdown += "| " + " | ".join(h.replace("_", " ").title() for h in headers) + " |\n"
                    markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"

                    # Table rows
                    for item in value:
                        row_values = []
                        for header in headers:
                            cell_value = item.get(header, "")
                            # Ensure cell value is string and doesn't break table format
                            cell_str = str(cell_value).replace("\n", "<br>")
                            row_values.append(cell_str)
                        markdown += "| " + " | ".join(row_values) + " |\n"
                    markdown += "\n"
                else:
                    # Format as numbered list of items
                    for i, item in enumerate(value):
                        markdown += f"{i+1}. "
                        if isinstance(item, dict):
                            markdown += "\n```json\n" + json.dumps(item, indent=2) + "\n```\n"
                        else:
                            markdown += f"{item}\n"
                    markdown += "\n"
            else:
                # Simple list
                for item in value:
                    markdown += f"- {item}\n"
                markdown += "\n"
        else:
            # Simple key-value
            markdown += f"**{key_display}**: {value}\n\n"

    return markdown

def format_movie_script(data: Dict[str, Any]) -> str:
    """
    """
    markdown = f"# {data.get('title', 'Movie Script')}\n\n"

    # Add metadata if available
    if "genre" in data:
        markdown += f"**Genre**: {data['genre']}\n\n"
    if "logline" in data:
        markdown += f"**Logline**: {data['logline']}\n\n"

    # Add scenes
    if "scenes" in data and isinstance(data["scenes"], list):
        for i, scene in enumerate(data["scenes"]):
            scene_num = i + 1
            markdown += f"## Scene {scene_num}: {scene.get('description', '')}\n\n"

            # Format location/setting
            if "setting" in scene:
                markdown += f"**Setting**: {scene['setting']}\n\n"

            # Format script content in a code block for better readability
            if "script_content" in scene:
                markdown += "```\n" + scene["script_content"] + "\n```\n\n"

    return markdown

def format_salesforce_results(data: Dict[str, Any]) -> str:
    """
    """
    markdown = "# Salesforce Results\n\n"

    # Add query information if available
    if "query" in data:
        markdown += f"**Query**: `{data['query']}`\n\n"

    # Add total count if available
    if "totalSize" in data:
        markdown += f"**Total Results**: {data['totalSize']}\n\n"

    # Format records as a table if they exist
    if "records" in data and isinstance(data["records"], list) and data["records"]:
        records = data["records"]

        # Extract fields from the first record (assuming all records have same structure)
        if records and isinstance(records[0], dict):
            # Filter out metadata fields that start with attributes
            fields = [k for k in records[0].keys() if not k.startswith("attributes")]

            # Create table header
            markdown += "| " + " | ".join(f.replace("_", " ").title() for f in fields) + " |\n"
            markdown += "| " + " | ".join(["---"] * len(fields)) + " |\n"

            # Create table rows
            for record in records:
                row_values = []
                for field in fields:
                    value = record.get(field, "")
                    # Format value and ensure it doesn't break table layout
                    if isinstance(value, dict):
                        value_str = json.dumps(value)
                    else:
                        value_str = str(value)
                    # Replace newlines to maintain table format
                    value_str = value_str.replace("\n", "<br>")
                    row_values.append(value_str)
                markdown += "| " + " | ".join(row_values) + " |\n"

            markdown += "\n"

    return markdown

def format_analysis_results(data: Dict[str, Any]) -> str:
    """
    """
    markdown = f"# {data.get('title', 'Analysis Results')}\n\n"

    # Add summary if available
    if "summary" in data:
        markdown += f"## Summary\n\n{data['summary']}\n\n"

    # Add key findings
    if "findings" in data and isinstance(data["findings"], list):
        markdown += "## Key Findings\n\n"
        for i, finding in enumerate(data["findings"]):
            if isinstance(finding, dict) and "title" in finding:
                markdown += f"### {i+1}. {finding['title']}\n\n"
                if "description" in finding:
                    markdown += f"{finding['description']}\n\n"
            else:
                markdown += f"{i+1}. {finding}\n\n"

    # Add recommendations
    if "recommendations" in data and isinstance(data["recommendations"], list):
        markdown += "## Recommendations\n\n"
        for i, rec in enumerate(data["recommendations"]):
            if isinstance(rec, dict) and "title" in rec:
                markdown += f"### {i+1}. {rec['title']}\n\n"
                if "description" in rec:
                    markdown += f"{rec['description']}\n\n"
            else:
                markdown += f"{i+1}. {rec}\n\n"

    # Add additional data sections
    for key, value in data.items():
        if key not in ("title", "summary", "findings", "recommendations"):
            section_title = key.replace("_", " ").title()
            markdown += f"## {section_title}\n\n"

            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for sub_key, sub_value in item.items():
                            sub_key_display = sub_key.replace("_", " ").title()
                            markdown += f"**{sub_key_display}**: {sub_value}\n\n"
                    else:
                        markdown += f"- {item}\n"
                markdown += "\n"
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    sub_key_display = sub_key.replace("_", " ").title()
                    markdown += f"**{sub_key_display}**: {sub_value}\n\n"
            else:
                markdown += f"{value}\n\n"

    return markdown

def format_structured_output_as_markdown(data: Any, output_type: Optional[str] = None) -> str:
    """
    """
    if hasattr(data, "dict") and callable(data.dict):
        data = data.dict()

    # Handle case where data is already a string
    if isinstance(data, str):
        return data

    # Format based on output_type hint if provided
    if output_type:
        if output_type == "movie_script":
            return format_movie_script(data)
        elif output_type == "salesforce":
            return format_salesforce_results(data)
        elif output_type == "analysis":
            return format_analysis_results(data)

    # Try to infer type from data structure
    if isinstance(data, dict):
        # Check for movie script
        if "title" in data and "scenes" in data and isinstance(data["scenes"], list):
            return format_movie_script(data)
        # Check for Salesforce results
        elif "records" in data and "totalSize" in data:
            return format_salesforce_results(data)
        # Check for analysis results
        elif any(k in data for k in ["findings", "recommendations", "analysis"]):
            return format_analysis_results(data)
        # Default dictionary formatter
        else:
            return format_dictionary_as_markdown(data)

    # Fallback to JSON formatting for unknown structures
    if isinstance(data, (dict, list)):
        return f"```json\n{json.dumps(data, indent=2, default=str)}\n```"

    # Return string representation for other types
    return str(data)
