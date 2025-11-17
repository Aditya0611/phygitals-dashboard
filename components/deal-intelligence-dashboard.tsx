"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { TrendingUp, DollarSign, Star, AlertTriangle, ExternalLink, RefreshCw } from 'lucide-react'
import { formatCurrency, parsePriceValue } from '@/lib/utils'

interface DealIntelligence {
  summary: {
    total_cards_analyzed: number
    total_deals_found: number
    crazy_deals: number
    excellent_deals: number
    tier_counts: Record<string, number>
    last_updated: string
  }
  top_crazy_deals: Array<{
    deal_score: number
    deal_tier: string
    absolute_savings: number
    savings_percentage: number
    upside_potential: number
    market_momentum: string
    current_price: string
    fmv: string
    pokemon_name: string
    grader: string
    grade: string
    listing_url: string
  }>
  top_excellent_deals: Array<{
    deal_score: number
    deal_tier: string
    absolute_savings: number
    savings_percentage: number
    upside_potential: number
    market_momentum: string
    current_price: string
    fmv: string
    pokemon_name: string
    grader: string
    grade: string
    listing_url: string
  }>
  tiered_deals: Record<string, Array<any>>
}

export default function DealIntelligenceDashboard() {
  const [intelligence, setIntelligence] = useState<DealIntelligence | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<string>('')
  // Tabs removed to avoid missing dependency; render sections directly

  useEffect(() => {
    fetchIntelligence()
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchIntelligence()
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchIntelligence = async (force = false) => {
    setLoading(true)
    try {
      // Add cache-busting timestamp to ensure fresh data
      const timestamp = new Date().getTime()
      const random = Math.random().toString(36).substring(7)
      const url = `/api/deal-intelligence?t=${timestamp}&r=${random}${force ? '&force=1' : ''}`
      
      const res = await fetch(url, {
        method: 'GET',
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        },
        next: { revalidate: 0 }
      })
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }
      
      const result = await res.json()
      if (result.success) {
        console.log('Deal intelligence fetched:', {
          lastUpdated: result.lastUpdated,
          fileMtime: result.fileMtime,
          crazyDeals: result.data?.summary?.crazy_deals,
          excellentDeals: result.data?.summary?.excellent_deals
        })
        setIntelligence(result.data)
        setLastUpdated(result.lastUpdated || result.fileMtime || new Date().toISOString())
      } else {
        console.error('Failed to fetch deal intelligence:', result.error)
      }
    } catch (error) {
      console.error('Error fetching deal intelligence:', error)
    } finally {
      setLoading(false)
    }
  }

  const getDealTierColor = (tier: string) => {
    switch (tier) {
      case 'CRAZY DEAL': return 'bg-red-500 text-white'
      case 'EXCELLENT DEAL': return 'bg-orange-500 text-white'
      case 'GOOD DEAL': return 'bg-green-500 text-white'
      case 'FAIR DEAL': return 'bg-blue-500 text-white'
      default: return 'bg-gray-500 text-white'
    }
  }

  const getMomentumColor = (momentum: string) => {
    switch (momentum) {
      case 'HIGH': return 'text-red-600'
      case 'MEDIUM': return 'text-orange-600'
      case 'LOW': return 'text-green-600'
      default: return 'text-gray-600'
    }
  }

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Deal Intelligence Dashboard</CardTitle>
          <CardDescription>Loading intelligence analysis...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            Loading...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!intelligence) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Deal Intelligence Dashboard</CardTitle>
          <CardDescription>No intelligence data available.</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Please run the deal intelligence system first.</p>
        </CardContent>
      </Card>
    )
  }

  const { summary, top_crazy_deals = [], top_excellent_deals = [], tiered_deals = {} } = intelligence || {}

  return (
    <div className="space-y-6">
      {/* Header with refresh button */}
      <div className="flex justify-between items-center border-b pb-4">
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent">
            🔥 Deal Intelligence Dashboard
          </h2>
          {lastUpdated && (
            <p className="text-sm text-muted-foreground mt-1">
              Last updated: {new Date(lastUpdated).toLocaleString()}
            </p>
          )}
        </div>
        <Button onClick={() => fetchIntelligence(true)} variant="outline" size="sm" disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Deals</p>
                <p className="text-2xl font-bold">{summary?.total_deals_found || 0}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">CRAZY DEALS</p>
                <p className="text-2xl font-bold text-red-600">{summary?.crazy_deals || 0}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">EXCELLENT DEALS</p>
                <p className="text-2xl font-bold text-orange-600">{summary?.excellent_deals || 0}</p>
              </div>
              <Star className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Cards Analyzed</p>
                <p className="text-2xl font-bold">{summary?.total_cards_analyzed || 0}</p>
              </div>
              <DollarSign className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* CRAZY DEALS */}
      <div className="w-full space-y-4">
        <Card className="border-2 border-red-500 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-red-50 to-red-100">
              <CardTitle className="text-2xl font-bold text-red-600 flex items-center gap-2">
                <span className="text-3xl">🚨</span>
                CRAZY DEALS - Don&rsquo;t Miss These!
              </CardTitle>
              <CardDescription className="text-base font-medium">
                Highest scoring deals with massive upside potential (All cards above $50)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {top_crazy_deals.length > 0 ? (
                <div className="space-y-4">
                  {top_crazy_deals.map((deal, index) => (
                    <Card key={index} className="border-l-4 border-l-red-500 bg-red-50">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge className={getDealTierColor(deal.deal_tier)}>
                                {deal.deal_tier}
                              </Badge>
                              <Badge variant="outline">
                                Score: {deal.deal_score}
                              </Badge>
                              <span className={`text-sm font-medium ${getMomentumColor(deal.market_momentum)}`}>
                                {deal.market_momentum} Momentum
                              </span>
                            </div>
                            
                            <h3 className="font-semibold text-lg mb-2">
                              {deal.pokemon_name} {deal.grader} {deal.grade}
                            </h3>
                            
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              <div>
                                <span className="text-muted-foreground">Current Price:</span>
                                <span className="ml-2 font-medium">
                                  {formatCurrency(deal.current_price)}
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">FMV:</span>
                                <span className="ml-2 font-medium">
                                  {formatCurrency(deal.fmv)}
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Upside:</span>
                                <span className="ml-2 font-medium text-green-600">
                                  {formatCurrency(deal.upside_potential)} ({deal.savings_percentage.toFixed(1)}%)
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Potential:</span>
                                <span className="ml-2 font-medium text-red-600">
                                  {formatCurrency(
                                    (parsePriceValue(deal.fmv) ?? 0) + (deal.upside_potential ?? 0)
                                  )}
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="ml-4">
                            <Button asChild variant="outline" size="sm">
                              <a href={deal.listing_url} target="_blank" rel="noopener noreferrer">
                                <ExternalLink className="h-4 w-4 mr-2" />
                                View Deal
                              </a>
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-muted-foreground">No CRAZY DEALS found in current data</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Run the high-value scraper to find premium deals
                  </p>
                </div>
              )}
            </CardContent>
        </Card>

        {/* EXCELLENT DEALS */}
        <Card className="border-2 border-orange-500 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-orange-50 to-orange-100">
              <CardTitle className="text-2xl font-bold text-orange-600 flex items-center gap-2">
                <span className="text-3xl">⭐</span>
                EXCELLENT DEALS - Strong Opportunities
              </CardTitle>
              <CardDescription className="text-base font-medium">
                High-scoring deals with significant upside potential (All cards above $50)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {top_excellent_deals.length > 0 ? (
                <div className="space-y-4">
                  {top_excellent_deals.map((deal, index) => (
                    <Card key={index} className="border-l-4 border-l-orange-500 bg-orange-50">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge className={getDealTierColor(deal.deal_tier)}>
                                {deal.deal_tier}
                              </Badge>
                              <Badge variant="outline">
                                Score: {deal.deal_score}
                              </Badge>
                              <span className={`text-sm font-medium ${getMomentumColor(deal.market_momentum)}`}>
                                {deal.market_momentum} Momentum
                              </span>
                            </div>
                            
                            <h3 className="font-semibold text-lg mb-2">
                              {deal.pokemon_name} {deal.grader} {deal.grade}
                            </h3>
                            
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              <div>
                                <span className="text-muted-foreground">Current Price:</span>
                                <span className="ml-2 font-medium">
                                  {formatCurrency(deal.current_price)}
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">FMV:</span>
                                <span className="ml-2 font-medium">
                                  {formatCurrency(deal.fmv)}
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Upside:</span>
                                <span className="ml-2 font-medium text-green-600">
                                  {formatCurrency(deal.upside_potential)} ({deal.savings_percentage.toFixed(1)}%)
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Potential:</span>
                                <span className="ml-2 font-medium text-orange-600">
                                  {formatCurrency(
                                    (parsePriceValue(deal.fmv) ?? 0) + (deal.upside_potential ?? 0)
                                  )}
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="ml-4">
                            <Button asChild variant="outline" size="sm">
                              <a href={deal.listing_url} target="_blank" rel="noopener noreferrer">
                                <ExternalLink className="h-4 w-4 mr-2" />
                                View Deal
                              </a>
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Star className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-muted-foreground">No EXCELLENT DEALS found in current data</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Focus on higher-value cards for better opportunities
                  </p>
                </div>
              )}
            </CardContent>
        </Card>
      </div>

      {/* Price Tier Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Deals by Price Tier</CardTitle>
          <CardDescription>Distribution of deals across different price ranges</CardDescription>
        </CardHeader>
        <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(summary?.tier_counts || {}).map(([tier, count]) => (
              <div key={tier} className="text-center p-4 border rounded-lg">
                <p className="text-sm text-muted-foreground">{tier}</p>
                <p className="text-2xl font-bold">{count}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
