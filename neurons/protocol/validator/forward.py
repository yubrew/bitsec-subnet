# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): John Yu
# Copyright © 2024 John Yu

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import bittensor as bt
import uuid

from protocol.protocol import LLMSecurityGen
from protocol.validator.reward import get_rewards
from protocol.utils.uids import get_random_uids

from openai import OpenAI

async def forward(self):
    """
    The forward function is called by the validator every time step.

    It is responsible for querying the network and scoring the responses.

    Args:
        self (:obj:`bittensor.neuron.Neuron`): The neuron object which contains all the necessary state for the validator.

    """

    miner_uids = get_random_uids(self, k=self.config.neuron.sample_size)

    bt.logging.info(f"miners: {miner_uids}")
    bt.logging.info(f"metagraph: {self.metagraph}")
    bt.logging.info(f"metagraph axons: {self.metagraph.axons}")

    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an LLM that will respond with only simple language that returns in the form of: `Create a solidity contract with {randomly generate a name here}`"},
            {"role": "user", "content": "Give me a sample prompt that asks an LLM to generate a sample solidity contract"},
        ]
    )
    challenge = completion.choices[0].message.content

    responses = await self.dendrite(
        axons=[self.metagraph.axons[uid] for uid in miner_uids],
        synapse=LLMSecurityGen(prompt_input=challenge),
        deserialize=True,
        timeout=self.config.neuron.timeout,
    )

    bt.logging.info(f"Received responses: {responses}")

    rewards = get_rewards(self, uid=str(uuid.uuid1()), query=challenge, responses=responses)

    bt.logging.info(f"Scored responses: {rewards}")
    self.update_scores(rewards, miner_uids)
