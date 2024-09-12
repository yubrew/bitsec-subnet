#!/bin/bash

# Load environment variables from .env file
set -a
source validator.env
set +a

# Check if the process is already running
if pm2 list | grep -q "bitsec_validator"; then
  echo "Process 'bitsec_validator' is already running. Deleting it..."
  pm2 delete bitsec_validator
fi

# Start the process with arguments from environment variables
pm2 start python --name bitsec_validator -- neurons/validator.py \
  --netuid $NETUID \
  --subtensor.network $SUBTENSOR_NETWORK \
  --subtensor.chain_endpoint $SUBTENSOR_CHAIN_ENDPOINT \
  --wallet.name $WALLET_NAME \
  --wallet.hotkey $WALLET_HOTKEY \
  --axon.port $VALIDATOR_AXON_PORT
