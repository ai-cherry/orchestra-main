"""
Slack parser implementation for data ingestion.

This module handles parsing of Slack export files including messages,
channels, users, and file attachments.
"""

import json
import logging
from typing import Dict, Any, List, AsyncIterator, Optional
from datetime import datetime
from pathlib import Path

from ..interfaces.parser import ParserInterface, ParsedData

logger = logging.getLogger(__name__)

class SlackParser(ParserInterface):
    """
    Parser for Slack export files.
    
    Handles various Slack export formats including:
    - Channel messages (JSON files)
    - Direct messages
    - User profiles
    - File attachments metadata
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Slack parser."""
        super().__init__(config)
        self.supported_formats = ["json", "zip"]
        self.content_types = ["message", "file", "user", "channel"]
        
    async def validate(self, file_content: bytes, filename: str) -> bool:
        """
        Validate if the file is a valid Slack export.
        
        Args:
            file_content: Raw file content
            filename: Name of the file
            
        Returns:
            True if valid Slack export format
        """
        try:
            # Check if it's a JSON file
            if filename.endswith('.json'):
                data = json.loads(file_content.decode('utf-8'))
                
                # Check for Slack message format
                if isinstance(data, list) and len(data) > 0:
                    # Check if first item has Slack message fields
                    first_item = data[0]
                    slack_fields = {'type', 'user', 'text', 'ts'}
                    if isinstance(first_item, dict) and any(field in first_item for field in slack_fields):
                        return True
                
                # Check for Slack metadata format
                elif isinstance(data, dict):
                    # Could be users.json, channels.json, etc.
                    if any(key in data for key in ['users', 'channels', 'members']):
                        return True
            
            return False
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.debug(f"File validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            return False
    
    async def parse(
        self, 
        file_content: bytes, 
        metadata: Dict[str, Any]
    ) -> AsyncIterator[ParsedData]:
        """
        Parse Slack export file and yield parsed data items.
        
        Args:
            file_content: Raw file content
            metadata: File metadata including filename, channel info, etc.
            
        Yields:
            ParsedData objects for each message or item
        """
        try:
            data = json.loads(file_content.decode('utf-8'))
            filename = metadata.get('filename', '')
            
            # Handle message files (array of messages)
            if isinstance(data, list):
                channel = metadata.get('channel') or self._extract_channel_from_filename(filename)
                
                for message in data:
                    if not isinstance(message, dict):
                        continue
                    
                    # Parse regular messages
                    if message.get('type') == 'message' and 'subtype' not in message:
                        parsed_data = ParsedData(
                            content_type='message',
                            source_id=message.get('ts', ''),
                            content=message.get('text', ''),
                            metadata={
                                'user': message.get('user'),
                                'channel': channel,
                                'timestamp': message.get('ts'),
                                'thread_ts': message.get('thread_ts'),
                                'reactions': message.get('reactions', []),
                                'reply_count': message.get('reply_count', 0),
                                'reply_users_count': message.get('reply_users_count', 0)
                            },
                            timestamp=self._parse_slack_timestamp(message.get('ts')),
                            file_import_id=metadata.get('file_import_id')
                        )
                        yield parsed_data
                    
                    # Parse file shares
                    elif message.get('subtype') == 'file_share':
                        for file_info in message.get('files', []):
                            parsed_data = ParsedData(
                                content_type='file',
                                source_id=file_info.get('id', ''),
                                content=file_info.get('title', '') + '\n' + file_info.get('preview', ''),
                                metadata={
                                    'user': message.get('user'),
                                    'channel': channel,
                                    'timestamp': message.get('ts'),
                                    'file_type': file_info.get('mimetype'),
                                    'file_size': file_info.get('size'),
                                    'file_name': file_info.get('name'),
                                    'file_url': file_info.get('url_private')
                                },
                                timestamp=self._parse_slack_timestamp(message.get('ts')),
                                file_import_id=metadata.get('file_import_id')
                            )
                            yield parsed_data
            
            # Handle metadata files (users.json, channels.json, etc.)
            elif isinstance(data, dict):
                # Parse users
                if 'users' in data:
                    for user in data['users']:
                        parsed_data = ParsedData(
                            content_type='user',
                            source_id=user.get('id', ''),
                            content=json.dumps({
                                'name': user.get('name'),
                                'real_name': user.get('real_name'),
                                'display_name': user.get('profile', {}).get('display_name')
                            }),
                            metadata={
                                'email': user.get('profile', {}).get('email'),
                                'title': user.get('profile', {}).get('title'),
                                'is_bot': user.get('is_bot', False),
                                'is_admin': user.get('is_admin', False),
                                'deleted': user.get('deleted', False)
                            },
                            file_import_id=metadata.get('file_import_id')
                        )
                        yield parsed_data
                
                # Parse channels
                elif 'channels' in data:
                    for channel in data['channels']:
                        parsed_data = ParsedData(
                            content_type='channel',
                            source_id=channel.get('id', ''),
                            content=json.dumps({
                                'name': channel.get('name'),
                                'topic': channel.get('topic', {}).get('value', ''),
                                'purpose': channel.get('purpose', {}).get('value', '')
                            }),
                            metadata={
                                'created': channel.get('created'),
                                'creator': channel.get('creator'),
                                'is_archived': channel.get('is_archived', False),
                                'is_private': channel.get('is_private', False),
                                'num_members': channel.get('num_members', 0)
                            },
                            timestamp=self._parse_slack_timestamp(str(channel.get('created'))),
                            file_import_id=metadata.get('file_import_id')
                        )
                        yield parsed_data
                        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing Slack data: {e}")
            raise
    
    async def extract_metadata(self, file_content: bytes) -> Dict[str, Any]:
        """
        Extract high-level metadata from the Slack export file.
        
        Args:
            file_content: Raw file content
            
        Returns:
            Dictionary containing file metadata
        """
        metadata = {
            'source_type': 'slack',
            'format': 'json'
        }
        
        try:
            data = json.loads(file_content.decode('utf-8'))
            
            if isinstance(data, list):
                # Message file
                metadata['type'] = 'messages'
                metadata['message_count'] = len(data)
                
                # Find date range
                if data:
                    timestamps = [msg.get('ts', '0') for msg in data if isinstance(msg, dict)]
                    if timestamps:
                        metadata['earliest_timestamp'] = min(timestamps)
                        metadata['latest_timestamp'] = max(timestamps)
                        metadata['date_range'] = {
                            'start': self._parse_slack_timestamp(metadata['earliest_timestamp']),
                            'end': self._parse_slack_timestamp(metadata['latest_timestamp'])
                        }
                
            elif isinstance(data, dict):
                # Metadata file
                if 'users' in data:
                    metadata['type'] = 'users'
                    metadata['user_count'] = len(data['users'])
                elif 'channels' in data:
                    metadata['type'] = 'channels'
                    metadata['channel_count'] = len(data['channels'])
                else:
                    metadata['type'] = 'metadata'
                    metadata['keys'] = list(data.keys())
                    
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            metadata['error'] = str(e)
            
        return metadata
    
    def _parse_slack_timestamp(self, ts: Optional[str]) -> Optional[datetime]:
        """
        Parse Slack timestamp to datetime.
        
        Slack timestamps are Unix timestamps with microseconds (e.g., "1234567890.123456")
        """
        if not ts:
            return None
            
        try:
            # Convert string timestamp to float
            timestamp = float(ts)
            return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError):
            return None
    
    def _extract_channel_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract channel name from filename.
        
        Slack exports often use format: channel_name/YYYY-MM-DD.json
        """
        path = Path(filename)
        if path.parent and path.parent.name:
            return path.parent.name
        return None