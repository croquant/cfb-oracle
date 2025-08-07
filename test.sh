#!/bin/sh

COVERAGE_FILE="coverage/.coverage_total"

# Run tests and generate coverage
coverage run manage.py test && coverage json && coverage report

# Get current total coverage percent (as integer)
TOTAL=$(coverage report --format=total | awk '{print int($1)}')
echo "Total coverage: $TOTAL%"

# If file doesn't exist, create it
if [ ! -f "$COVERAGE_FILE" ]; then
    echo "$TOTAL" > "$COVERAGE_FILE"
    echo "Saved initial coverage percent."
    exit 0
fi

# Read previous coverage percent
PREV_TOTAL=$(cat "$COVERAGE_FILE")

if [ "$TOTAL" -lt "$PREV_TOTAL" ]; then
    echo "Error: Coverage decreased from $PREV_TOTAL% to $TOTAL%!"
    exit 1
else
    echo "$TOTAL" > "$COVERAGE_FILE"
    echo "Coverage did not decrease."
fi