#!/bin/bash

# Define output directory for generated images
OUTPUT_DIR="generated"
mkdir -p "$OUTPUT_DIR"

# Generate diagrams
echo "Generating diagrams..."

# Generate each diagram
for file in *.puml; do
    if [ -f "$file" ]; then
        echo "Processing $file..."
        base_name=$(basename "$file" .puml)
        plantuml -tpng "$file" -o "$OUTPUT_DIR"
    fi
done

echo "Done! Diagrams have been generated in the '$OUTPUT_DIR' directory."

# Open the generated directory
open "$OUTPUT_DIR"