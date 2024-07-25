# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 Idris Hanafi
# Copyright © 2024 [Your Name]

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import typing
from typing import List, Dict, Optional
import bittensor as bt

class LLMSecurityGen(bt.Synapse):
    """
    An LLM Security Generator protocol which uses bt.Synapse as its base.
    This protocol helps in handling LLM Security analysis request and response communication between
    the miner and the validator.

    Attributes:
    - solidity_input: A string value representing the Solidity code input sent by the validator.
    - vulnerabilities: A list of strings representing identified vulnerabilities in the code.
    - fixes: A list of strings representing suggested fixes for the identified vulnerabilities.
    """

    # Required request input, filled by sending dendrite caller.
    solidity_input: str = ""

    # Optional request outputs, filled by receiving axon.
    vulnerabilities: Optional[List[str]] = None
    fixes: Optional[List[str]] = None

    def deserialize(self) -> Dict[str, typing.Union[str, List[str]]]:
        """
        Deserialize the security analysis output. This method retrieves the response from
        the miner in the form of vulnerabilities and fixes, deserializes it and returns it
        as the output of the dendrite.query() call.

        Returns:
        - Dict[str, Union[str, List[str]]]: A dictionary containing the original Solidity input,
          identified vulnerabilities, and suggested fixes.
        """
        return self.serialize()

    def serialize(self) -> Dict[str, typing.Union[str, List[str]]]:
        """
        Serialize the security analysis input and output. This method is used to prepare
        the data for transmission over the wire.

        Returns:
        - Dict[str, Union[str, List[str]]]: A dictionary containing the Solidity input,
          identified vulnerabilities, and suggested fixes.
        """
        return {
            "solidity_input": self.solidity_input,
            "vulnerabilities": self.vulnerabilities or [],
            "fixes": self.fixes or [],
        }

    @classmethod
    def deserialize_from_wire(cls, data: Dict[str, typing.Union[str, List[str]]]) -> 'LLMSecurityGen':
        """
        Deserialize the data received from the wire into an LLMSecurityGen object.

        Args:
        - data (Dict[str, Union[str, List[str]]]): The serialized data received from the wire.

        Returns:
        - LLMSecurityGen: An instance of the LLMSecurityGen class with the deserialized data.
        """
        instance = cls()
        instance.solidity_input = data.get("solidity_input", "")
        instance.vulnerabilities = data.get("vulnerabilities")
        instance.fixes = data.get("fixes")
        return instance

    def validate(self) -> bool:
        """
        Validate the LLMSecurityGen object to ensure all required fields are present and valid.

        Returns:
        - bool: True if the object is valid, False otherwise.
        """
        if not isinstance(self.solidity_input, str) or not self.solidity_input:
            return False
        if self.vulnerabilities is not None and not isinstance(self.vulnerabilities, list):
            return False
        if self.fixes is not None and not isinstance(self.fixes, list):
            return False
        if self.vulnerabilities is not None and self.fixes is not None:
            if len(self.vulnerabilities) != len(self.fixes):
                return False
        return True