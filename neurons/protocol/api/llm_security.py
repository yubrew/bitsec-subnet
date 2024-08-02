"""
The LLM API that will interface the subnet
"""
import traceback
import torch
import bittensor as bt
from bittensor.subnets import SubnetsAPI
from typing import List, Optional, Union, Any, Dict, AsyncGenerator

from protocol.protocol import LLMSecurityGen
from protocol.utils.config import config, check_config, add_args
from protocol.api.get_query_axons import get_query_api_axons
from protocol.utils.uids import get_random_uids

from pydantic import BaseModel, Field
import asyncio

class TextGenerationInput(BaseModel):
    prompt_text: str = ""

class LLMSecurityGenAPI(SubnetsAPI):
    def __init__(self):
        client_config = self.client_config()
        self.config = client_config
        self.check_config(client_config)
        self.wallet = bt.wallet(config=client_config)
        bt.logging.info(f"Client Config Info: {client_config}...")
        super().__init__(self.wallet)

        self.subtensor = bt.subtensor(config=client_config)

        self.metagraph = self.subtensor.metagraph(client_config.netuid)
        bt.logging.info(f"Metagraph: {self.metagraph}")
        bt.logging.info(f"Metagraph axons: {self.metagraph.axons}")

        self.metagraph.sync(subtensor=self.subtensor)

        self.netuid = client_config.netuid
        self.name = "llm-security-gen"

        self.metagraph_resync: Task

    def prepare_synapse(self, prompt_input: str) -> LLMSecurityGen:
        synapse = LLMSecurityGen(prompt_input=prompt_input)
        return synapse

    async def process_responses(
        self, responses: AsyncGenerator[Union["bt.Synapse", Any], None]
    ) -> List[str]:
        outputs = []
        async for response in responses:
            bt.logging.info(f"Parsing response: {response}...")
            if not response:
                continue
            outputs.append(response)
        return outputs

    async def get_responses(
        self,
        axons: Union[bt.axon, List[bt.axon]],
        synapse: LLMSecurityGen,
        timeout: int,
    ) -> AsyncGenerator[str, None]:
        if isinstance(axons, list):
            bt.logging.info(f"its instance")
            responses = asyncio.as_completed([
                self.dendrite(
                    axons=axon,
                    synapse=synapse,
                    deserialize=True,
                    timeout=timeout,
                )
                for axon in axons
            ])

            for future in responses:
                yield await future
        else:
            yield await self.dendrite(
                axons=axons,
                synapse=synapse,
                deserialize=True,
                timeout=timeout,
            )

    async def query_api(
        self,
        inputs: TextGenerationInput,
        axons: Union[bt.axon, List[bt.axon]],
        timeout: Optional[int] = 60,
    ) -> List[str]:
        synapse = self.prepare_synapse(inputs.prompt_text)
        bt.logging.info(f"Prepared synapse for query: {synapse}")
        bt.logging.info(f"Querying validator axons {axons} with synapse {synapse}...")

        resp_generator = self.get_responses(axons, synapse, timeout)
        bt.logging.info(f"Responses received: {resp_generator}")
        return await self.process_responses(resp_generator)

    def get_all_axons(self):
        return self.metagraph.axons

    @classmethod
    def client_config(cls):
        return config(cls)

    @classmethod
    def check_config(cls, client_config: "bt.Config"):
        check_config(cls, client_config)

    @classmethod
    def add_args(cls, parser):
        add_args(cls, parser)

    async def __aenter__(self):
        async def resync_metagraph():
            while True:
                bt.logging.info("resync_metagraph()")

                try:
                    self.metagraph.sync(subtensor=self.subtensor)
                    await sync_neuron_info(self, self.dendrite)
                except Exception as _:
                    bt.logging.error("Failed to sync client metagraph, ", traceback.format_exc())

                await asyncio.sleep(30)

        self.metagraph_resync = asyncio.get_event_loop().create_task(resync_metagraph())

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.metagraph_resync.cancel()
