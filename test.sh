#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

COVERAGE_FILE="coverage/.coverage_total"

# Run tests and generate coverage
coverage run manage.py test
coverage json
coverage report

# Extract the overall coverage percentage (integer) from the “TOTAL” line
TOTAL=$(
  coverage report --format=total
)

echo "Total coverage: ${TOTAL}%"

# If this is the first run, record the baseline and exit
if [[ ! -f "${COVERAGE_FILE}" ]]; then
  printf '%d\n' "${TOTAL}" > "${COVERAGE_FILE}"
  echo "Saved initial coverage percent."
  exit 0
fi

# Read previous coverage value
PREV_TOTAL=$(< "${COVERAGE_FILE}")

# Compare and act
if (( TOTAL < PREV_TOTAL )); then
  echo "Error: Coverage decreased from ${PREV_TOTAL}% to ${TOTAL}%!" >&2
  exit 1
else
  printf '%d\n' "${TOTAL}" > "${COVERAGE_FILE}"
  echo "Coverage did not decrease."
fi
