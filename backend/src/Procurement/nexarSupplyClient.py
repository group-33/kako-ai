# https://github.com/NexarDeveloper/nexar-examples-py/blob/main/examplePrograms/nexarClients/supply/nexarSupplyClient.py

"""MIT License

Copyright (c) 2022 Altium LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

"""Resources for making Nexar requests."""

import requests
import base64
import json
import time
import os
import random
from typing import Dict

NEXAR_URL = "https://api.nexar.com/graphql"
PROD_TOKEN_URL = "https://identity.nexar.com/connect/token"


def get_token(client_id, client_secret):
    """Return the Nexar token from the client_id and client_secret provided."""

    if not client_id or not client_secret:
        raise Exception("client_id and/or client_secret are empty")

    token = {}
    try:
        token = requests.post(
            url=PROD_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            allow_redirects=False,
        ).json()

    except Exception:
        raise

    return token


def decodeJWT(token):
    return json.loads(
        (base64.urlsafe_b64decode(token.split(".")[1] + "==")).decode("utf-8")
    )


class NexarClient:
    def __init__(self, id, secret, is_live=True) -> None:
        self.id = id
        self.secret = secret
        self.is_live = is_live
        self.cache_file = os.path.join(
            os.path.dirname(__file__), "cached_responses.json"
        )

        if is_live:
            self.s = requests.session()
            self.s.keep_alive = False
            self.token = get_token(id, secret)
            self.s.headers.update({"token": self.token.get("access_token")})
            self.exp = decodeJWT(self.token.get("access_token")).get("exp")
        else:
            self.s = None
            self.token = None
            self.exp = None

    def check_exp(self):
        if self.exp < time.time() + 300:
            self.token = get_token(self.id, self.secret)
            self.s.headers.update({"token": self.token.get("access_token")})
            self.exp = decodeJWT(self.token.get("access_token")).get("exp")

    def get_query(self, query: str, variables: Dict) -> dict:
        """Return Nexar response for the query."""
        if not self.is_live:
            return self._get_mock_response(variables)

        try:
            self.check_exp()
            r = self.s.post(
                NEXAR_URL,
                json={"query": query, "variables": variables},
            )

        except Exception as e:
            print(e)
            raise Exception("Error while getting Nexar response")

        response = r.json()
        if "errors" in response:
            for error in response["errors"]:
                print(error["message"])
            raise SystemExit

        return response["data"]

    def _get_mock_response(self, variables: Dict) -> dict:
        """Return a mock response from cached data."""
        try:
            with open(self.cache_file, "r") as f:
                cached_responses = json.load(f)
        except FileNotFoundError:
            print(
                f"Warning: Cache file not found at {self.cache_file}. Returning empty response."
            )
            return {"supMultiMatch": []}
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in cache file. Returning empty response.")
            return {"supMultiMatch": []}

        if not cached_responses:
            print("Warning: No cached responses available. Returning empty response.")
            return {"supMultiMatch": []}

        # Pick a random cached response
        cached_entry = random.choice(cached_responses)
        response = json.loads(json.dumps(cached_entry["response"]))  # Deep copy

        # Swap MPNs if variables contain queries
        if "queries" in variables:
            requested_mpns = [
                q.get("mpnOrSku") or q.get("mpn") for q in variables["queries"]
            ]
            response = self._swap_mpns_in_response(response, requested_mpns)

        return response

    def _swap_mpns_in_response(self, response: dict, requested_mpns: list) -> dict:
        """Swap MPNs in the cached response with requested MPNs."""
        if "supMultiMatch" in response:
            matches = response["supMultiMatch"]
            for i, match in enumerate(matches):
                if i < len(requested_mpns) and match.get("parts"):
                    for part in match["parts"]:
                        part["mpn"] = requested_mpns[i]

        return response
