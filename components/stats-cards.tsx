"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CardData } from "@/components/data-table"
import { formatPrice } from "@/lib/utils"
import { TrendingUp, DollarSign, Award, Package } from "lucide-react"

interface StatsCardsProps {
  data: CardData[]
}

export function StatsCards({ data }: StatsCardsProps) {
  const totalCards = data.length
  const totalValue = data.reduce((sum, card) => sum + formatPrice(card.current_price), 0)
  const avgPrice = totalValue / totalCards || 0
  
  const graders = data.reduce((acc, card) => {
    acc[card.grader] = (acc[card.grader] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  
  const topGrader = Object.entries(graders).sort(([,a], [,b]) => b - a)[0]
  
  const grades = data.reduce((acc, card) => {
    acc[card.grade] = (acc[card.grade] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  
  const topGrade = Object.entries(grades).sort(([,a], [,b]) => b - a)[0]

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Cards</CardTitle>
          <Package className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalCards.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">
            Cards in marketplace
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Value</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">${totalValue.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">
            Combined market value
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Average Price</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">${avgPrice.toFixed(2)}</div>
          <p className="text-xs text-muted-foreground">
            Per card average
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Top Grader</CardTitle>
          <Award className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            <Badge variant="secondary">{topGrader?.[0] || 'N/A'}</Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            {topGrader?.[1] || 0} cards
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
