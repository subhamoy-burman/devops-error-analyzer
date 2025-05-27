import os
import sys
import re
import logging
from pathlib import Path

logger = logging.getLogger("devops_error_analyzer.utils")

class ErrorClassifier:
    """
    Utility class to help classify common DevOps errors
    """
    
    ERROR_PATTERNS = {
        "kubernetes": [
            r"kubectl.*error",
            r"Error from server \(.*\)",
            r"pod.*not found",
            r"deployment.*failed",
            r"CrashLoopBackOff",
            r"ImagePullBackOff",
        ],
        "docker": [
            r"docker.*error",
            r"Error response from daemon",
            r"image.*not found",
            r"container.*exited",
            r"permission denied.*docker",
        ],
        "ci_cd": [
            r"pipeline.*failed",
            r"build.*error",
            r"(jenkins|github actions|gitlab ci|azure devops).*failed",
            r"workflow.*error",
        ],
        "terraform": [
            r"terraform.*error",
            r"Error applying plan",
            r"provider.*error",
            r"resource.*already exists",
        ],
        "cloud": [
            r"aws.*error",
            r"azure.*error",
            r"gcp.*error",
            r"cloud.*permission denied",
            r"access denied",
            r"insufficient permissions",
        ],
        "networking": [
            r"connection.*refused",
            r"timeout",
            r"network.*unreachable",
            r"dns.*error",
            r"no route to host",
        ]
    }
    
    @classmethod
    def classify_error(cls, error_text):
        """
        Classify the error text into known categories
        """
        if not error_text:
            return []
        
        categories = []
        for category, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_text, re.IGNORECASE):
                    categories.append(category)
                    break
        
        return list(set(categories))  # Remove duplicates

def extract_error_codes(text):
    """
    Extract error codes from text (e.g., "Error code: ABC-123")
    """
    # Common error code patterns
    patterns = [
        r'error\s+code[:\s]+([A-Z0-9\-_]+)',
        r'exit\s+code[:\s]+(\d+)',
        r'status\s+code[:\s]+(\d+)',
        r'exception\s+code[:\s]+([A-Z0-9\-_]+)'
    ]
    
    error_codes = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            error_codes.append(match.group(1))
    
    return error_codes

def generate_error_summary(error_text):
    """
    Generate a short summary of the error text
    """
    if not error_text or len(error_text) < 10:
        return "No error details provided"
    
    # Extract error codes
    error_codes = extract_error_codes(error_text)
    
    # Classify error
    categories = ErrorClassifier.classify_error(error_text)
    
    # Try to find the most significant part of the error message
    lines = error_text.strip().split('\n')
    error_lines = [line for line in lines if 'error' in line.lower()]
    
    if error_lines:
        summary = error_lines[0][:100]  # Take first error line, truncated
    else:
        summary = lines[0][:100]  # Take first line, truncated
    
    result = {
        'summary': summary,
        'error_codes': error_codes,
        'categories': categories,
        'total_lines': len(lines)
    }
    
    return result
