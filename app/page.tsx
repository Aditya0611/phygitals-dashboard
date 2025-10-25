"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/data-table'
import { StatsCards } from '@/components/stats-cards'
import AdvancedFilters from '@/components/advanced-filters'
// import PSAAltXYZIntegration from '@/components/psa-alt-xyz-integration'
import { CardData } from '@/components/data-table'
import { RefreshCw, Download, Calendar, Database } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export default function Dashboard() {
  const [data, setData] = useState<CardData[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<string>('')
  const [scrapingStatus, setScrapingStatus] = useState<'idle' | 'running' | 'completed'>('idle')

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/data')
      const result = await response.json()
      setData(result.data || [])
      setLastUpdated(result.lastUpdated || '')
      setScrapingStatus(result.scrapingStatus || 'idle')
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const startScraping = async () => {
    try {
      setScrapingStatus('running')
      const response = await fetch('/api/scrape', { method: 'POST' })
      const result = await response.json()
      if (result.success) {
        // Refresh data after a short delay
        setTimeout(fetchData, 2000)
      }
    } catch (error) {
      console.error('Error starting scraping:', error)
      setScrapingStatus('idle')
    }
  }

  const downloadData = () => {
    const csvContent = [
      ['Card Name', 'Grader', 'Grade', 'Price', 'FMV', 'Pokemon', 'Set', 'Number', 'URL'],
      ...data.map(card => [
        card.full_listing_name,
        card.grader,
        card.grade,
        card.current_price,
        card.fmv,
        card.pokemon_name,
        card.card_set,
        card.card_number,
        card.listing_url
      ])
    ].map(row => row.join(',')).join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `phygitals-data-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  useEffect(() => {
    fetchData()
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Phygitals Marketplace</h1>
          <p className="text-muted-foreground">
            Real-time Pokemon card marketplace data and analytics
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={scrapingStatus === 'running' ? 'default' : 'secondary'}>
            {scrapingStatus === 'running' ? 'Scraping...' : 'Idle'}
          </Badge>
          <Button onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <StatsCards data={data} />

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Database className="h-5 w-5 mr-2" />
            Data Management
          </CardTitle>
          <CardDescription>
            Manage your marketplace data collection and downloads
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium">Last Updated</p>
              <p className="text-sm text-muted-foreground">
                {lastUpdated ? formatDate(lastUpdated) : 'Never'}
              </p>
            </div>
            <div className="flex space-x-2">
              <Button 
                onClick={startScraping} 
                disabled={scrapingStatus === 'running'}
                variant="outline"
              >
                <Calendar className="h-4 w-4 mr-2" />
                Start Scraping
              </Button>
              <Button onClick={downloadData} disabled={data.length === 0}>
                <Download className="h-4 w-4 mr-2" />
                Download CSV
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Filters */}
      <AdvancedFilters />

      {/* PSA Certificate & Alt.xyz Integration */}
      {/* <PSAAltXYZIntegration /> */}

      {/* Data Table */}
      <Card>
        <CardHeader>
          <CardTitle>Marketplace Cards</CardTitle>
          <CardDescription>
            {data.length.toLocaleString()} cards found in the marketplace
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <RefreshCw className="h-6 w-6 animate-spin mr-2" />
              Loading data...
            </div>
          ) : (
            <DataTable data={data} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
