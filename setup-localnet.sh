# setup devnet locally

#!/bin/bash
set -euo pipefail

# Check if Docker is installed
if ! command -v docker &> /dev/null
then
    echo "Docker is not installed. Please install Docker Desktop for macOS first."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null
then
    echo "Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

if ! command -v btcli &> /dev/null
then
  echo "ERROR: please install btcli: https://github.com/opentensor/bittensor?tab=readme-ov-file#install"
  exit 1
fi

: "${OWNER_WALLET_NAME:=owner}"
: "${VALIDATOR_WALLET_NAME:=validator}"
: "${MINER_WALLET_NAME:=miner}"
: "${WALLETS_DIR:=$HOME/.bittensor/wallets}"
WALLETS_DIR=$(realpath "$WALLETS_DIR")

# set up wallets
for WALLET_NAME in "$OWNER_WALLET_NAME" "$VALIDATOR_WALLET_NAME" "$MINER_WALLET_NAME"
do
  if [ ! -e "$WALLETS_DIR/$WALLET_NAME" ]
  then
    echo "Creating wallet: $WALLET_NAME"
    btcli wallet create --wallet.name "$WALLET_NAME" --wallet.hotkey default --no_password --no_prompt
  fi
done

BT_DEFAULT_TOKEN_WALLET=$(python3 -c 'import sys, json; print(json.load(sys.stdin)["ss58Address"])' < "$WALLETS_DIR/$OWNER_WALLET_NAME/coldkeypub.txt")

echo "Setting up Docker container for subtensor..."

# use docker-compose.yml to build from Dockerfile
# cat > docker-compose.yml <<EOF
# services:
#   subtensor:
#     build:
#       context: .
#       dockerfile: Dockerfile
#     restart: unless-stopped
#     volumes:
#       - './chain/alice:/tmp/alice'
#       - './chain/bob:/tmp/bob'
#       - './chain/spec:/spec'
#       - '/Users/john/.bittensor:/root/.bittensor'
#     ports:
#       - '30334:30334'
#       - '9946:9946'
#       - '9934:9934'
#     environment:
#       - BT_DEFAULT_TOKEN_WALLET=5Ca8wibJNPwXrqdw4k3BxfuuVAYcSrT9d8DbEzPcA2AFSXGG
#       - OPENAI_API_KEY
# EOF

docker compose pull
docker compose up -d --force-recreate

# btcli command wrapper
run_btcli_command() {
    max_attempts=3
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if $@; then
            return 0
        fi
        attempt=$((attempt+1))
        echo "Command failed. Retrying in 5 seconds... (attempt $attempt of $max_attempts)"
        sleep 5
    done
    echo "Command failed after $max_attempts attempts."
    return 1
}

echo "Waiting for subtensor to start..."
max_attempts=30
attempt=0
while ! curl -s http://localhost:9946 > /dev/null; do
    if [ $attempt -eq $max_attempts ]; then
        echo "Subtensor failed to start after $max_attempts attempts."
        exit 1
    fi
    attempt=$((attempt+1))
    echo "Waiting for subtensor to start (attempt $attempt)..."
    sleep 2
done

CHAIN_ENDPOINT="ws://localhost:9946"
echo ">> subtensor installed, chain endpoint: $CHAIN_ENDPOINT"

run_btcli_command btcli subnet create --wallet.name "$OWNER_WALLET_NAME" --wallet.hotkey default --subtensor.chain_endpoint "$CHAIN_ENDPOINT" --no_prompt

# Transfer tokens to miner and validator coldkeys
BT_MINER_TOKEN_WALLET=$(python3 -c 'import sys, json; print(json.load(sys.stdin)["ss58Address"])' < "$WALLETS_DIR/$MINER_WALLET_NAME/coldkeypub.txt")
BT_VALIDATOR_TOKEN_WALLET=$(python3 -c 'import sys, json; print(json.load(sys.stdin)["ss58Address"])' < "$WALLETS_DIR/$VALIDATOR_WALLET_NAME/coldkeypub.txt")

btcli wallet transfer --subtensor.network "$CHAIN_ENDPOINT" --wallet.name "$OWNER_WALLET_NAME" --dest "$BT_MINER_TOKEN_WALLET" --amount 1000 --no_prompt
btcli wallet transfer --subtensor.network "$CHAIN_ENDPOINT" --wallet.name "$OWNER_WALLET_NAME" --dest "$BT_VALIDATOR_TOKEN_WALLET" --amount 10000 --no_prompt

# Register wallet hotkeys to subnet
btcli subnet register --wallet.name "$MINER_WALLET_NAME" --netuid 1 --wallet.hotkey default --subtensor.chain_endpoint "$CHAIN_ENDPOINT" --no_prompt
btcli subnet register --wallet.name "$VALIDATOR_WALLET_NAME" --netuid 1 --wallet.hotkey default --subtensor.chain_endpoint "$CHAIN_ENDPOINT" --no_prompt

# Add stake to the validator
btcli stake add --wallet.name "$VALIDATOR_WALLET_NAME" --wallet.hotkey default --subtensor.chain_endpoint "$CHAIN_ENDPOINT" --amount 100 --no_prompt

# Set root weight
btcli root register --wallet.name "$VALIDATOR_WALLET_NAME" --wallet.hotkey default --subtensor.chain_endpoint "$CHAIN_ENDPOINT" --no_prompt
sleep 4800 # Add 80 min sleep to avoid SettingWeightsTooFast error
btcli root boost --netuid 1 --increase 1 --wallet.name "$VALIDATOR_WALLET_NAME" --wallet.hotkey default --subtensor.chain_endpoint "$CHAIN_ENDPOINT" --no_prompt

cat <<EOF


    Local subtensor setup complete.
    CHAIN_ENDPOINT: $CHAIN_ENDPOINT
    Use this chain endpoint with your test miners/validators and btcli command's --subtensor.network option.
EOF

# uncomment to kill the container when the script exits
# leave it up to run more actions like mining, staking, setting weights, transfer, etc
# cleanup() {
#     echo "Cleaning up..."
#     docker compose down
#     exit
# }

# trap cleanup EXIT