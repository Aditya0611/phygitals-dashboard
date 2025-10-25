import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET() {
  try {
    // Look for the filtered data file
    const dataDir = process.cwd()
    const filteredFile = path.join(dataDir, 'filtered_marketplace_data.json')
    
    if (!fs.existsSync(filteredFile)) {
      return NextResponse.json({ 
        error: 'Filtered data not found. Please run the filtering system first.' 
      }, { status: 404 })
    }
    
    // Read the filtered data
    const data = JSON.parse(fs.readFileSync(filteredFile, 'utf8'))
    
    return NextResponse.json({
      success: true,
      data: data,
      lastUpdated: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('Error reading filtered data:', error)
    return NextResponse.json({ 
      error: 'Failed to read filtered data' 
    }, { status: 500 })
  }
}
