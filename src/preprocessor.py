"""
Log file preprocessor to extract relevant error information from large log files
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple

logger = logging.getLogger("devops_error_analyzer.preprocessor")

class LogPreprocessor:
    """
    Preprocesses large log files to extract error-related content
    and reduce token usage when sending to Azure OpenAI
    """
    
    # Keywords to look for in log files
    ERROR_KEYWORDS = [
        "error", "exception", "failure", "fail", "failed", "critical", 
        "severe", "fatal", "crash", "crashed", "abort", "aborted",
        "denied", "denied", "reject", "rejected", "timeout", "timed out",
        "invalid", "incorrect", "warning", "alert", "emergency", 
        "panic", "unexpected", "unable", "cannot", "not found", 
        "forbidden", "prohibited", "unauthorized", "access denied",
        "permission denied", "insufficient", "missing", "bad request",
        "out of memory", "OOM", "killed", "segfault", "null pointer",
        "unexpected EOF", "corrupt", "deadlock", "race condition",
        "leaked", "overflow", "underflow", "exceed", "too many",
        "too few", "too large", "too small"
    ]
    
    def __init__(self, context_lines: int = 2, max_errors: int = 500):
        """
        Initialize the log preprocessor
        
        Args:
            context_lines: Number of lines before and after error lines to include
            max_errors: Maximum number of error sections to extract (to prevent token overflow)
        """
        self.context_lines = context_lines
        self.max_errors = max_errors
    
    def extract_error_sections(self, log_file_path: str) -> str:
        """
        Extract error-related sections from a log file
        
        Args:
            log_file_path: Path to the log file
            
        Returns:
            Consolidated error sections as a single string
        """
        logger.info(f"Preprocessing log file: {log_file_path}")
        
        try:
            # Check if file exists and get file size
            file_path = Path(log_file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Log file not found: {log_file_path}")
            
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"Log file size: {file_size_mb:.2f} MB")
            
            # Read the file and extract error sections
            error_sections = []
            line_count = 0
            
            # First pass: count lines and check if preprocessing is needed
            with open(log_file_path, 'r', encoding='utf-8', errors='replace') as file:
                for _ in file:
                    line_count += 1
            
            logger.info(f"Log file line count: {line_count}")
            
            # If file is small enough, return it as is
            if file_size_mb < 0.2:  # Less than 200KB
                logger.info("Log file is small, returning entire content")
                with open(log_file_path, 'r', encoding='utf-8', errors='replace') as file:
                    return file.read()
            
            # For larger files, extract error sections
            with open(log_file_path, 'r', encoding='utf-8', errors='replace') as file:
                # Read all lines into memory
                lines = file.readlines()
                
            # Find lines with error keywords
            error_line_indices = set()
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in self.ERROR_KEYWORDS):
                    error_line_indices.add(i)
            
            logger.info(f"Found {len(error_line_indices)} lines with error keywords")
            
            # Extract sections with context
            extracted_sections = []
            processed_indices = set()
            
            # Sort the error line indices to process them in order
            for i in sorted(error_line_indices):
                # Skip if already processed as part of another section
                if i in processed_indices:
                    continue
                
                # Determine section boundaries
                start_idx = max(0, i - self.context_lines)
                end_idx = min(len(lines) - 1, i + self.context_lines)
                
                # Mark all indices in this range as processed
                for idx in range(start_idx, end_idx + 1):
                    processed_indices.add(idx)
                
                # Extract the section
                section = "".join(lines[start_idx:end_idx + 1])
                extracted_sections.append(section)
                
                # Check if we've hit the maximum number of sections
                if len(extracted_sections) >= self.max_errors:
                    logger.warning(f"Reached maximum error section limit: {self.max_errors}")
                    break
            
            # Join extracted sections with separators
            if extracted_sections:
                consolidated_errors = "\n\n" + "="*40 + " ERROR SECTION " + "="*40 + "\n\n".join(extracted_sections)
                logger.info(f"Extracted {len(extracted_sections)} error sections with context")
                return consolidated_errors
            else:
                logger.warning("No error sections found in log file")
                
                # If no error sections found, return a sample of the log
                sample_size = min(100, len(lines))
                logger.info(f"Returning first {sample_size} lines as a sample")
                return "".join(lines[:sample_size]) + "\n\n[...log file continues...]"
                
        except Exception as e:
            logger.error(f"Error preprocessing log file: {str(e)}")
            raise
    
    def _merge_overlapping_sections(self, sections: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Merge overlapping sections
        
        Args:
            sections: List of section start/end tuples
            
        Returns:
            Merged sections
        """
        if not sections:
            return []
        
        # Sort sections by start index
        sections.sort()
        
        merged = [sections[0]]
        
        for current in sections[1:]:
            previous = merged[-1]
            
            # If current section overlaps with previous, merge them
            if current[0] <= previous[1] + 1:
                merged[-1] = (previous[0], max(previous[1], current[1]))
            else:
                merged.append(current)
        
        return merged
    
    def extract_error_patterns(self, log_text: str) -> Dict:
        """
        Extract common error patterns and statistics from log text
        
        Args:
            log_text: Log text to analyze
            
        Returns:
            Dictionary with error patterns and statistics
        """
        error_stats = {
            "common_errors": {},
            "error_count": 0,
            "warning_count": 0,
            "exception_types": {},
            "error_codes": {},
        }
        
        # Extract exception types
        exception_pattern = r'([A-Za-z]+Exception|[A-Za-z]+Error):'
        exceptions = re.findall(exception_pattern, log_text)
        for exception in exceptions:
            if exception in error_stats["exception_types"]:
                error_stats["exception_types"][exception] += 1
            else:
                error_stats["exception_types"][exception] = 1
        
        # Extract error codes
        error_code_pattern = r'(?:error|code)[\s:=]+([A-Z0-9_\-]+)'
        error_codes = re.findall(error_code_pattern, log_text, re.IGNORECASE)
        for code in error_codes:
            if code in error_stats["error_codes"]:
                error_stats["error_codes"][code] += 1
            else:
                error_stats["error_codes"][code] = 1
        
        # Count errors and warnings
        error_stats["error_count"] = log_text.lower().count("error")
        error_stats["warning_count"] = log_text.lower().count("warning")
        
        # Extract common error messages
        error_line_pattern = r'^.*error.*$|^.*exception.*$|^.*fail.*$'
        error_lines = re.findall(error_line_pattern, log_text, re.IGNORECASE | re.MULTILINE)
        
        # Simplify and count recurring error patterns
        simplified_errors = {}
        for line in error_lines:
            # Replace specific details with placeholders to identify common patterns
            simplified = re.sub(r'[0-9a-f]{8}[-0-9a-f]{4}[-0-9a-f]{4}[-0-9a-f]{4}[-0-9a-f]{12}', '<UUID>', line)
            simplified = re.sub(r'\b\d+\b', '<NUM>', simplified)
            simplified = re.sub(r'\"[^\"]+\"', '<STRING>', simplified)
            
            if simplified in simplified_errors:
                simplified_errors[simplified] += 1
            else:
                simplified_errors[simplified] = 1
        
        # Sort by frequency and take top 10
        error_stats["common_errors"] = dict(sorted(
            simplified_errors.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        return error_stats
