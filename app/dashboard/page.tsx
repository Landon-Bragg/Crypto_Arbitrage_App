"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  TrendingUp,
  DollarSign,
  Activity,
  Settings,
  Bell,
  RefreshCw,
  Info,
  Zap,
  Target,
  BarChart3,
  Clock,
  Shield,
  Wifi,
  WifiOff,
} from "lucide-react"
import { useWebSocket } from "@/hooks/use-websocket"
import { timeAgo, formatCurrency, formatPercent } from "@/lib/utils"

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
  buyVolume?: number
  sellVolume?: number
  confidenceScore: number
  profitPotential: number
  executionTimeEstimate: number
  riskLevel: string
  historicalFrequency: number
}

interface ExchangeStatus {
  name: string
  connected: boolean
  last_update: number
  error_count: number
  avg_response_time: number
  supported_symbols: string[]
  health_score: number
}

interface ApiMetadata {
  total_opportunities: number
  timestamp: number
  connected_exchanges: string[]
  detection_stats: {
    total_detections: number
    opportunities_found: number
    avg_detection_time: number
  }
  current_analytics: {
    total_opportunities: number
    avg_spread: number
    max_spread: number
    total_profit_potential: number
    avg_confidence: number
  }
}

interface AlertCondition {
  id: string
  name: string
  symbol?: string
  min_spread_percent: number
  min_profit_potential: number
  min_confidence_score: number
  preferred_exchanges: string[]
  max_risk_level: string
  enabled: boolean
}

// Enhanced mock data for professional demo
const mockOpportunities: ArbitrageOpportunity[] = [
  {
    id: "1",
    symbol: "BTC/USD",
    buyExchange: "kraken",
    sellExchange: "bitfinex",
    buyPrice: 43250.5,
    sellPrice: 43380.25,
    spread: 129.75,
    spreadPercent: 0.3,
    timestamp: Date.now() / 1000,
    buyVolume: 2.5,
    sellVolume: 3.2,
    confidenceScore: 0.85,
    profitPotential: 64.88,
    executionTimeEstimate: 45,
    riskLevel: "medium",
    historicalFrequency: 0.12,
  },
  {
    id: "2",
    symbol: "ETH/USD",
    buyExchange: "kucoin",
    sellExchange: "kraken",
    buyPrice: 2650.8,
    sellPrice: 2668.45,
    spread: 17.65,
    spreadPercent: 0.67,
    timestamp: Date.now() / 1000 - 30,
    buyVolume: 15.2,
    sellVolume: 12.8,
    confidenceScore: 0.92,
    profitPotential: 226.32,
    executionTimeEstimate: 35,
    riskLevel: "medium-low",
    historicalFrequency: 0.08,
  },
  {
    id: "3",
    symbol: "XRP/USD",
    buyExchange: "bitfinex",
    sellExchange: "kucoin",
    buyPrice: 0.6234,
    sellPrice: 0.6251,
    spread: 0.0017,
    spreadPercent: 0.27,
    timestamp: Date.now() / 1000 - 60,
    buyVolume: 1000.0,
    sellVolume: 1200.0,
    confidenceScore: 0.78,
    profitPotential: 1.7,
    executionTimeEstimate: 60,
    riskLevel: "low",
    historicalFrequency: 0.15,
  },
]

const mockExchangeStatuses: Record<string, ExchangeStatus> = {
  kraken: {
    name: "kraken",
    connected: true,
    last_update: Date.now() / 1000,
    error_count: 2,
    avg_response_time: 0.8,
    supported_symbols: ["BTC/USD", "ETH/USD", "XRP/USD", "LTC/USD"],
    health_score: 0.95,
  },
  kucoin: {
    name: "kucoin",
    connected: true,
    last_update: Date.now() / 1000 - 5,
    error_count: 1,
    avg_response_time: 1.2,
    supported_symbols: ["BTC/USD", "ETH/USD", "XRP/USD", "LTC/USD"],
    health_score: 0.88,
  },
  bitfinex: {
    name: "bitfinex",
    connected: true,
    last_update: Date.now() / 1000 - 3,
    error_count: 0,
    avg_response_time: 0.6,
    supported_symbols: ["BTC/USD", "ETH/USD", "XRP/USD", "LTC/USD"],
    health_score: 0.98,
  },
}

