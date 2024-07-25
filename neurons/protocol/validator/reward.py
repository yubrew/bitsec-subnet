# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): Idris Hanafi
# Copyright © 2023 Idris Hanafi

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

import torch
from typing import List
import os
import subprocess
import shutil
import bittensor as bt

def write_contract(file_path, code):
    with open(file_path, 'w') as file:
        file.write(code)

def compile_solidity_code(uid, solidity_code):
    contract_path = ""
    contract_dir = "contracts"

    if not os.path.exists(contract_dir):
        os.makedirs(contract_dir)

    json_res = {"status": False, "message": ""}

    try:
        contract_name = solidity_code.split('contract ')[1].split(' ')[0]

        contract_path = os.path.join(contract_dir, f'{contract_name}.sol')

        # Write solidity code to a file
        write_contract(contract_path, solidity_code)

        # Compile using Foundry
        result = subprocess.run(["forge", "build"], capture_output=True, cwd=os.path.dirname(contract_path))
        std_out = result.stdout.decode()
        std_err = result.stderr.decode()

        if "successful" in std_out or 'compilation skipped' in std_out:
            json_res = {"status": True, "message": "Compile successful!"}
        else:
            raise Exception(f"Couldn't compile code with error: {std_err}")
    except Exception as e:
        json_res = {"status": False, "message": e}
        bt.logging.info(f"got exception: {e}")
    finally:
        if os.path.exists(contract_path) and os.path.isfile(contract_path):
            os.remove(contract_path)

        return json_res


def reward(uid: str, query: str, response: str) -> float:
    """
    Reward the miner response to the prompt. This method returns a reward
    value for the miner, which is used to update the miner's score.

    Returns:
    - float: The reward value for the miner.
    """
    compile_result = compile_solidity_code(uid, response)

    return 1.0 if compile_result["status"] else 0


def get_rewards(
    self,
    uid: str,
    query: str,
    responses: List[str],
) -> torch.FloatTensor:
    """
    Returns a tensor of rewards for the given query and responses.

    Args:
    - query (str): The query sent to the miner.
    - responses (List[str]): A list of responses from the miner.

    Returns:
    - torch.FloatTensor: A tensor of rewards for the given query and responses.
    """
    # Get all the reward results by iteratively calling your reward() function.
    return torch.FloatTensor(
        [reward(uid, query, response) for response in responses]
    ).to(self.device)
