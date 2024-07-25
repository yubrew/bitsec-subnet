import os
import bittensor as bt
import random
import uvicorn
import asyncio

from datetime import datetime
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from typing import List, Any, Annotated

from protocol.api.llm_solidity import LLMSolidityGenAPI, TextGenerationInput

async def main():
    app = FastAPI()

    async with LLMSolidityGenAPI() as client:
        @app.post("/api/generate")
        async def generate(input_parameters: Annotated[TextGenerationInput, Body()]) -> List[str]:
            """
            Option 1. User -> Validator API -> Top 5 Miners -> User
            pros:
            - with high probability, ensures respnses from miners are working
            - less complex
            cons:
            - vector weights aren't updated
            - limits the potential miners that users encounters

            Option 2. User -> Validator API -> Validators -> (Random or best) Miners -> Validators -> User
            pros:
            - ensures 100% that response will work
            - updates weights of miners
            cons:
            - complexity increase: smart mechanism to select miners (instead of random)
            - increases latency for responses to users
            """
            # TODO(Idris): Return top 5 miners
            all_axons = client.get_all_axons()
            res = await client.query_api(input_parameters, all_axons)
            return res

        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", str(8000))))

if __name__ == "__main__":
    asyncio.run(main())
