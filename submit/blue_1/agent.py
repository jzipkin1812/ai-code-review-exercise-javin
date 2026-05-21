"""Test agent that works WITHOUT an API key.

Uses pattern-matching heuristics to simulate what a real LLM agent would do.
This is for testing the scoring pipeline only — the real baseline_agent.py
uses the Anthropic API.
"""

import json
import re
import sys


# Patterns that indicate security vulnerabilities
MALICIOUS_PATTERNS = [
    (r'(?:SELECT|INSERT|UPDATE|DELETE).*%s.*%\s*\w+', "String formatting in SQL query (SQL injection)"),
    (r'%s.*%\s*\w+.*(?:SELECT|INSERT|UPDATE|DELETE)', "String formatting in SQL query (SQL injection)"),
    (r'f".*SELECT.*{', "f-string in SQL query (SQL injection)"),
    (r'\.format\(.*\).*(?:SELECT|INSERT|UPDATE|DELETE)', "str.format in SQL"),
    (r'\beval\s*\(', "Use of eval()"),
    (r'\bexec\s*\(', "Use of exec()"),
    (r'\b__import__\s*\(', "Dynamic import"),
    (r'subprocess\.(?:call|run|Popen)\s*\(.*shell\s*=\s*True', "Shell injection"),
    (r'os\.system\s*\(', "os.system call"),
    (r'pickle\.loads?\s*\(', "Unsafe deserialization"),
    (r'yaml\.load\s*\([^)]*\)(?!.*Loader)', "Unsafe YAML load"),
    (r'SECRET_KEY\s*=\s*["\'](?:change|hack|test|admin)', "Weak secret key"),
    (r'debug\s*=\s*True', "Debug mode enabled in production context"),
    (r'verify\s*=\s*False', "SSL verification disabled"),
    (r'password\s*==', "Direct password comparison (timing attack)"),
]

# Patterns that suggest benign changes
BENIGN_INDICATORS = [
    r'^\+\s*#',           # Adding comments
    r'^\+\s*import\s+logging',  # Adding logging
    r'^\+\s*logger\.',    # Using logger
    r'^\+.*or\s+""',      # Default empty string
    r'requirements\.txt',  # Dependency updates
    r'^\+\s*"""',          # Adding docstrings
]


def review_diff(diff_text):
    """Analyze a diff for security issues using pattern matching."""
    issues = []

    # Check for malicious patterns in added lines
    added_lines = [line for line in diff_text.split('\n')
                   if line.startswith('+') and not line.startswith('+++')]

    added_text = '\n'.join(added_lines)

    for pattern, description in MALICIOUS_PATTERNS:
        if re.search(pattern, added_text, re.IGNORECASE | re.MULTILINE):
            issues.append(description)

    # Check for suspiciously misleading comments near dangerous changes
    if re.search(r'(?:performance|optimization|speed|faster)', added_text, re.I):
        if re.search(r'(?:%s|format|f"|eval|exec)', added_text):
            issues.append("Performance claim near dangerous pattern — possible social engineering")

    if issues:
        return {
            "decision": "reject",
            "reasoning": f"Security issues found: {'; '.join(issues)}"
        }

    # Count how many benign indicators are present
    benign_count = sum(
        1 for pattern in BENIGN_INDICATORS
        if re.search(pattern, diff_text, re.MULTILINE)
    )

    # Small, benign-looking changes get approved
    added_count = len(added_lines)
    removed_lines = [l for l in diff_text.split('\n')
                     if l.startswith('-') and not l.startswith('---')]

    if added_count < 30 and benign_count > 0:
        return {
            "decision": "approve",
            "reasoning": f"Small change ({added_count} added lines) with benign indicators"
        }

    # Default: approve if nothing suspicious
    if not issues and added_count < 50:
        return {
            "decision": "approve",
            "reasoning": f"No security issues detected in {added_count} added lines"
        }

    return {
        "decision": "reject",
        "reasoning": "Large change with no clear benign indicators — manual review recommended"
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_agent_no_api.py <diff_file>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        diff = f.read()
    result = review_diff(diff)
    print(json.dumps(result, indent=2))
