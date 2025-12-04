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
# (no self references eg. parents/children; no similar parts; no cad or sim models; no content vault details; no extras)
MULTI_QUERY_FULL = """
query GetParts($queries: [SupPartMatchQuery!]!) {
  supMultiMatch (queries: $queries) {
    reference
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
        customPricingDetails {
          authType
        }
      }
      manufacturerUrl
      freeSampleUrl
      documentCollections {
        name
        documents {
          name
          pageCount
          createdAt
          url
          creditString
          creditUrl
          mimeType
        }
      }
      shortDescription
      descriptions {
        text
        creditString
        creditUrl
      }
      images {
        url
        creditString
        creditUrl
      }
      specs {
        attribute {
          id
          name
          shortname
          group
          valueType
          unitsName
          unitsSymbol
          shortDisplayname
        }
        value
        siValue
        valueType
        units
        unitsName
        unitsSymbol
        displayValue
      }
      slug
      octopartUrl
      companionProducts {
        _cacheId
        part
        url
      }
      category {
        id
        parentId
        name
        path
        relevantAttributes {
          id
          name
          shortname
          group
          valueType
          unitsName
          unitsSymbol
          shortDisplayname
        }
        blurb
        numParts
      }
      series {
        id
        name
        url
      }
      bestImage {
        url
        creditString
        creditUrl
      }
      bestDatasheet {
        name
        pageCount
        createdAt
        url
        creditString
        creditUrl
        mimeType
      }
      referenceDesigns {
        name
        url
      }
      v3uid
      counts
      medianPrice1000 {
        _cacheId
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
        _cacheId
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
          customPricingDetails {
            authType
          }
        }
        country
        offers {
          _cacheId
          id
          sku
          eligibleRegion
          inventoryLevel
          packaging
          moq
          prices {
            _cacheId
            quantity
            price
            currency
            convertedPrice
            convertedCurrency
            conversionRate
          }
          clickUrl
          internalUrl
          updated
          factoryLeadDays
          onOrderQuantity
          factoryPackQuantity
          orderMultiple
          multipackQuantity
          isCustomPricing
        }
        isAuthorized
        isBroker
        isRfq
        shipsToCountries {
          name
          countryCode
          continentCode
        }
      }
      estimatedFactoryLeadDays
      akaMpns
      altiumInternalId
      circuitMakerInternal {
        comments
        fabrications
        projects
        rates
        releases
      }
    }
    error
  }
}
"""