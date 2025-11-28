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
