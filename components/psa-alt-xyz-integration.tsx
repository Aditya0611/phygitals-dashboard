"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Certificate, DollarSign, TrendingUp } from 'lucide-react'

interface PSACard {
  card_name: string
  psa_certificate_number: string
  grader: string
  grade: string
  current_price: string
  fmv: string
  listing_url: string
  alt_xyz_urls: string[]
  primary_alt_xyz_url: string
  alt_xyz_integration_status: string
}

interface AltXYZData {
  psa_certificates: {
    total_cards: number
    cards_with_certificates: number
    integration_ready: number
  }
  alt_xyz_integration: {
    status: string
    url_pattern: string
    sample_urls: Array<{
      certificate_number: string
      card_name: string
      alt_xyz_url: string
    }>
    integration_steps: Record<string, string>
  }
  enhanced_psa_cards: PSACard[]
  top_5_sales_implementation: {
    description: string
    method_1: string
    method_2: string
    method_3: string
  }
}

export default function PSAAltXYZIntegration() {
  const [data, setData] = useState<AltXYZData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedCard, setSelectedCard] = useState<PSACard | null>(null)

  useEffect(() => {
    fetchPSAAltXYZData()
  }, [])

  const fetchPSAAltXYZData = async () => {
    try {
      const response = await fetch('/api/psa-alt-xyz')
      if (response.ok) {
        const result = await response.json()
        setData(result.data)
      }
    } catch (error) {
      console.error('Error fetching PSA Alt.xyz data:', error)
    } finally {
      setLoading(false)
    }
  }

  const openAltXYZ = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>PSA Certificate & Alt.xyz Integration</CardTitle>
          <CardDescription>Loading PSA certificate data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>PSA Certificate & Alt.xyz Integration</CardTitle>
          <CardDescription>No PSA Alt.xyz data available</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Please run the PSA certificate extractor and Alt.xyz integration system first.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">PSA Cards</CardTitle>
            <Certificate className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.psa_certificates.total_cards}</div>
            <p className="text-xs text-muted-foreground">
              Total PSA cards found
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">With Certificates</CardTitle>
            <Badge variant="secondary">Ready</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.psa_certificates.cards_with_certificates}</div>
            <p className="text-xs text-muted-foreground">
              PSA certificate numbers extracted
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Alt.xyz Ready</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.psa_certificates.integration_ready}</div>
            <p className="text-xs text-muted-foreground">
              Cards ready for Alt.xyz integration
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Integration Status */}
      <Card>
        <CardHeader>
          <CardTitle>Alt.xyz Integration Status</CardTitle>
          <CardDescription>
            PSA certificate extraction and Alt.xyz URL generation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="font-medium">Integration Status:</span>
              <Badge variant="default" className="bg-green-100 text-green-800">
                {data.alt_xyz_integration.status}
              </Badge>
            </div>
            
            <div className="space-y-2">
              <span className="font-medium">URL Pattern:</span>
              <code className="block p-2 bg-gray-100 rounded text-sm">
                {data.alt_xyz_integration.url_pattern}
              </code>
            </div>

            <div className="space-y-2">
              <span className="font-medium">Integration Steps:</span>
              <ul className="list-disc list-inside space-y-1 text-sm">
                {Object.entries(data.alt_xyz_integration.integration_steps).map(([step, description]) => (
                  <li key={step} className="text-muted-foreground">
                    <span className="font-medium">{step.replace('_', ' ').toUpperCase()}:</span> {description}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sample PSA Cards with Certificates */}
      <Card>
        <CardHeader>
          <CardTitle>PSA Cards with Certificates</CardTitle>
          <CardDescription>
            Cards with extracted PSA certificate numbers and Alt.xyz URLs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.enhanced_psa_cards.slice(0, 10).map((card, index) => (
              <div key={index} className="border rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-sm">{card.card_name}</h4>
                  <Badge variant="outline">{card.grader} {card.grade}</Badge>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Certificate:</span>
                    <span className="ml-2 font-mono">{card.psa_certificate_number}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Price:</span>
                    <span className="ml-2">{card.current_price}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openAltXYZ(card.primary_alt_xyz_url)}
                    className="flex items-center space-x-1"
                  >
                    <ExternalLink className="h-3 w-3" />
                    <span>View on Alt.xyz</span>
                  </Button>
                  
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setSelectedCard(card)}
                  >
                    View Details
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Top 5 Sales Implementation */}
      <Card>
        <CardHeader>
          <CardTitle>Top 5 Sales Implementation</CardTitle>
          <CardDescription>
            Methods for getting top 5 sales from Alt.xyz for each PSA card
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {data.top_5_sales_implementation.description}
            </p>
            
            <div className="space-y-2">
              <div className="flex items-start space-x-2">
                <Badge variant="secondary">Method 1</Badge>
                <span className="text-sm">{data.top_5_sales_implementation.method_1}</span>
              </div>
              
              <div className="flex items-start space-x-2">
                <Badge variant="secondary">Method 2</Badge>
                <span className="text-sm">{data.top_5_sales_implementation.method_2}</span>
              </div>
              
              <div className="flex items-start space-x-2">
                <Badge variant="secondary">Method 3</Badge>
                <span className="text-sm">{data.top_5_sales_implementation.method_3}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Selected Card Details Modal */}
      {selectedCard && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">PSA Card Details</h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedCard(null)}
              >
                Close
              </Button>
            </div>
            
            <div className="space-y-4">
              <div>
                <span className="font-medium">Card Name:</span>
                <p className="text-sm text-muted-foreground">{selectedCard.card_name}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="font-medium">PSA Certificate:</span>
                  <p className="text-sm font-mono">{selectedCard.psa_certificate_number}</p>
                </div>
                <div>
                  <span className="font-medium">Grade:</span>
                  <p className="text-sm">{selectedCard.grader} {selectedCard.grade}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="font-medium">Current Price:</span>
                  <p className="text-sm">{selectedCard.current_price}</p>
                </div>
                <div>
                  <span className="font-medium">FMV:</span>
                  <p className="text-sm">{selectedCard.fmv}</p>
                </div>
              </div>
              
              <div>
                <span className="font-medium">Alt.xyz URLs:</span>
                <div className="space-y-1 mt-2">
                  {selectedCard.alt_xyz_urls.map((url, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <code className="text-xs bg-gray-100 p-1 rounded flex-1">{url}</code>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openAltXYZ(url)}
                        className="flex items-center space-x-1"
                      >
                        <ExternalLink className="h-3 w-3" />
                        <span>Open</span>
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
