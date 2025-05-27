import os
import sys
import base64
import time
from openai import AzureOpenAI
import argparse
from pathlib import Path
import json
import logging

# Load environment variables from .env file
from src.config import load_env_file
from src.preprocessor import LogPreprocessor

# Make sure environment variables are loaded
load_env_file()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("devops_error_analyzer")

class DevOpsErrorAnalyzer:
    def __init__(self, endpoint=None, deployment=None, api_key=None):
        """
        Initialize the DevOps Error Analyzer with Azure OpenAI configuration
        """
        self.endpoint = endpoint or os.getenv("ENDPOINT_URL")
        self.deployment = deployment or os.getenv("DEPLOYMENT_NAME")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("No API key provided. Set the AZURE_OPENAI_API_KEY environment variable or pass it as a parameter.")
        
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version="2025-01-01-preview",
        )
        
        logger.info(f"DevOps Error Analyzer initialized with deployment: {self.deployment}")

    def analyze_error(self, error_text):
        """
        Analyze the provided error text and generate a solution
        """
        if not error_text or error_text.strip() == "":
            logger.warning("No error text provided for analysis")
            return "Please provide error text for analysis"
            
        logger.info(f"Analyzing error text of length: {len(error_text)}")
        
        # Prepare the chat prompt
        chat_prompt = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        You are a specialized DevOps troubleshooting assistant. Your task is to:
                        1. Analyze the provided error logs or text
                        2. Identify the root cause of the problem
                        3. Provide a clear, step-by-step solution to fix the issue
                        4. Include any relevant commands, code snippets, or configuration changes needed
                        5. Suggest preventive measures to avoid similar issues in the future
                        
                        Format your response in a clear, structured manner with separate sections for:
                        - Problem Identification
                        - Root Cause Analysis
                        - Step-by-Step Solution
                        - Preventive Measures
                        """
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Please analyze the following DevOps error and provide a solution:\n\n{error_text}"
                    }
                ]
            }
        ]

        try:
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=chat_prompt,
                temperature=0.2,
                max_tokens=4000
            )
            
            solution = response.choices[0].message.content
            logger.info("Analysis completed successfully")
            return solution
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            return f"An error occurred during analysis: {str(e)}"
    
    def analyze_error_from_file(self, file_path, context_lines=2, preprocess_large_files=True):
        """
        Read error text from a file and analyze it
        
        Args:
            file_path: Path to the file containing error text
            context_lines: Number of lines before and after error lines to include when preprocessing
            preprocess_large_files: Whether to preprocess large log files to extract only error sections
        """
        try:
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # Check if file is large and preprocessing is enabled
            if preprocess_large_files and file_size_mb >= 0.01:  # If file is >= 500KB
                logger.info(f"Large log file detected ({file_size_mb:.2f} MB). Preprocessing to extract error sections.")
                
                # Create preprocessor instance
                preprocessor = LogPreprocessor(context_lines=context_lines)
                
                # Extract error sections
                start_time = time.time()
                error_text = preprocessor.extract_error_sections(file_path)
                end_time = time.time()
                
                # Get error pattern statistics
                error_stats = preprocessor.extract_error_patterns(error_text)
                
                logger.info(f"Preprocessing completed in {end_time - start_time:.2f} seconds")
                logger.info(f"Extracted text size: {len(error_text) / 1024:.2f} KB")
                logger.info(f"Error statistics: {error_stats}")
                
                # Add a summary of error statistics to the error text
                stats_summary = "\n\n" + "="*80 + "\nERROR STATISTICS SUMMARY\n" + "="*80 + "\n"
                stats_summary += f"Total errors identified: {error_stats['error_count']}\n"
                stats_summary += f"Total warnings identified: {error_stats['warning_count']}\n"
                
                if error_stats['exception_types']:
                    stats_summary += "\nException types:\n"
                    for exception, count in error_stats['exception_types'].items():
                        stats_summary += f"- {exception}: {count} occurrences\n"
                
                if error_stats['error_codes']:
                    stats_summary += "\nError codes:\n"
                    for code, count in error_stats['error_codes'].items():
                        stats_summary += f"- {code}: {count} occurrences\n"
                
                error_text = stats_summary + "\n" + error_text
                
                if file_size_mb > 3:  # For very large files, add a note for the AI
                    error_text = (
                        "NOTE: This is a preprocessed version of a very large log file "
                        f"({file_size_mb:.2f} MB). Only sections containing errors and "
                        f"{context_lines} lines of context before and after are included.\n\n"
                    ) + error_text
                
                return self.analyze_error(error_text)
            else:
                # For smaller files, read the entire content
                with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                    error_text = file.read()
                return self.analyze_error(error_text)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return f"Error reading file: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='DevOps Error Analyzer - Get solutions for your DevOps errors')
    
    # Add arguments
    parser.add_argument('--text', type=str, help='Error text to analyze')
    parser.add_argument('--file', type=str, help='Path to file containing error text')
    parser.add_argument('--api-key', type=str, help='Azure OpenAI API key')
    parser.add_argument('--endpoint', type=str, help='Azure OpenAI endpoint URL')
    parser.add_argument('--deployment', type=str, help='Azure OpenAI deployment name')
    parser.add_argument('--output', type=str, help='Output file to save the analysis results')
    parser.add_argument('--context-lines', type=int, default=2, help='Number of context lines to include before and after error lines (default: 2)')
    parser.add_argument('--raw', action='store_true', help='Process raw log file without preprocessing')
    parser.add_argument('--save-preprocessed', type=str, help='Save the preprocessed log to a file before analysis')
    
    args = parser.parse_args()
    
    # Initialize the analyzer
    try:
        analyzer = DevOpsErrorAnalyzer(
            endpoint=args.endpoint,
            deployment=args.deployment,
            api_key=args.api_key
        )
          # Get the error text
        error_text = None
        preprocessed_text = None
        
        if args.text:
            error_text = args.text
            solution = analyzer.analyze_error(error_text)
        elif args.file:
            logger.info(f"Processing log file: {args.file}")
            
            # Check if preprocessing should be skipped
            should_preprocess = not args.raw
            
            # If file needs to be processed, use the preprocessing function
            if should_preprocess:
                # Process the file and get analysis
                if args.save_preprocessed:
                    # First get the preprocessed text
                    preprocessor = LogPreprocessor(context_lines=args.context_lines)
                    preprocessed_text = preprocessor.extract_error_sections(args.file)
                    
                    # Save the preprocessed text
                    with open(args.save_preprocessed, 'w', encoding='utf-8') as file:
                        file.write(preprocessed_text)
                    logger.info(f"Saved preprocessed log to: {args.save_preprocessed}")
                
                # Analyze the file with preprocessing
                solution = analyzer.analyze_error_from_file(
                    args.file, 
                    context_lines=args.context_lines, 
                    preprocess_large_files=should_preprocess
                )
            else:
                # Read the entire file without preprocessing
                with open(args.file, 'r', encoding='utf-8', errors='replace') as file:
                    error_text = file.read()
                solution = analyzer.analyze_error(error_text)
        else:
            print("Please provide error text using --text or --file argument")
            parser.print_help()
            return 1
        
        # Output the solution
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as file:
                file.write(solution)
            print(f"Analysis saved to {args.output}")
        else:
            print("\n" + "="*50)
            print("DEVOPS ERROR ANALYSIS RESULTS")
            print("="*50 + "\n")
            print(solution)
        
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
