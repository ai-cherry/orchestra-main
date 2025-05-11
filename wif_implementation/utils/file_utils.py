"""
File utilities for WIF implementation.

This module provides utilities for efficient file operations,
including streaming file processing and memory-efficient file comparison.
"""

import hashlib
import io
import logging
import os
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional, Set, Tuple, Union, Any, BinaryIO, TextIO, Iterator

logger = logging.getLogger(__name__)


def read_file_in_chunks(
    file_path: Union[str, Path], 
    chunk_size: int = 8192,
    binary_mode: bool = False,
    encoding: str = "utf-8",
) -> Generator[Union[str, bytes], None, None]:
    """
    Read a file in chunks to avoid loading the entire file into memory.
    
    Args:
        file_path: Path to the file to read
        chunk_size: Size of each chunk in bytes
        binary_mode: Whether to read the file in binary mode
        encoding: Encoding to use when reading the file in text mode
        
    Yields:
        Chunks of the file content
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
        UnicodeDecodeError: If the file cannot be decoded with the specified encoding
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")
    
    mode = "rb" if binary_mode else "r"
    kwargs = {} if binary_mode else {"encoding": encoding}
    
    with open(file_path, mode, **kwargs) as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def process_file_by_chunks(
    file_path: Union[str, Path],
    processor: Callable[[Union[str, bytes]], Any],
    chunk_size: int = 8192,
    binary_mode: bool = False,
    encoding: str = "utf-8",
) -> bool:
    """
    Process a file in chunks using a processor function.
    
    Args:
        file_path: Path to the file to process
        processor: Function to process each chunk
        chunk_size: Size of each chunk in bytes
        binary_mode: Whether to read the file in binary mode
        encoding: Encoding to use when reading the file in text mode
        
    Returns:
        True if the file was processed successfully, False otherwise
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
    """
    try:
        for chunk in read_file_in_chunks(file_path, chunk_size, binary_mode, encoding):
            processor(chunk)
        return True
    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"Error accessing file {file_path}: {str(e)}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"Error decoding file {file_path}: {str(e)}")
        if not binary_mode:
            logger.info(f"Trying to process file {file_path} in binary mode")
            return process_file_by_chunks(file_path, processor, chunk_size, True)
        raise
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return False


def calculate_file_hash(
    file_path: Union[str, Path], 
    hash_algorithm: str = "sha256",
    chunk_size: int = 8192,
) -> str:
    """
    Calculate the hash of a file.
    
    Args:
        file_path: Path to the file
        hash_algorithm: Hash algorithm to use (md5, sha1, sha256, etc.)
        chunk_size: Size of each chunk in bytes
        
    Returns:
        The hash of the file
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
        ValueError: If the hash algorithm is not supported
    """
    try:
        hasher = hashlib.new(hash_algorithm)
    except ValueError:
        logger.error(f"Unsupported hash algorithm: {hash_algorithm}")
        raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")
    
    def update_hash(chunk: bytes) -> None:
        hasher.update(chunk)
    
    process_file_by_chunks(file_path, update_hash, chunk_size, True)
    
    return hasher.hexdigest()


def compare_files(
    file_path1: Union[str, Path],
    file_path2: Union[str, Path],
    chunk_size: int = 8192,
) -> bool:
    """
    Compare two files efficiently without loading them entirely into memory.
    
    Args:
        file_path1: Path to the first file
        file_path2: Path to the second file
        chunk_size: Size of each chunk in bytes
        
    Returns:
        True if the files are identical, False otherwise
        
    Raises:
        FileNotFoundError: If either file does not exist
        PermissionError: If either file cannot be read
    """
    file_path1 = Path(file_path1)
    file_path2 = Path(file_path2)
    
    # Quick check: if the files have different sizes, they are different
    if file_path1.stat().st_size != file_path2.stat().st_size:
        return False
    
    # Compare the files chunk by chunk
    with open(file_path1, "rb") as f1, open(file_path2, "rb") as f2:
        while True:
            chunk1 = f1.read(chunk_size)
            chunk2 = f2.read(chunk_size)
            
            if chunk1 != chunk2:
                return False
            
            if not chunk1:  # End of both files
                return True


def find_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = True,
) -> Generator[Path, None, None]:
    """
    Find files matching a pattern in a directory.
    
    Args:
        directory: Directory to search in
        pattern: Glob pattern to match files against
        recursive: Whether to search recursively
        
    Yields:
        Paths to matching files
        
    Raises:
        FileNotFoundError: If the directory does not exist
        PermissionError: If the directory cannot be accessed
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")
    
    glob_pattern = f"**/{pattern}" if recursive else pattern
    yield from directory.glob(glob_pattern)


