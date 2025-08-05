#!/bin/bash

# Setup script for freqtrade strategies.
# This script prepares specified strategies for Docker deployment by:
# 1. Packaging them into a 'strategies.tar.gz' archive for the Docker build.
# 2. Generating a 'docker-compose.yml' file to run each strategy in its own container.

set -e

# --- User Configuration ---
# Define the strategies you want to deploy here.
# These names must correspond to the strategy file or directory name in 'user_data/strategies/'.
STRATEGIES=(
    "ichiV1"
    "LookaheadStrategy"
    "Macd"
    "CustomStoplossWithPSAR"
    "MACDCCI"
)
# --- End of User Configuration ---

echo "Setting up Freqtrade Strategies for Docker Deployment"
echo "======================================================"

if [ ${#STRATEGIES[@]} -eq 0 ]; then
    echo "Error: No strategies defined in the STRATEGIES array. Please edit the script to add strategies."
    exit 1
fi

echo "Packaging ${#STRATEGIES[@]} strategies:"
for i in "${!STRATEGIES[@]}"; do
    echo "$((i+1)). ${STRATEGIES[$i]}"
done
echo ""

SOURCE_DIR="user_data/strategies"
TEMP_DIR="staging_strategies"
ARCHIVE_NAME="strategies.tar.gz"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' not found. Cannot package strategies."
    exit 1
fi

# Cleanup previous artifacts and create a temporary staging area
rm -rf "$TEMP_DIR" "$ARCHIVE_NAME"
mkdir -p "$TEMP_DIR"

echo "Locating and staging strategy files..."
found_count=0
for strategy in "${STRATEGIES[@]}"; do
    strategy_path_dir="$SOURCE_DIR/$strategy"
    strategy_path_file="$SOURCE_DIR/$strategy.py"
    
    if [ -d "$strategy_path_dir" ]; then
        cp -R "$strategy_path_dir" "$TEMP_DIR/"
        echo "✓ Staged '$strategy' (directory)"
        ((found_count++))
    elif [ -f "$strategy_path_file" ]; then
        cp "$strategy_path_file" "$TEMP_DIR/"
        echo "✓ Staged '$strategy' (file)"
        ((found_count++))
    else
        echo "⚠ Warning: Strategy file/dir not found for '$strategy' in '$SOURCE_DIR'"
    fi
done

if [ "$found_count" -eq 0 ]; then
    echo "Error: No strategy files were found for the configured strategies. Aborting."
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo ""
echo "Creating compressed archive '$ARCHIVE_NAME'..."
tar -czf "$ARCHIVE_NAME" -C "$TEMP_DIR" .
rm -rf "$TEMP_DIR"
echo "Successfully created '$ARCHIVE_NAME'."
echo ""

# --- Docker Compose Generation ---

echo "Generating docker-compose.yml..."

# Generate the service name for a strategy based on its name.
# This creates a consistent, DNS-friendly name (e.g., "MyStrategyV1" -> "mystrategyv1").
get_service_name() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g'
}

# Generates a snake_case version of a strategy name for the container name.
# Handles acronyms and mixed case more elegantly.
# e.g., "CustomStoplossWithPSAR" -> "custom_stoploss_with_psar"
# e.g., "MACDCCI" -> "macdcci"
# e.g., "ichiV1" -> "ichi_v1"
get_container_name_suffix() {
    local name="$1"
    
    # Handle all-caps acronyms (like MACDCCI, RSI, etc.)
    if [[ "$name" =~ ^[A-Z]+$ ]]; then
        echo "$name" | tr '[:upper:]' '[:lower:]'
        return
    fi
    
    # Handle mixed case with numbers (like ichiV1, SMA20, etc.)
    # First, add underscore before numbers
    name=$(echo "$name" | sed -E 's/([0-9])/_\1/g')
    
    # Then add underscore before uppercase letters that follow lowercase
    name=$(echo "$name" | sed -E 's/([a-z])([A-Z])/\1_\2/g')
    
    # Convert to lowercase and clean up
    echo "$name" | tr '[:upper:]' '[:lower:]' | sed -E 's/^_//'
}

# Build the 'depends_on' list for the UI service
depends_on_list=""
for strategy in "${STRATEGIES[@]}"; do
    service_name=$(get_service_name "$strategy")
    depends_on_list+="      - freqtrade-${service_name}\n"
done

# Write the header and the UI service definition to docker-compose.yml
cat > docker-compose.yml <<EOF
version: '3.8'

services:
  frequi:
    build:
      context: ./ui
      dockerfile: Dockerfile
    container_name: freqtrade-ui
    restart: unless-stopped
    ports:
      - "8080:80"
    depends_on:
$(echo -e "${depends_on_list}")
EOF

# Append a service definition for each strategy
port=8081
for strategy in "${STRATEGIES[@]}"; do
    service_name=$(get_service_name "$strategy")
    container_name_suffix=$(get_container_name_suffix "$strategy")
    cat >> docker-compose.yml <<EOF

  freqtrade-${service_name}:
    build: .
    container_name: freqtrade-trader-${container_name_suffix}
    restart: unless-stopped
    ports:
      - "${port}:8080"
    volumes:
      - "./user_data:/freqtrade/user_data"
    command: >
      trade
      --config /freqtrade/user_data/config.json
      --strategy ${strategy}
EOF
    port=$((port + 1))
done

echo "docker-compose.yml generated successfully."
echo ""
echo "Setup complete! Next steps:"
echo "1. The image will be built with your strategies from '$ARCHIVE_NAME'."
echo "2. Run 'docker-compose up --build' to build and start your strategy containers."
echo ""
echo "Ready for deployment! 🚀" 