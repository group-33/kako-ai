import sys
import json
from nexarSupplyClient import NexarClient

NEXAR_CLIENT_ID = "" #todo
NEXAR_CLIENT_SECRET = "" #todo
DEFAULT_QUERY = """
query ($mpn: String!) {
  supSearchMpn(
    q: $mpn
    limit: 1
  ){
    results {
      part {
        category {
          parentId
          id
          name
          path
        }
        mpn
        manufacturer {
          name
        }
        shortDescription
        descriptions {
          text
          creditString
        }
        specs {
          attribute {
            name
            shortname
          }
          displayValue
        }
      }
    }
  }
}
"""

def setup_api():
    client = NexarClient(NEXAR_CLIENT_ID, NEXAR_CLIENT_SECRET)
    print("API setup complete.")
    return client

def request_api(client, variables, query=DEFAULT_QUERY):
    data = client.get_query(query, variables)
    print(json.dumps(data["supSearchMpn"], indent=1))
    return data

if __name__ == "__main__":
    client = setup_api()
    mpn = input("Enter a MPN: ")
    if not mpn:
        sys.exit()
    variables = {
        "mpn": mpn
    }
    request_api(client, variables, DEFAULT_QUERY)