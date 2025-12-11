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
import hashlib
import copy
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
    def __init__(self, id, secret, is_live=True, enable_caching=True) -> None:
        self.id = id
        self.secret = secret
        self.is_live = is_live
        self.enable_caching = enable_caching
        self.cache_file = os.path.join(
            os.path.dirname(__file__), "cached_responses.json"
        )
        self.persistent_cache_file = os.path.join(
            os.path.dirname(__file__), "persistent_cache.json"
        )
        self.persistent_cache = self._load_persistent_cache()

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

    def _load_persistent_cache(self) -> dict:
        """Load the persistent cache from disk."""
        try:
            with open(self.persistent_cache_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_persistent_cache(self):
        """Save the persistent cache to disk."""
        try:
            with open(self.persistent_cache_file, "w") as f:
                json.dump(self.persistent_cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

    def _get_query_hash(self, query: str) -> str:
        """Generate a unique hash for the query."""
        return hashlib.sha256(query.encode("utf-8")).hexdigest()

    def _get_variables_hash(self, variables: Dict) -> str:
        """Generate a unique hash for the variables."""
        # Canonicalize variables by sorting keys
        serialized_vars = json.dumps(variables, sort_keys=True)
        return hashlib.sha256(serialized_vars.encode("utf-8")).hexdigest()

    def get_query(self, query: str, variables: Dict) -> dict:
        """Return Nexar response for the query."""

        query_hash = self._get_query_hash(query)
        variables_hash = self._get_variables_hash(variables)

        # 1. Check persistent cache first if enabled
        if self.enable_caching:
            if query_hash in self.persistent_cache:
                if variables_hash in self.persistent_cache[query_hash]:
                    return self.persistent_cache[query_hash][variables_hash]

        # 2. If not in cache and not live, use mock fallback
        if not self.is_live:
            # Try to find ANY entry for this query in persistent cache
            if (
                query_hash in self.persistent_cache
                and self.persistent_cache[query_hash]
            ):
                # Pick random entry
                random_var_hash = random.choice(
                    list(self.persistent_cache[query_hash].keys())
                )
                cached_data = copy.deepcopy(
                    self.persistent_cache[query_hash][random_var_hash]
                )

                # Swap MPNs to make it "realistic"
                if "queries" in variables:
                    requested_mpns = [
                        q.get("mpnOrSku") or q.get("mpn") for q in variables["queries"]
                    ]
                    return self._swap_mpns_in_response(cached_data, requested_mpns)
                return cached_data

            print("Warning: No cached data found in persistent cache for this query.")
            return {"supMultiMatch": []}

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

        # 3. Save to persistent cache if enabled
        data = response["data"]
        if self.enable_caching:
            if query_hash not in self.persistent_cache:
                self.persistent_cache[query_hash] = {}

            self.persistent_cache[query_hash][variables_hash] = data
            self._save_persistent_cache()

        return data

    def _swap_mpns_in_response(self, response: dict, requested_mpns: list) -> dict:
        """Swap MPNs in the cached response with requested MPNs."""
        if "supMultiMatch" in response:
            matches = response["supMultiMatch"]
            for i, match in enumerate(matches):
                if i < len(requested_mpns) and match.get("parts"):
                    for part in match["parts"]:
                        part["mpn"] = requested_mpns[i]

        return response
