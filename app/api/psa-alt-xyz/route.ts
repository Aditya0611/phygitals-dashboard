import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET() {
  try {
    // Look for the PSA Alt.xyz integration data
    const dataDir = process.cwd()
    const psaDataFile = path.join(dataDir, 'dashboard_alt_xyz_data.json')
    
    if (!fs.existsSync(psaDataFile)) {
      return NextResponse.json({ 
        error: 'PSA Alt.xyz data not found. Please run the integration system first.' 
      }, { status: 404 })
    }
    
    // Read the PSA Alt.xyz data
    const data = JSON.parse(fs.readFileSync(psaDataFile, 'utf8'))
    
    return NextResponse.json({
      success: true,
      data: data,
      lastUpdated: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('Error reading PSA Alt.xyz data:', error)
    return NextResponse.json({ 
      error: 'Failed to read PSA Alt.xyz data' 
    }, { status: 500 })
  }
}
