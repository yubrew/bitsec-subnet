build-miner-docker:
	docker build -t subnet-llm-miner -f Dockerfile.miner .

run-miner-local:
	docker run --env-file .env --network="host" -v $${HOME}/.bittensor/wallets:/root/.bittensor/wallets -it subnet-llm-miner python neurons/miner.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name miner --wallet.hotkey default --axon.port 8092 --axon.external_port 8092 --logging.debug

run-miner-testnet:
	docker run --env-file .env -p 8092:8092 -v $${HOME}/.bittensor/wallets:/root/.bittensor/wallets -it subnet-llm-miner python neurons/miner.py --netuid 204 --subtensor.chain_endpoint test --wallet.name miner --wallet.hotkey default --axon.port 8092 --axon.external_port 8092 --logging.debug

build-validator-docker:
	docker build -t subnet-llm-validator -f Dockerfile.validator .

run-validator-local:
	docker run --env-file .env --network="host" -v $${HOME}/.bittensor/wallets:/root/.bittensor/wallets -it subnet-llm-validator python neurons/validator.py --netuid 1 --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name validator --wallet.hotkey default --axon.port 8091 --axon.external_port 8091 --logging.debug

run-validator-testnet:
	docker run --env-file .env -p 8091:8091 -v $${HOME}/.bittensor/wallets:/root/.bittensor/wallets -it subnet-llm-validator python neurons/validator.py --netuid 204 --subtensor.chain_endpoint test --wallet.name validator --wallet.hotkey default --axon.port 8091 --axon.external_port 8091 --logging.debug


build-validator-api-docker:
	docker build -t subnet-llm-validator-api -f Dockerfile.validator_api .

run-api-local:
	docker run -p 8000:8000 -v $${HOME}/.bittensor/wallets:/root/.bittensor/wallets -it subnet-llm-validator-api python neurons/validator_api.py --netuid 1 --subtensor.chain_endpoint ws://host.docker.internal:9946 --wallet.name miner --wallet.hotkey default --axon.port 8093 --axon.external_port 8093 --logging.debug
