# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 Idris Hanafi
# Copyright © 2024 [Your Name]

import os
import random
import argparse
import asyncio
import bittensor as bt
import torch
from typing import List
from neurons.protocol import LLMSecurityGen

class Validator:
    def __init__(self, config):
        self.config = config
        self.subtensor = bt.subtensor(config=config)
        self.wallet = bt.wallet(config=config)
        self.metagraph = self.subtensor.metagraph(self.config.netuid)
        self.dendrite = bt.dendrite(wallet=self.wallet)
        self.sample_dir = os.path.join(os.path.dirname(__file__), '..', 'samples')
        bt.logging.info(f"Validator {self.wallet.hotkey} initialized")

    async def run(self):
        bt.logging.info("Validator running...")
        
        step = 0
        while True:
            bt.logging.info(f"Step {step}")
            
            try:
                # Sync the metagraph
                self.metagraph.sync(subtensor=self.subtensor)
                
                # Get a Solidity code sample for analysis
                solidity_code = self.get_solidity_sample()

                # Query the network
                responses = await self.query_network(solidity_code)

                # Process responses and update scores
                scores = self.process_responses(responses)

                # Update weights based on scores
                self.update_weights(scores)

                # Set weights on the Bittensor network
                await self.set_weights()

            except Exception as e:
                bt.logging.error(f"Error in validator loop: {e}")

            step += 1
            await asyncio.sleep(self.config.validator_sleep)

    def get_solidity_sample(self) -> str:
        """Load a random Solidity code sample from the samples directory."""
        sample_files = [f for f in os.listdir(self.sample_dir) if f.endswith('.sol')]
        if not sample_files:
            raise ValueError("No Solidity sample files found")
        
        sample_file = os.path.join(self.sample_dir, random.choice(sample_files))
        with open(sample_file, 'r') as file:
            return file.read()

    async def query_network(self, solidity_code: str) -> List[dict]:
        """Query the network with the given Solidity code."""
        bt.logging.info(f"Querying network with Solidity code sample")
        responses = await self.dendrite.query(
            self.metagraph.axons,
            LLMSecurityGen(solidity_input=solidity_code),
            deserialize=True,
            timeout=self.config.timeout
        )
        return responses

    def process_responses(self, responses: List[dict]) -> torch.Tensor:
        """Process responses and calculate scores."""
        scores = torch.zeros(len(self.metagraph.axons))
        
        for i, (axon, response) in enumerate(zip(self.metagraph.axons, responses)):
            if response is not None and isinstance(response, dict):
                vulnerabilities = response.get('vulnerabilities', [])
                fixes = response.get('fixes', [])
                
                bt.logging.info(f"Response from {axon.hotkey}:")
                bt.logging.info(f"Vulnerabilities: {vulnerabilities}")
                bt.logging.info(f"Fixes: {fixes}")
                
                # Calculate score based on number and quality of vulnerabilities and fixes
                score = len(vulnerabilities) + len(fixes)
                
                # TODO: Implement more sophisticated scoring
                # For example, check if fixes actually address the vulnerabilities,
                # or use a language model to evaluate the quality of the analysis
                
                scores[i] = score
        
        return scores

    def update_weights(self, scores: torch.Tensor):
        """Update weights based on calculated scores."""
        weights = torch.nn.functional.normalize(scores, p=1.0, dim=0)
        self.metagraph.set_weights(weights)

    async def set_weights(self):
        """Set weights on the Bittensor network."""
        try:
            weights = self.metagraph.weights
            uids = self.metagraph.uids.to("cpu")
            
            bt.logging.info("Setting weights on chain...")
            result = await self.subtensor.set_weights(
                netuid=self.config.netuid,
                wallet=self.wallet,
                uids=uids,
                weights=weights,
                wait_for_inclusion=True,
                version_key=1,
            )
            if result:
                bt.logging.success("Successfully set weights.")
            else:
                bt.logging.error("Failed to set weights.")
        except Exception as e:
            bt.logging.error(f"Failed to set weights on the network: {e}")

def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("--netuid", type=int, default=1, help="The chain subnet uid.")
    parser.add_argument("--wallet.name", type=str, default="default", help="The name of the wallet to use.")
    parser.add_argument("--wallet.hotkey", type=str, default="default", help="The name of the hotkey to use.")
    parser.add_argument("--logging.debug", action="store_true", help="Enable debug logging.")
    parser.add_argument("--logging.trace", action="store_true", help="Enable trace logging.")
    parser.add_argument("--validator_sleep", type=float, default=60, help="The number of seconds to sleep between validation rounds.")
    parser.add_argument("--timeout", type=float, default=30, help="The timeout for each network query in seconds.")
    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    config = bt.config(parser)
    return config

async def main(config):
    validator = Validator(config)
    await validator.run()

if __name__ == "__main__":
    config = get_config()
    bt.logging(config=config)
    asyncio.run(main(config))