def search_file_content(
    file_path: Union[str, Path],
    search_text: str,
    context_lines: int = 2,
    max_matches: Optional[int] = None,
    case_sensitive: bool = True,
    encoding: str = "utf-8",
) -> List[Tuple[int, List[str]]]:
    """
    Search for text in a file and return matching lines with context.
    
    Args:
        file_path: Path to the file to search
        search_text: Text to search for
        context_lines: Number of context lines to include before and after matches
        max_matches: Maximum number of matches to return (None for all)
        case_sensitive: Whether the search is case-sensitive
        encoding: Encoding to use when reading the file
        
    Returns:
        A list of tuples containing the line number and matching lines with context
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
        UnicodeDecodeError: If the file cannot be decoded with the specified encoding
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")
    
    # Read the file into a list of lines
    with open(file_path, "r", encoding=encoding) as f:
        lines = f.readlines()
    
    # Search for matches
    matches = []
    match_count = 0
    
    for i, line in enumerate(lines):
        if not case_sensitive:
            line_to_search = line.lower()
            search_text_lower = search_text.lower()
            if search_text_lower in line_to_search:
                match = True
            else:
                match = False
        else:
            if search_text in line:
                match = True
            else:
                match = False
        
        if match:
            # Calculate context line range
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            
            # Extract context lines
            context = lines[start:end]
            
            # Add match to results
            matches.append((i + 1, context))
            
            match_count += 1
            if max_matches is not None and match_count >= max_matches:
                break
    
    return matches


def write_file_safely(
    file_path: Union[str, Path],
    content: Union[str, bytes],
    mode: str = "w",
    encoding: Optional[str] = "utf-8",
    create_dirs: bool = True,
) -> bool:
    """
    Write content to a file safely, creating directories if needed.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        mode: File mode (w, wb, a, ab, etc.)
        encoding: Encoding to use when writing the file (None for binary mode)
        create_dirs: Whether to create parent directories if they don't exist
        
    Returns:
        True if the file was written successfully, False otherwise
        
    Raises:
        PermissionError: If the file cannot be written
    """
    file_path = Path(file_path)
    
    # Create parent directories if needed
    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Determine if we're in binary mode
        is_binary = "b" in mode
        
        # Set up keyword arguments
        kwargs = {}
        if not is_binary and encoding is not None:
            kwargs["encoding"] = encoding
        
        # Write the file
        with open(file_path, mode, **kwargs) as f:
            f.write(content)
        
        return True
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {str(e)}")
        return False


def read_file_safely(
    file_path: Union[str, Path],
    mode: str = "r",
    encoding: Optional[str] = "utf-8",
    default: Any = None,
) -> Any:
    """
    Read content from a file safely, returning a default value if the file cannot be read.
    
    Args:
        file_path: Path to the file to read
        mode: File mode (r, rb, etc.)
        encoding: Encoding to use when reading the file (None for binary mode)
        default: Default value to return if the file cannot be read
        
    Returns:
        The file content, or the default value if the file cannot be read
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return default
    
    try:
        # Determine if we're in binary mode
        is_binary = "b" in mode
        
        # Set up keyword arguments
        kwargs = {}
        if not is_binary and encoding is not None:
            kwargs["encoding"] = encoding
        
        # Read the file
        with open(file_path, mode, **kwargs) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return default


def paginate_large_file(
    file_path: Union[str, Path],
    page_size: int = 1000,
    page_number: int = 1,
    encoding: str = "utf-8",
) -> Tuple[List[str], int, int]:
    """
    Read a specific page of lines from a large file.
    
    Args:
        file_path: Path to the file to read
        page_size: Number of lines per page
        page_number: Page number to read (1-based)
        encoding: Encoding to use when reading the file
        
    Returns:
        A tuple containing the lines for the requested page, the total number of pages,
        and the total number of lines in the file
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
        ValueError: If page_number or page_size is invalid
    """
    if page_size <= 0:
        raise ValueError("Page size must be positive")
    
    if page_number <= 0:
        raise ValueError("Page number must be positive")
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Count the total number of lines in the file
    total_lines = sum(1 for _ in open(file_path, "r", encoding=encoding))
    
    # Calculate the total number of pages
    total_pages = (total_lines + page_size - 1) // page_size
    
    # Validate the page number
    if page_number > total_pages:
        raise ValueError(f"Page number {page_number} exceeds total pages {total_pages}")
    
    # Calculate the start and end line numbers (0-based)
    start_line = (page_number - 1) * page_size
    end_line = min(start_line + page_size, total_lines)
    
    # Read the requested page
    lines = []
    with open(file_path, "r", encoding=encoding) as f:
        # Skip to the start line
        for _ in range(start_line):
            next(f)
        
        # Read the requested lines
        for _ in range(end_line - start_line):
            lines.append(next(f))
    
    return lines, total_pages, total_lines