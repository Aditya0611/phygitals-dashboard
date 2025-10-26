"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface FilteredData {
  summary: {
    total_cards: number
    deals_found: number
    high_value_cards: number
    psa_cards: number
    price_range_10_plus: number
    fmv_25_plus: number
    top_pokemon: [string, number][]
  }
  deals: any[]
  high_value_cards: any[]
  all_cards: any[]
  price_range_10_plus: any[]
  fmv_25_plus: any[]
  psa_cards_with_certificates: any[]
  alt_xyz_integration: any
  pokemon_breakdown: Record<string, number>
}

export default function AdvancedFilters() {
  const [filteredData, setFilteredData] = useState<FilteredData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedFilter, setSelectedFilter] = useState('deals')
  const [searchTerm, setSearchTerm] = useState('')
  const [minValue, setMinValue] = useState(250)

  useEffect(() => {
    fetchFilteredData()
  }, [])

  const fetchFilteredData = async () => {
    try {
      const response = await fetch('/api/filtered-data')
      if (response.ok) {
        const data = await response.json()
        setFilteredData(data.data)
      }
    } catch (error) {
      console.error('Error fetching filtered data:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatPrice = (price: string) => {
    if (!price || price === 'N/A') return 'N/A'
    return price
  }

  const parsePrice = (price: string) => {
    if (!price || price === 'N/A') return 0
    return parseFloat(price.replace(/[^\d.]/g, ''))
  }

  const getFilteredCards = () => {
    if (!filteredData) return []
    
    let cards = []
    switch (selectedFilter) {
      case 'deals':
        cards = filteredData.deals
        break
      case 'all_cards':
        cards = filteredData.all_cards
        break
      case 'high_value':
        cards = filteredData.high_value_cards
        break
      case 'price_range_10_plus':
        cards = filteredData.price_range_10_plus
        break
      case 'fmv_25_plus':
        cards = filteredData.fmv_25_plus
        break
      case 'psa':
        cards = filteredData.psa_cards_with_certificates
        break
      default:
        cards = []
    }

    // Apply search filter
    if (searchTerm) {
      cards = cards.filter((card: any) =>
        card.full_listing_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        card.pokemon_name?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    return cards.slice(0, 20) // Show top 20 results
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading filtered data...</p>
        </div>
      </div>
    )
  }

  if (!filteredData) {
    return (
      <div className="text-center p-8">
        <p className="text-red-600">No filtered data available. Please run the filtering system first.</p>
        <Button onClick={fetchFilteredData} className="mt-4">
          Retry
        </Button>
      </div>
    )
  }

  const cards = getFilteredCards()

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Cards</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{filteredData.summary.total_cards}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Deals Found</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{filteredData.summary.deals_found}</div>
            <p className="text-xs text-muted-foreground">FMV &gt; Current Price</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">High Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{filteredData.summary.high_value_cards}</div>
            <p className="text-xs text-muted-foreground">Price &amp; FMV &gt; $25</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Price Range ($10+)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{filteredData.summary.price_range_10_plus}</div>
            <p className="text-xs text-muted-foreground">Cards $10 and above</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">FMV Starting Point</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-teal-600">{filteredData.summary.fmv_25_plus}</div>
            <p className="text-xs text-muted-foreground">FMV $25 and above</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">PSA Cards (Preferred)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{filteredData.summary.psa_cards}</div>
            <p className="text-xs text-muted-foreground">With Certificates</p>
          </CardContent>
        </Card>
      </div>

      {/* Filter Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Advanced Filters</CardTitle>
          <CardDescription>Filter cards by your specific criteria</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-4">
            <Select value={selectedFilter} onValueChange={setSelectedFilter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select filter type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all_cards">All Cards</SelectItem>
                <SelectItem value="deals">Deals (FMV &gt; Price)</SelectItem>
                <SelectItem value="high_value">High Value (&gt;$25)</SelectItem>
                <SelectItem value="price_range_10_plus">Price Range ($10+)</SelectItem>
                <SelectItem value="fmv_25_plus">FMV Starting Point ($25+)</SelectItem>
                <SelectItem value="psa">PSA Cards (Preferred)</SelectItem>
              </SelectContent>
            </Select>
            
            <Input
              placeholder="Search Pokemon names..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-[250px]"
            />
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedFilter === 'deals' && 'Best Deals'}
            {selectedFilter === 'high_value' && 'High-Value Cards'}
            {selectedFilter === 'psa' && 'PSA Graded Cards'}
          </CardTitle>
          <CardDescription>
            Showing {cards.length} results
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {cards.map((card: any, index: number) => (
              <div key={index} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-medium text-sm mb-2 line-clamp-2">
                      {card.full_listing_name}
                    </h3>
                    
                    <div className="flex flex-wrap gap-2 mb-2">
                      <Badge variant="outline">{card.grader} {card.grade}</Badge>
                      {card.pokemon_name && (
                        <Badge variant="secondary">{card.pokemon_name}</Badge>
                      )}
                      {selectedFilter === 'psa' && (
                        <Badge variant="default">PSA Certificate</Badge>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Current Price:</span>
                        <span className="ml-2 font-medium">{formatPrice(card.current_price)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">FMV:</span>
                        <span className="ml-2 font-medium">{formatPrice(card.fmv)}</span>
                      </div>
                    </div>
                    
                    {selectedFilter === 'deals' && card.potential_savings && (
                      <div className="mt-2 p-2 bg-green-50 rounded">
                        <div className="text-green-700 font-medium">
                          💰 Potential Savings: ${card.potential_savings.toFixed(2)} 
                          ({card.savings_percentage.toFixed(1)}%)
                        </div>
                      </div>
                    )}
                    
                    {selectedFilter === 'psa' && card.psa_certificate_number && (
                      <div className="mt-2 p-2 bg-blue-50 rounded">
                        <div className="text-blue-700 font-medium text-sm">
                          📋 PSA Certificate: {card.psa_certificate_number}
                        </div>
                      </div>
                    )}
                    
                    {/* Always show listing URL for deals */}
                    {selectedFilter === 'deals' && card.listing_url && (
                      <div className="mt-2">
                        <a 
                          href={card.listing_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline text-sm"
                        >
                          🔗 View Listing →
                        </a>
                      </div>
                    )}
                  </div>
                  
                  <div className="text-right">
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => window.open(card.listing_url, '_blank')}
                    >
                      View Details
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            
            {cards.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No cards found matching your criteria.
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Alt.xyz Integration Info */}
      <Card>
        <CardHeader>
          <CardTitle>Alt.xyz Integration</CardTitle>
          <CardDescription>FMV data source and integration possibilities</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Integration Possibilities:</h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                <li>Direct API integration with Alt.xyz for real-time FMV data</li>
                <li>Web scraping Alt.xyz for historical sales data</li>
                <li>Batch processing to get FMV for all cards</li>
                <li>Real-time price comparison between Phygitals and Alt.xyz</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">FMV Data Sources:</h4>
              <p className="text-sm text-muted-foreground">
                {filteredData.alt_xyz_integration.fmv_sources.length} cards have FMV data available
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
