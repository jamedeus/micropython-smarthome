#!/bin/bash

# Track if any tests failed (can easily miss due to fast-moving output)
failed=0

# Run CLI tests
repo=$(pwd)
export PYTHONPATH="$PYTHONPATH:$repo/CLI"
pipenv run coverage run --data-file=.coverage.cli -m unittest discover tests/cli || failed=1

# Run frontend tests
cd frontend/ || { printf "ERROR: Unable to find frontend directory\n"; exit 1; }
pipenv run python3 manage.py test || failed=1
cd ..

# Run firmware tests
pipenv run coverage run --data-file=.coverage.firmware --source='core,devices,sensors' tests/mock_environment/runtests.py || failed=1

# Print all reports
printf "\n\n=== CLI TEST RESULTS ===\n\n"
pipenv run coverage report --data-file=.coverage.cli
printf "\n\n=== FRONTEND TEST RESULTS ===\n\n"
pipenv run coverage report --data-file=frontend/.coverage
printf "\n\n=== FIRMWARE TEST RESULTS ===\n\n"
pipenv run coverage report --data-file=.coverage.firmware

if [[ $failed == 1 ]]; then
    printf "\nTESTS FAILED\n"
else
    printf "\nALL TESTS PASSED\n"
fi
