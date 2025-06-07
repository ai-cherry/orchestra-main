# TODO: Consider adding connection pooling configuration
"""
Cherry AI - Database Models
This module contains Pydantic models for database entities.
"""

from typing import List, Dict, Any, Optional
from typing_extensions import Optional, Union
from uuid import uuid4, UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

""