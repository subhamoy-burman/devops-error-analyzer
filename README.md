# DevOps Error Analyzer

A Python tool that analyzes DevOps error logs and provides actionable solutions using Azure OpenAI.

## Features

- Analyzes error logs from various DevOps tools and platforms
- Identifies root causes of common DevOps issues
- Provides step-by-step solutions to resolve problems
- Suggests preventive measures
- Supports analysis from text or file input
- **Smart Log Preprocessing**: Automatically extracts relevant error sections from large log files to reduce token usage

## Installation

1. Clone the repository
2. Install the requirements:

```powershell
cd devops_error_analyzer
pip install -r requirements.txt
```

3. Set up your Azure OpenAI environment variables:

```powershell
$env:ENDPOINT_URL="your-azure-openai-endpoint"
$env:DEPLOYMENT_NAME="your-deployment-name"
$env:AZURE_OPENAI_API_KEY="your-api-key"
```

## Usage

### Command Line Interface

Analyze errors from a file:

```powershell
python src/main.py --file "./data/sample_errors.log"
```

Analyze errors from text input:

```powershell
python src/main.py --text "Error: connection refused when connecting to database"
```

Save analysis to a file:

```powershell
python src/main.py --file "./data/sample_errors.log" --output "./analysis_results.txt"
```

### Large Log File Processing

For large log files, the tool automatically extracts and analyzes only the error-related sections to reduce token usage:

```powershell
# Process a large log file with default settings (2 lines of context before/after errors)
python src/main.py --file "./data/large_sample.log"

# Increase context to 5 lines before and after each error
python src/main.py --file "./data/large_sample.log" --context-lines 5

# Process raw log without preprocessing (for smaller files)
python src/main.py --file "./data/small_sample.log" --raw

# Save the preprocessed log for inspection
python src/main.py --file "./data/large_sample.log" --save-preprocessed "./preprocessed.log"
```

### Generating Test Log Files

The tool includes a utility to generate test log files with configurable size and error density:

```powershell
# Generate a test log file with default settings (50,000 entries, 5% errors)
python src/generate_test_logs.py

# Generate a larger log file with more errors
python src/generate_test_logs.py --entries 100000 --error-percentage 10 --filename "./data/large_error_sample.log"
```

### Using custom Azure OpenAI settings

```powershell
python src/main.py --file "./data/sample_errors.log" --endpoint "your-endpoint" --deployment "your-deployment" --api-key "your-api-key"
```

## Sample Data

A sample error log file is included in the `data` directory for testing:

```
data/sample_errors.log
```

## Requirements

- Python 3.8+
- Azure OpenAI subscription
- Internet connection for API access

## How It Works

1. The tool takes DevOps error logs or messages as input
2. It pre-processes and categorizes the errors
3. The error information is sent to Azure OpenAI
4. The AI analyzes the errors and generates solutions
5. The tool formats and presents the solutions

## License

This project is licensed under the MIT License
