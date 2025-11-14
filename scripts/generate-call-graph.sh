#!/bin/bash
# SPDX-License-Identifier: Apache-2.0

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <json-file>"
    echo "Generates a call graph for the artifacts given in the JSON file."
    echo
    echo "The JSON file should contain an array of objects with as fields to the generate-call-graph.yml workflow:"
    echo "  - repository: The GitHub repository in the format 'owner/repo'."
    echo "  - tag: The git reference (tag or commit SHA)."
    echo "  - relative_path: The relative path to the artifact within the repository."
    echo "  - artifact: The GAV coordinates of the artifact (e.g., 'groupId:artifactId:version')."
    exit 1
fi

JSON_FILE="$1"
if [ ! -f "$JSON_FILE" ]; then
    echo "Error: File '$JSON_FILE' not found!"
    exit 1
fi

jq -c '.[]' "$JSON_FILE" | while read -r entry; do
    REPOSITORY=$(echo "$entry" | jq -r '.repository')
    TAG=$(echo "$entry" | jq -r '.tag')
    RELATIVE_PATH=$(echo "$entry" | jq -r '.relative_path')
    ARTIFACT=$(echo "$entry" | jq -r '.artifact')

    echo "Generating call graph for artifact '$ARTIFACT' from repository '$REPOSITORY' at tag '$TAG' and path '$RELATIVE_PATH'..."

    echo "$entry" | gh workflow run generate-call-graph.yaml --json

    if [ $? -ne 0 ]; then
        echo "Error: Failed to trigger workflow for artifact '$ARTIFACT'."
    else
        echo "Successfully triggered workflow for artifact '$ARTIFACT'."
    fi
done

