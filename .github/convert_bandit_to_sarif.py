#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timezone


def convert_to_sarif(bandit_json_file, sarif_output_file):
    """
    Convert Bandit JSON output to SARIF format.
    """
    # Load the Bandit JSON output
    with open(bandit_json_file, "r") as f:
        bandit_data = json.load(f)

    # Create SARIF format
    sarif_output = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Bandit",
                        "informationUri": "https://github.com/PyCQA/bandit",
                        "semanticVersion": bandit_data.get("metadata", {}).get(
                            "version", "1.0.0"
                        ),
                        "rules": [],
                    }
                },
                "results": [],
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "commandLine": "bandit -r tapo_exporter/",
                        "endTimeUtc": datetime.now(timezone.utc)
                        .isoformat()
                        .replace("+00:00", "Z"),
                        "workingDirectory": {"uri": "file:///"},
                    }
                ],
            }
        ],
    }

    # Process Bandit results into SARIF
    rule_indices = {}
    for result in bandit_data.get("results", []):
        test_id = result.get("test_id", "")
        test_name = result.get("test_name", "")

        # Add rule if not already added
        if test_id not in rule_indices:
            rule = {
                "id": test_id,
                "name": test_name,
                "shortDescription": {"text": test_name},
                "fullDescription": {"text": result.get("issue_text", "")},
                "defaultConfiguration": {"level": "warning"},
            }

            sarif_output["runs"][0]["tool"]["driver"]["rules"].append(rule)
            rule_indices[test_id] = (
                len(sarif_output["runs"][0]["tool"]["driver"]["rules"]) - 1
            )

        # Map Bandit severity to SARIF level
        level = "warning"
        if result.get("issue_severity", "").lower() == "high":
            level = "error"
        elif result.get("issue_severity", "").lower() == "low":
            level = "note"

        # Add result
        sarif_result = {
            "ruleId": test_id,
            "ruleIndex": rule_indices[test_id],
            "level": level,
            "message": {"text": result.get("issue_text", "")},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": result.get("filename", "").replace("\\", "/")
                        },
                        "region": {
                            "startLine": result.get("line_number", 1),
                            "startColumn": 1,
                        },
                    }
                }
            ],
        }

        sarif_output["runs"][0]["results"].append(sarif_result)

    # Write SARIF output
    with open(sarif_output_file, "w") as f:
        json.dump(sarif_output, f, indent=2)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <bandit_json_file> <sarif_output_file>")
        sys.exit(1)

    convert_to_sarif(sys.argv[1], sys.argv[2])
