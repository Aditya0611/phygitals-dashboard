import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET() {
  try {
    const dataDir = process.cwd()
    const psaDealsFile = path.join(dataDir, 'psa_deals_analysis.json')
    
    if (!fs.existsSync(psaDealsFile)) {
      return NextResponse.json({ 
        error: 'PSA deals analysis not found. Please run the PSA analysis first.' 
      }, { status: 404 })
    }
    
    const data = JSON.parse(fs.readFileSync(psaDealsFile, 'utf8'))
    
    return NextResponse.json({
      success: true,
      data: data,
      lastUpdated: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('Error reading PSA deals data:', error)
    return NextResponse.json({ 
      error: 'Failed to read PSA deals data' 
    }, { status: 500 })
  }
}
