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

# Simplified query for multiple MPNs - based on DEFAULT_QUERY structure
MULTI_QUERY_FULL = """
query GetParts($queries: [SupPartMatchQuery!]!) {
  supMultiMatch (queries: $queries) {
    hits
    parts {
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
      category {
        parentId
        id
        name
        path
      }
      totalAvail
      sellers {
        company {
          name
          isVerified
        }
        isAuthorized
        offers {
          sku
          inventoryLevel
          moq
          prices {
            quantity
            convertedPrice
            convertedCurrency
          }
          factoryLeadDays
        }
      }
    }
    error
  }
}
"""

# Query for searching alternatives by category and description
SEARCH_BY_CATEGORY_QUERY = """
query SearchByCategory($description: String!) {
  supSearch(
    q: $description,
    limit: 3
  ) {
    hits
    results {
      part {
        id
        name
        mpn
        manufacturer {
          name
        }
        shortDescription
        category {
          id
          name
        }
        specs {
          attribute {
            name
            shortname
          }
          value
          displayValue
        }
        totalAvail
        sellers {
          company {
            name
            isVerified
          }
          offers {
            sku
            inventoryLevel
            moq
            prices {
              quantity
              convertedPrice
              convertedCurrency
            }
            factoryLeadDays
          }
          isAuthorized
        }
      }
    }
  }
}
"""
