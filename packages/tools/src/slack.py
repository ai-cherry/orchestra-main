"""Tool for sending messages and reports to Slack channels."""

import os
from typing import Dict, Any, Optional, List, Union

from agno.tool import tool
from orchestra.tools.base import OrchestraTool

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    raise ImportError(
        "slack_sdk package is required. Install it with 'pip install slack-sdk'"
    )


def _get_slack_client() -> WebClient:
    """Create and return an authenticated Slack WebClient."""
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        raise ValueError("Missing SLACK_BOT_TOKEN in environment variables.")
    
    return WebClient(token=token)


@tool
def send_slack_message(
    channel: str,
    text: str,
    blocks: Optional[List[Dict[str, Any]]] = None,
    thread_ts: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a message to a Slack channel.
    
    Args:
        channel: The Slack channel ID or name to send the message to
        text: The message text content (fallback for notifications)
        blocks: Optional Slack Block Kit components for rich formatting
        thread_ts: Optional thread timestamp to reply in a thread
        
    Returns:
        Dictionary containing the Slack API response
    """
    client = _get_slack_client()
    
    try:
        # Prepare the message parameters
        msg_params = {
            "channel": channel,
            "text": text
        }
        
        # Add optional parameters if provided
        if blocks:
            msg_params["blocks"] = blocks
        if thread_ts:
            msg_params["thread_ts"] = thread_ts
        
        # Send the message
        response = client.chat_postMessage(**msg_params)
        
        # Format the response
        return {
            "ok": response.get("ok", False),
            "channel": response.get("channel"),
            "ts": response.get("ts"),
            "message": response.get("message", {})
        }
    
    except SlackApiError as e:
        return {
            "ok": False,
            "error": f"Slack API error: {e.response['error']}"
        }


@tool
def format_slack_message(
    title: str,
    sections: List[Dict[str, Any]],
    include_divider: bool = True
) -> List[Dict[str, Any]]:
    """
    Format a structured message using Slack Block Kit components.
    
    Args:
        title: Title for the message
        sections: List of section contents as dictionaries with required keys:
                 - text: Main text content (string)
                 - fields: Optional list of field dictionaries with text & optional title
        include_divider: Whether to include dividers between sections
        
    Returns:
        List of Slack Block Kit blocks ready to use with send_slack_message
    """
    blocks = []
    
    # Add header
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": title,
            "emoji": True
        }
    })
    
    # Add divider after header if required
    if include_divider:
        blocks.append({"type": "divider"})
    
    # Process each section
    for section in sections:
        section_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": section["text"]
            }
        }
        
        # Add fields if present
        if "fields" in section and section["fields"]:
            section_block["fields"] = [
                {
                    "type": "mrkdwn",
                    "text": f"*{field.get('title', '')}*\n{field['text']}"
                } if "title" in field else {
                    "type": "mrkdwn",
                    "text": field["text"]
                }
                for field in section["fields"]
            ]
        
        blocks.append(section_block)
        
        # Add divider after each section (except the last one)
        if include_divider and section != sections[-1]:
            blocks.append({"type": "divider"})
    
    return blocks


@tool
def send_data_visualization(
    channel: str, 
    title: str,
    report_text: str,
    image_url: str,
    alt_text: str = "Data Visualization"
) -> Dict[str, Any]:
    """
    Send a data visualization image to a Slack channel with contextual information.
    
    Args:
        channel: The Slack channel ID or name to send the message to
        title: Title for the visualization
        report_text: Contextual text describing the visualization
        image_url: Public URL to the image (must be accessible to Slack)
        alt_text: Alternative text for the image for accessibility
        
    Returns:
        Dictionary containing the Slack API response
    """
    client = _get_slack_client()
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": title,
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": report_text
            }
        },
        {
            "type": "image",
            "image_url": image_url,
            "alt_text": alt_text
        }
    ]
    
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=f"{title}: {report_text}",
            blocks=blocks
        )
        
        return {
            "ok": response.get("ok", False),
            "channel": response.get("channel"),
            "ts": response.get("ts"),
            "message": response.get("message", {})
        }
    
    except SlackApiError as e:
        return {
            "ok": False,
            "error": f"Slack API error: {e.response['error']}"
        }


class SlackMessenger(OrchestraTool):
    """
    Tool for sending messages and reports to Slack channels.
    Implements the OrchestraTool interface.
    """
    
    def __init__(self):
        """Initialize the SlackMessenger."""
        super().__init__(
            name="SlackMessenger",
            description="Send messages and reports to Slack channels",
        )
    
    def send_message(
        self, 
        channel: str, 
        text: str, 
        blocks: Optional[List[Dict[str, Any]]] = None, 
        thread_ts: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a Slack channel.
        
        Args:
            channel: The Slack channel ID or name to send the message to
            text: The message text content (fallback for notifications)
            blocks: Optional Slack Block Kit components for rich formatting
            thread_ts: Optional thread timestamp to reply in a thread
        
        Returns:
            Dictionary containing the Slack API response
        """
        return send_slack_message(channel, text, blocks, thread_ts)
    
    def format_message(
        self, 
        title: str, 
        sections: List[Dict[str, Any]], 
        include_divider: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Format a structured message using Slack Block Kit components.
        
        Args:
            title: Title for the message
            sections: List of section contents as dictionaries with required keys:
                    - text: Main text content (string)
                    - fields: Optional list of field dictionaries with text & optional title
            include_divider: Whether to include dividers between sections
            
        Returns:
            List of Slack Block Kit blocks ready to use with send_message
        """
        return format_slack_message(title, sections, include_divider)
    
    def send_data_visualization(
        self, 
        channel: str, 
        title: str, 
        report_text: str, 
        image_url: str, 
        alt_text: str = "Data Visualization"
    ) -> Dict[str, Any]:
        """
        Send a data visualization image to a Slack channel with contextual information.
        
        Args:
            channel: The Slack channel ID or name to send the message to
            title: Title for the visualization
            report_text: Contextual text describing the visualization
            image_url: Public URL to the image (must be accessible to Slack)
            alt_text: Alternative text for the image for accessibility
            
        Returns:
            Dictionary containing the Slack API response
        """
        return send_data_visualization(channel, title, report_text, image_url, alt_text)
