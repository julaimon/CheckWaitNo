#!/bin/bash
set -e

# Root folder of your project
ROOT_DIR=$(pwd)

# Function to build a Lambda package
build_lambda() {
    LAMBDA_DIR=$1   # e.g., webhook or checker
    ZIP_NAME=$2     # e.g., webhook_lambda.zip

    echo "Building $ZIP_NAME..."

    cd "$ROOT_DIR/$LAMBDA_DIR"

    # Ensure package folder exists
    rm -rf package
    mkdir package

    # Install dependencies into package folder
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt -t package/
    fi

    # Copy lambda_function.py and get_data.py into package folder
    cp lambda_function.py get_data.py package/

    # Create ZIP of the contents of package folder
    cd package
    zip -r "../$ZIP_NAME" .

    echo "$ZIP_NAME created successfully!"
}

# Build both Lambdas
build_lambda "webhook" "webhook_lambda.zip"
build_lambda "checker" "checker_lambda.zip"

echo "All Lambda packages built."
