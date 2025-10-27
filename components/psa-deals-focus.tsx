"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, TrendingUp, DollarSign, Target } from 'lucide-react'

interface PSADeal {
  name: string
  price: number
  fmv: number
  savings: number
  savings_pct: number
  cert: string
  url: string
  grade: string
}

interface PSADealsData {
  affordable_deals: PSADeal[]
  premium_deals: PSADeal[]
  all_psa_deals: PSADeal[]
  summary: {
    total_psa_cards: number
    psa_deals_found: number
    affordable_count: number
    premium_count: number
  }
}

export default function PSADealsFocus() {
  const [psaData, setPsaData] = useState<PSADealsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedRange, setSelectedRange] = useState<'affordable' | 'premium'>('affordable')

  useEffect(() => {
    fetchPSADeals()
  }, [])

  const fetchPSADeals = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/psa-deals')
      const result = await res.json()
      if (result.success) {
        setPsaData(result.data)
      } else {
        console.error('Failed to fetch PSA deals:', result.error)
      }
    } catch (error) {
      console.error('Error fetching PSA deals:', error)
    } finally {
      setLoading(false)
    }
  }

  const getCurrentDeals = () => {
    if (!psaData) return []
    return selectedRange === 'affordable' ? psaData.affordable_deals : psaData.premium_deals
  }

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>PSA Deals Focus</CardTitle>
          <CardDescription>Loading PSA deals analysis...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            Loading...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!psaData) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>PSA Deals Focus</CardTitle>
          <CardDescription>No PSA deals data available.</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Please run the PSA analysis first.</p>
        </CardContent>
      </Card>
    )
  }

  const currentDeals = getCurrentDeals()

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total PSA Cards</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{psaData.summary.total_psa_cards}</div>
            <p className="text-xs text-muted-foreground">PSA graded cards</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">PSA Deals Found</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{psaData.summary.psa_deals_found}</div>
            <p className="text-xs text-muted-foreground">FMV &gt; Price</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Affordable Deals</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{psaData.summary.affordable_count}</div>
            <p className="text-xs text-muted-foreground">$10-$15 range</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Premium Deals</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{psaData.summary.premium_count}</div>
            <p className="text-xs text-muted-foreground">$100-$300 range</p>
          </CardContent>
        </Card>
      </div>

      {/* Range Selector */}
      <Card>
        <CardHeader>
          <CardTitle>PSA Deals Focus</CardTitle>
          <CardDescription>Select your target price range for PSA cards</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button
              variant={selectedRange === 'affordable' ? 'default' : 'outline'}
              onClick={() => setSelectedRange('affordable')}
              className="flex items-center gap-2"
            >
              <DollarSign className="h-4 w-4" />
              Affordable ($10-$15) - Mass Accumulation
            </Button>
            <Button
              variant={selectedRange === 'premium' ? 'default' : 'outline'}
              onClick={() => setSelectedRange('premium')}
              className="flex items-center gap-2"
            >
              <DollarSign className="h-4 w-4" />
              Premium ($100-$300) - High Value
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Deals Display */}
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedRange === 'affordable' ? 'Affordable PSA Deals ($10-$15)' : 'Premium PSA Deals ($100-$300)'}
          </CardTitle>
          <CardDescription>
            {currentDeals.length} PSA cards with FMV &gt; Current Price
            {selectedRange === 'affordable' && ' - Perfect for mass accumulation'}
            {selectedRange === 'premium' && ' - High-value investments'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {currentDeals.length > 0 ? (
            <div className="space-y-4">
              {currentDeals.map((deal, index) => (
                <Card key={index} className="border-l-4 border-l-green-500">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="secondary">PSA {deal.grade}</Badge>
                          <Badge variant="outline">Cert: {deal.cert || 'N/A'}</Badge>
                        </div>
                        
                        <h3 className="font-medium text-sm mb-2 line-clamp-2">
                          {deal.name}
                        </h3>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm mb-3">
                          <div>
                            <span className="text-muted-foreground">Current Price:</span>
                            <span className="ml-2 font-medium">${deal.price.toFixed(2)}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">FMV:</span>
                            <span className="ml-2 font-medium">${deal.fmv.toFixed(2)}</span>
                          </div>
                        </div>
                        
                        <div className="p-3 bg-green-50 rounded-lg">
                          <div className="text-green-700 font-medium">
                            💰 Potential Savings: ${deal.savings.toFixed(2)} ({deal.savings_pct.toFixed(1)}%)
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right ml-4">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => window.open(deal.url, '_blank')}
                          className="flex items-center gap-2"
                        >
                          <ExternalLink className="h-4 w-4" />
                          View Listing
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p className="text-lg font-medium">No PSA deals found in this range</p>
              <p className="text-sm">
                {selectedRange === 'premium' 
                  ? 'Need to scrape more high-value PSA cards ($100+)'
                  : 'All PSA cards in this range are priced correctly'
                }
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
