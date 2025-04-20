#!/bin/bash
set -e


# if the script throw error return the error code:
python error_regression.py || { echo "Tests failed, exiting"; exit 1; }

echo "Tests passed, good commit"
exit 0