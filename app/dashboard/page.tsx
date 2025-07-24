"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { TrendingUp, AlertTriangle, DollarSign, Activity, Settings, Bell } from "lucide-react"

interface ArbitrageOpportunity {
  id: string
  symbol: string
  buyExchange: string
  sellExchange: string
  buyPrice: number
  sellPrice: number
  spread: number
  spreadPercent: number
  timestamp: number
  volume: number
}

export default function Dashboard() {
  const [opportunities, setOpportunities] = useState<ArbitrageOpportunity[]>([])
  const [isConnected, setIsConnected] = useState(false)

  // Mock data for demonstration
  useEffect(() => {
    const mockOpportunities: ArbitrageOpportunity[] = [
      {
        id: "1",
        symbol: "BTC/USD",
        buyExchange: "Coinbase",
        sellExchange: "Kraken",
        buyPrice: 43250.5,
        sellPrice: 43380.25,
        spread: 129.75,
        spreadPercent: 0.3,
        timestamp: Date.now(),
        volume: 2.5,
      },
      {
        id: "2",
        symbol: "ETH/USD",
        buyExchange: "Kraken",
        sellExchange: "Coinbase",
        buyPrice: 2650.8,
        sellPrice: 2668.45,
        spread: 17.65,
        spreadPercent: 0.67,
        timestamp: Date.now() - 30000,
        volume: 15.2,
      },
      {
        id: "3",
        symbol: "XRP/USD",
        buyExchange: "Coinbase",
        sellExchange: "Kraken",
        buyPrice: 0.6234,
        sellPrice: 0.6251,
        spread: 0.0017,
        spreadPercent: 0.27,
        timestamp: Date.now() - 60000,
        volume: 1000.0,
      },
    ]

    setOpportunities(mockOpportunities)
    setIsConnected(true)

    // Simulate real-time updates
    const interval = setInterval(() => {
      setOpportunities((prev) =>
        prev
          .map((opp) => ({
            ...opp,
            buyPrice: opp.buyPrice + (Math.random() - 0.5) * opp.buyPrice * 0.001,
            sellPrice: opp.sellPrice + (Math.random() - 0.5) * opp.sellPrice * 0.001,
            timestamp: Date.now(),
          }))
          .map((opp) => ({
            ...opp,
            spread: opp.sellPrice - opp.buyPrice,
            spreadPercent: ((opp.sellPrice - opp.buyPrice) / opp.buyPrice) * 100,
          })),
      )
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  const formatTime = (timestamp: number) => {
    const now = Date.now()
    const diff = now - timestamp
    if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    return new Date(timestamp).toLocaleTimeString()
  }

  const totalPotentialProfit = opportunities.reduce((sum, opp) => sum + opp.spread * opp.volume, 0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-8 w-8 text-purple-400" />
            <span className="text-2xl font-bold text-white">ArbitrageAI</span>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-400" : "bg-red-400"}`} />
              <span className="text-sm text-gray-300">{isConnected ? "Connected" : "Disconnected"}</span>
            </div>
            <Button variant="ghost" size="sm" className="text-white hover:bg-white/10">
              <Bell className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" className="text-white hover:bg-white/10">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-300">Active Opportunities</CardTitle>
              <Activity className="h-4 w-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{opportunities.length}</div>
              <p className="text-xs text-gray-400">+2 from last hour</p>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-300">Potential Profit</CardTitle>
              <DollarSign className="h-4 w-4 text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">${totalPotentialProfit.toFixed(2)}</div>
              <p className="text-xs text-gray-400">Based on current volume</p>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-300">Best Spread</CardTitle>
              <TrendingUp className="h-4 w-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {Math.max(...opportunities.map((o) => o.spreadPercent)).toFixed(2)}%
              </div>
              <p className="text-xs text-gray-400">ETH/USD opportunity</p>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-300">Exchanges</CardTitle>
              <AlertTriangle className="h-4 w-4 text-yellow-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">2</div>
              <p className="text-xs text-gray-400">Coinbase, Kraken</p>
            </CardContent>
          </Card>
        </div>

        {/* Opportunities Table */}
        <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-white">Live Arbitrage Opportunities</CardTitle>
            <CardDescription className="text-gray-300">Real-time price differences across exchanges</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {opportunities.map((opp) => (
                <div
                  key={opp.id}
                  className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/10"
                >
                  <div className="flex items-center space-x-4">
                    <div>
                      <div className="font-semibold text-white">{opp.symbol}</div>
                      <div className="text-sm text-gray-400">
                        Buy: {opp.buyExchange} → Sell: {opp.sellExchange}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-6">
                    <div className="text-right">
                      <div className="text-sm text-gray-400">Buy Price</div>
                      <div className="font-medium text-white">${opp.buyPrice.toFixed(2)}</div>
                    </div>

                    <div className="text-right">
                      <div className="text-sm text-gray-400">Sell Price</div>
                      <div className="font-medium text-white">${opp.sellPrice.toFixed(2)}</div>
                    </div>

                    <div className="text-right">
                      <div className="text-sm text-gray-400">Spread</div>
                      <div className="font-medium text-green-400">
                        ${opp.spread.toFixed(2)} ({opp.spreadPercent.toFixed(2)}%)
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-sm text-gray-400">Volume</div>
                      <div className="font-medium text-white">{opp.volume.toFixed(1)}</div>
                    </div>

                    <div className="text-right">
                      <Badge variant={opp.spreadPercent > 0.5 ? "default" : "secondary"} className="bg-purple-600">
                        {opp.spreadPercent > 0.5 ? "High" : "Low"}
                      </Badge>
                      <div className="text-xs text-gray-400 mt-1">{formatTime(opp.timestamp)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
