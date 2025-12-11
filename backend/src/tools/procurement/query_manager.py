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

# Full GraphQL query for multiple MPNs
# (no self references eg. parents/children; no similar parts; no cad or sim models; no content vault details; no extras; no internal info)
MULTI_QUERY_FULL = """
query GetParts(
  $queries: [SupPartMatchQuery!]!,
  $country: String!,
  $currency: String!
) {
  supMultiMatch (
    queries: $queries,
    country: $country,
    currency: $currency
  ) {
    hits
    parts {
      id
      name
      mpn
      genericMpn
      manufacturer {
        id
        name
        aliases
        displayFlag
        homepageUrl
        slug
        isVerified
        isDistributorApi
        isOctocartSupported
      }
      manufacturerUrl
      documentCollections {
        name
        documents {
          name
          url
        }
      }
      shortDescription
      descriptions {
        text
      }
      images {
        url
      }
      specs {
        attribute {
          id
          name
          group
        }
        value
        valueType
        displayValue
      }
      octopartUrl
      companionProducts {
        url
      }
      category {
        id
        parentId
        name
        path
      }
      series {
        id
        name
        url
      }
      bestImage {
        url
      }
      bestDatasheet {
        name
        url
      }
      referenceDesigns {
        name
        url
      }
      counts
      medianPrice1000 {
        quantity
        price
        currency
        convertedPrice
        convertedCurrency
        conversionRate
      }
      totalAvail
      avgAvail
      sellers {
        company {
          id
          name
          aliases
          displayFlag
          homepageUrl
          slug
          isVerified
          isDistributorApi
          isOctocartSupported
        }
        country
        offers {
          id
          sku
          eligibleRegion
          inventoryLevel
          moq
          prices {
            quantity
            price
            currency
            convertedPrice
            convertedCurrency
            conversionRate
          }
          clickUrl
          updated
          factoryLeadDays
          onOrderQuantity
          factoryPackQuantity
          orderMultiple
          multipackQuantity
        }
        isAuthorized
        isBroker
        shipsToCountries {
          name
          countryCode
          continentCode
        }
      }
      estimatedFactoryLeadDays
      akaMpns
    }
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