const mockMetadata: ApiMetadata = {
  total_opportunities: 3,
  timestamp: Date.now() / 1000,
  connected_exchanges: ["kraken", "kucoin", "bitfinex"],
  detection_stats: {
    total_detections: 1247,
    opportunities_found: 89,
    avg_detection_time: 0.85,
  },
  current_analytics: {
    total_opportunities: 3,
    avg_spread: 0.41,
    max_spread: 0.67,
    total_profit_potential: 292.9,
    avg_confidence: 0.85,
  },
}

export default function ProfessionalDashboard() {
  const [opportunities, setOpportunities] = useState<ArbitrageOpportunity[]>([])
  const [exchangeStatuses, setExchangeStatuses] = useState<Record<string, ExchangeStatus>>({})
  const [metadata, setMetadata] = useState<ApiMetadata | null>(null)
  const [alerts, setAlerts] = useState<AlertCondition[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<number>(Date.now())
  const [error, setError] = useState<string | null>(null)
  const [isPreviewMode, setIsPreviewMode] = useState(false)
  const [selectedTab, setSelectedTab] = useState("opportunities")

  // Check if we're in preview mode
  useEffect(() => {
    if (typeof window !== "undefined") {
      const isPreview = window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
      setIsPreviewMode(isPreview)

      if (isPreview) {
        setOpportunities(mockOpportunities)
        setExchangeStatuses(mockExchangeStatuses)
        setMetadata(mockMetadata)
        setLastUpdated(Date.now())
        setIsLoading(false)
        setError("Demo Mode - Connect to backend for live data")
      }
    }
  }, [])

  // WebSocket connection for real-time updates
  const { status: wsStatus } = useWebSocket(isPreviewMode ? null : "ws://localhost:8000/ws", {
    onMessage: (event) => {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case "arbitrage_update":
            setOpportunities(data.data.opportunities)
            setLastUpdated(data.data.timestamp * 1000)
            break
          case "health_update":
            setExchangeStatuses(data.data.exchange_statuses)
            break
          case "alert_triggered":
            // Handle alert notifications
            console.log("Alert triggered:", data.data.alerts)
            break
          case "initial_data":
            setOpportunities(data.data.opportunities)
            setLastUpdated(data.data.timestamp * 1000)
            break
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error)
      }
    },
    autoReconnect: !isPreviewMode,
  })

  // Initial data fetch
  useEffect(() => {
    if (isPreviewMode) return

    async function fetchInitialData() {
      try {
        setIsLoading(true)
        setError(null)

        // Fetch opportunities
        const arbResponse = await fetch("http://localhost:8000/arbitrage")
        if (arbResponse.ok) {
          const arbData = await arbResponse.json()
          setOpportunities(arbData.opportunities)
          setMetadata(arbData.metadata)
        }

        // Fetch exchange statuses
        const exchangeResponse = await fetch("http://localhost:8000/exchanges")
        if (exchangeResponse.ok) {
          const exchangeData = await exchangeResponse.json()
          setExchangeStatuses(exchangeData.exchanges)
        }

        // Fetch alerts
        const alertResponse = await fetch("http://localhost:8000/alerts")
        if (alertResponse.ok) {
          const alertData = await alertResponse.json()
          setAlerts(Object.values(alertData.alerts))
        }

        setLastUpdated(Date.now())
      } catch (error) {
        console.error("Error fetching initial data:", error)
        setError("Could not connect to backend server. Using demo data.")

        // Fallback to mock data
        setOpportunities(mockOpportunities)
        setExchangeStatuses(mockExchangeStatuses)
        setMetadata(mockMetadata)
        setLastUpdated(Date.now())
      } finally {
        setIsLoading(false)
      }
    }

    fetchInitialData()
  }, [isPreviewMode])

  const handleRefresh = useCallback(async () => {
    if (isPreviewMode) {
      setIsLoading(true)
      setTimeout(() => {
        const updatedOpportunities = mockOpportunities
          .map((opp) => ({
            ...opp,
            buyPrice: opp.buyPrice * (1 + (Math.random() * 0.01 - 0.005)),
            sellPrice: opp.sellPrice * (1 + (Math.random() * 0.01 - 0.005)),
            timestamp: Date.now() / 1000,
          }))
          .map((opp) => ({
            ...opp,
            spread: opp.sellPrice - opp.buyPrice,
            spreadPercent: ((opp.sellPrice - opp.buyPrice) / opp.buyPrice) * 100,
          }))

        setOpportunities(updatedOpportunities)
        setLastUpdated(Date.now())
        setIsLoading(false)
      }, 800)
      return
    }

    try {
      setIsLoading(true)
      const response = await fetch("http://localhost:8000/arbitrage")
      if (response.ok) {
        const data = await response.json()
        setOpportunities(data.opportunities)
        setMetadata(data.metadata)
        setLastUpdated(Date.now())
      }
    } catch (error) {
      console.error("Error refreshing data:", error)
    } finally {
      setIsLoading(false)
    }
  }, [isPreviewMode])

  const isConnected = !isPreviewMode && wsStatus === "open"
  const connectedExchanges = Object.values(exchangeStatuses).filter((e) => e.connected)
  const totalProfitPotential = opportunities.reduce((sum, opp) => sum + opp.profitPotential, 0)
  const avgConfidence =
    opportunities.length > 0
      ? opportunities.reduce((sum, opp) => sum + opp.confidenceScore, 0) / opportunities.length
      : 0
  const bestOpportunity =
    opportunities.length > 0
      ? opportunities.reduce((best, opp) => (opp.spreadPercent > best.spreadPercent ? opp : best))
      : null

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case "low":
        return "text-green-400"
      case "medium-low":
        return "text-blue-400"
      case "medium":
        return "text-yellow-400"
      case "medium-high":
        return "text-orange-400"
      case "high":
        return "text-red-400"
      default:
        return "text-gray-400"
    }
  }

  const getHealthColor = (score: number) => {
    if (score >= 0.9) return "text-green-400"
    if (score >= 0.7) return "text-yellow-400"
    return "text-red-400"
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Enhanced Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <TrendingUp className="h-8 w-8 text-purple-400" />
              <div>
                <span className="text-2xl font-bold text-white">ArbitrageAI Pro</span>
                <div className="text-xs text-gray-400">Professional Trading Platform</div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                {isConnected ? (
                  <Wifi className="h-4 w-4 text-green-400" />
                ) : (
                  <WifiOff className="h-4 w-4 text-red-400" />
                )}
                <span className="text-sm text-gray-300">
                  {isPreviewMode ? "Demo Mode" : isConnected ? "Live" : "Offline"}
                </span>
              </div>

              {/* Exchange Status */}
              <div className="flex items-center space-x-1">
                {Object.values(exchangeStatuses).map((exchange) => (
                  <div
                    key={exchange.name}
                    className={`w-2 h-2 rounded-full ${exchange.connected ? "bg-green-400" : "bg-red-400"}`}
                    title={`${exchange.name}: ${exchange.connected ? "Connected" : "Disconnected"}`}
                  />
                ))}
              </div>

              {/* Action Buttons */}
              <Button
                variant="ghost"
                size="sm"
                className="text-white hover:bg-white/10"
                onClick={handleRefresh}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              </Button>

              <Button variant="ghost" size="sm" className="text-white hover:bg-white/10">
                <Bell className="h-4 w-4" />
                {alerts.filter((a) => a.enabled).length > 0 && (
                  <span className="ml-1 text-xs bg-purple-600 rounded-full px-1">
                    {alerts.filter((a) => a.enabled).length}
                  </span>
                )}
              </Button>

              <Button variant="ghost" size="sm" className="text-white hover:bg-white/10">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        {/* Error/Status Banner */}
        {error && (
          <div className="mb-6 p-4 bg-yellow-500/20 border border-yellow-500/30 rounded-lg flex items-center gap-3 text-yellow-200">
            <Info className="h-5 w-5 flex-shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {/* Key Metrics Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-300">Active Opportunities</CardTitle>
              <Activity className="h-4 w-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{opportunities.length}</div>
              <p className="text-xs text-gray-400">
                {metadata?.detection_stats.total_detections || 0} total detections
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-300">Profit Potential</CardTitle>
              <DollarSign className="h-4 w-4 text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{formatCurrency(totalProfitPotential)}</div>
              <p className="text-xs text-gray-400">
                Avg: {formatCurrency(totalProfitPotential / Math.max(opportunities.length, 1))}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-300">Best Spread</CardTitle>
              <TrendingUp className="h-4 w-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {bestOpportunity ? formatPercent(bestOpportunity.spreadPercent) : "0.00%"}
              </div>
              <p className="text-xs text-gray-400">{bestOpportunity ? bestOpportunity.symbol : "No opportunities"}</p>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-300">System Health</CardTitle>
              <Shield className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{connectedExchanges.length}/3</div>
              <p className="text-xs text-gray-400">Avg confidence: {formatPercent(avgConfidence)}</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-white/5 border-white/10">
            <TabsTrigger value="opportunities" className="data-[state=active]:bg-purple-600">
              Opportunities
            </TabsTrigger>
            <TabsTrigger value="exchanges" className="data-[state=active]:bg-purple-600">
              Exchanges
            </TabsTrigger>
            <TabsTrigger value="analytics" className="data-[state=active]:bg-purple-600">
              Analytics
            </TabsTrigger>
            <TabsTrigger value="alerts" className="data-[state=active]:bg-purple-600">
              Alerts
            </TabsTrigger>
          </TabsList>

          {/* Opportunities Tab */}
          <TabsContent value="opportunities">
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Live Arbitrage Opportunities
                </CardTitle>
                <CardDescription className="text-gray-300">
                  Real-time opportunities across Kraken, KuCoin, and Bitfinex • Updated {timeAgo(lastUpdated)}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex justify-center items-center py-12">
                    <RefreshCw className="h-8 w-8 text-purple-400 animate-spin" />
                  </div>
                ) : opportunities.length > 0 ? (
                  <div className="space-y-4">
                    {opportunities.map((opp) => (
                      <div
                        key={opp.id}
                        className="p-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div>
                              <div className="font-semibold text-white text-lg">{opp.symbol}</div>
                              <div className="text-sm text-gray-400">
                                {opp.buyExchange} → {opp.sellExchange}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center space-x-6">
                            <div className="text-right">
                              <div className="text-sm text-gray-400">Buy Price</div>
                              <div className="font-medium text-white">{formatCurrency(opp.buyPrice)}</div>
                            </div>

                            <div className="text-right">
                              <div className="text-sm text-gray-400">Sell Price</div>
                              <div className="font-medium text-white">{formatCurrency(opp.sellPrice)}</div>
                            </div>

                            <div className="text-right">
                              <div className="text-sm text-gray-400">Spread</div>
                              <div className="font-medium text-green-400">
                                {formatCurrency(opp.spread)} ({formatPercent(opp.spreadPercent)})
                              </div>
                            </div>

                            <div className="text-right">
                              <div className="text-sm text-gray-400">Profit</div>
                              <div className="font-medium text-green-400">{formatCurrency(opp.profitPotential)}</div>
                            </div>

                            <div className="text-right">
                              <div className="text-sm text-gray-400">Confidence</div>
                              <div className="font-medium text-white">{formatPercent(opp.confidenceScore)}</div>
                            </div>

                            <div className="text-right">
                              <div className="text-sm text-gray-400">Risk</div>
                              <Badge className={`${getRiskColor(opp.riskLevel)} bg-transparent border-current`}>
                                {opp.riskLevel}
                              </Badge>
                            </div>

                            <div className="text-right">
                              <div className="text-sm text-gray-400">Time Window</div>
                              <div className="font-medium text-white flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {opp.executionTimeEstimate}s
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <div className="text-gray-400 text-lg">No arbitrage opportunities found</div>
                    <p className="text-sm text-gray-500 mt-2">Monitoring for spreads above 0.05% threshold</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Exchanges Tab */}
          <TabsContent value="exchanges">
            <div className="grid gap-6">
              {Object.values(exchangeStatuses).map((exchange) => (
                <Card key={exchange.name} className="bg-white/5 border-white/10 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${exchange.connected ? "bg-green-400" : "bg-red-400"}`} />
                        {exchange.name.toUpperCase()}
                      </div>
                      <Badge className={`${getHealthColor(exchange.health_score)} bg-transparent border-current`}>
                        Health: {formatPercent(exchange.health_score)}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <div className="text-sm text-gray-400">Status</div>
                        <div className={`font-medium ${exchange.connected ? "text-green-400" : "text-red-400"}`}>
                          {exchange.connected ? "Connected" : "Disconnected"}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-400">Response Time</div>
                        <div className="font-medium text-white">{exchange.avg_response_time.toFixed(2)}s</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-400">Error Count</div>
                        <div className="font-medium text-white">{exchange.error_count}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-400">Last Update</div>
                        <div className="font-medium text-white">{timeAgo(exchange.last_update * 1000)}</div>
                      </div>
                    </div>
                    <div className="mt-4">
                      <div className="text-sm text-gray-400 mb-2">Supported Symbols</div>
                      <div className="flex flex-wrap gap-2">
                        {exchange.supported_symbols.map((symbol) => (
                          <Badge key={symbol} variant="secondary" className="bg-white/10 text-white">
                            {symbol}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics">
            <div className="grid gap-6">
              <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Performance Analytics
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <div className="text-sm text-gray-400">Detection Performance</div>
                      <div className="mt-2 space-y-2">
                        <div className="flex justify-between">
                          <span className="text-white">Total Detections</span>
                          <span className="text-white">{metadata?.detection_stats.total_detections || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-white">Opportunities Found</span>
                          <span className="text-white">{metadata?.detection_stats.opportunities_found || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-white">Avg Detection Time</span>
                          <span className="text-white">
                            {metadata?.detection_stats.avg_detection_time.toFixed(2) || 0}s
                          </span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="text-sm text-gray-400">Current Session</div>
                      <div className="mt-2 space-y-2">
                        <div className="flex justify-between">
                          <span className="text-white">Active Opportunities</span>
                          <span className="text-white">{opportunities.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-white">Average Spread</span>
                          <span className="text-white">
                            {formatPercent(metadata?.current_analytics.avg_spread || 0)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-white">Max Spread</span>
                          <span className="text-white">
                            {formatPercent(metadata?.current_analytics.max_spread || 0)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="text-sm text-gray-400">Profit Analysis</div>
                      <div className="mt-2 space-y-2">
                        <div className="flex justify-between">
                          <span className="text-white">Total Potential</span>
                          <span className="text-white">{formatCurrency(totalProfitPotential)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-white">Average per Opp</span>
                          <span className="text-white">
                            {formatCurrency(totalProfitPotential / Math.max(opportunities.length, 1))}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-white">Avg Confidence</span>
                          <span className="text-white">{formatPercent(avgConfidence)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts">
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Zap className="h-5 w-5" />
                    Alert Conditions
                  </div>
                  <Button className="bg-purple-600 hover:bg-purple-700">Create Alert</Button>
                </CardTitle>
                <CardDescription className="text-gray-300">
                  Manage your custom alert conditions for arbitrage opportunities
                </CardDescription>
              </CardHeader>
              <CardContent>
                {alerts.length > 0 ? (
                  <div className="space-y-4">
                    {alerts.map((alert) => (
                      <div
                        key={alert.id}
                        className="p-4 rounded-lg bg-white/5 border border-white/10 flex items-center justify-between"
                      >
                        <div>
                          <div className="font-medium text-white">{alert.name}</div>
                          <div className="text-sm text-gray-400">
                            {alert.symbol || "All symbols"} • Min spread: {formatPercent(alert.min_spread_percent)} •
                            Min profit: {formatCurrency(alert.min_profit_potential)}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={alert.enabled ? "default" : "secondary"}>
                            {alert.enabled ? "Active" : "Disabled"}
                          </Badge>
                          <Button variant="ghost" size="sm" className="text-white hover:bg-white/10">
                            Edit
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Zap className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <div className="text-gray-400 text-lg">No alert conditions configured</div>
                    <p className="text-sm text-gray-500 mt-2">
                      Create custom alerts to be notified of specific arbitrage opportunities
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
