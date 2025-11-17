import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET() {
  try {
    const dataDir = process.cwd()
    const psaDealsFile = path.join(dataDir, 'psa_deals_analysis.json')
    
    if (!fs.existsSync(psaDealsFile)) {
      // Return empty data structure instead of error
      return NextResponse.json({
        success: true,
        data: {
          affordable_deals: [],
          premium_deals: [],
          all_psa_deals: [],
          summary: {
            total_psa_cards: 0,
            psa_deals_found: 0,
            affordable_count: 0,
            premium_count: 0
          }
        },
        lastUpdated: new Date().toISOString()
      })
    }
    
    const data = JSON.parse(fs.readFileSync(psaDealsFile, 'utf8'))
    
    return NextResponse.json({
      success: true,
      data: data,
      lastUpdated: new Date().toISOString()
    }, {
      headers: {
        'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    })
    
  } catch (error) {
    console.error('Error reading PSA deals data:', error)
    return NextResponse.json({ 
      error: 'Failed to read PSA deals data' 
    }, { status: 500 })
  }
}
