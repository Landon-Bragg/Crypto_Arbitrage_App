import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, TrendingUp, Zap, Shield, BarChart3 } from "lucide-react"
import Link from "next/link"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-8 w-8 text-purple-400" />
            <span className="text-2xl font-bold text-white">ArbitrageAI</span>
          </div>
          <nav className="hidden md:flex space-x-6">
            <Link href="#features" className="text-gray-300 hover:text-white transition-colors">
              Features
            </Link>
            <Link href="#pricing" className="text-gray-300 hover:text-white transition-colors">
              Pricing
            </Link>
            <Link href="/dashboard" className="text-gray-300 hover:text-white transition-colors">
              Dashboard
            </Link>
          </nav>
          <div className="flex space-x-2">
            <Button variant="ghost" className="text-white hover:bg-white/10">
              Sign In
            </Button>
            <Button className="bg-purple-600 hover:bg-purple-700">Start Free Trial</Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <Badge className="mb-4 bg-purple-600/20 text-purple-300 border-purple-600/30">
            Real-time Crypto Arbitrage Detection
          </Badge>
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
            Profit from
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
              {" "}
              Price Gaps
            </span>
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Discover profitable arbitrage opportunities across major crypto exchanges in real-time. Our advanced
            algorithms monitor price differences and alert you to actionable trades.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-purple-600 hover:bg-purple-700 text-lg px-8 py-4">
              Start Free Trial <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10 text-lg px-8 py-4 bg-transparent"
            >
              View Live Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 bg-black/20">
        <div className="container mx-auto">
          <h2 className="text-4xl font-bold text-white text-center mb-12">Why Choose ArbitrageAI?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <Zap className="h-12 w-12 text-purple-400 mb-4" />
                <CardTitle className="text-white">Real-time Detection</CardTitle>
                <CardDescription className="text-gray-300">
                  Monitor price differences across exchanges with millisecond precision
                </CardDescription>
              </CardHeader>
              <CardContent className="text-gray-300">
                <ul className="space-y-2">
                  <li>• WebSocket connections to major exchanges</li>
                  <li>• Sub-second opportunity alerts</li>
                  <li>• Live order book analysis</li>
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <BarChart3 className="h-12 w-12 text-purple-400 mb-4" />
                <CardTitle className="text-white">Advanced Analytics</CardTitle>
                <CardDescription className="text-gray-300">
                  Comprehensive data and insights to maximize your profits
                </CardDescription>
              </CardHeader>
              <CardContent className="text-gray-300">
                <ul className="space-y-2">
                  <li>• Historical arbitrage data</li>
                  <li>• Profit potential calculations</li>
                  <li>• Market trend analysis</li>
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <Shield className="h-12 w-12 text-purple-400 mb-4" />
                <CardTitle className="text-white">Risk Management</CardTitle>
                <CardDescription className="text-gray-300">
                  Built-in safeguards to protect your trading capital
                </CardDescription>
              </CardHeader>
              <CardContent className="text-gray-300">
                <ul className="space-y-2">
                  <li>• Minimum spread thresholds</li>
                  <li>• Volume analysis</li>
                  <li>• Exchange reliability scores</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4">
        <div className="container mx-auto">
          <h2 className="text-4xl font-bold text-white text-center mb-12">Choose Your Plan</h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white">Starter</CardTitle>
                <CardDescription className="text-gray-300">Perfect for beginners</CardDescription>
                <div className="text-3xl font-bold text-white mt-4">
                  $29<span className="text-lg text-gray-300">/month</span>
                </div>
              </CardHeader>
              <CardContent className="text-gray-300">
                <ul className="space-y-3">
                  <li>• 3 cryptocurrency pairs</li>
                  <li>• 2 exchanges monitored</li>
                  <li>• Email alerts</li>
                  <li>• Basic analytics</li>
                </ul>
                <Button className="w-full mt-6 bg-purple-600 hover:bg-purple-700">Start Free Trial</Button>
              </CardContent>
            </Card>

            <Card className="bg-white/5 border-purple-500/50 backdrop-blur-sm relative">
              <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-purple-600">Most Popular</Badge>
              <CardHeader>
                <CardTitle className="text-white">Professional</CardTitle>
                <CardDescription className="text-gray-300">For serious traders</CardDescription>
                <div className="text-3xl font-bold text-white mt-4">
                  $99<span className="text-lg text-gray-300">/month</span>
                </div>
              </CardHeader>
              <CardContent className="text-gray-300">
                <ul className="space-y-3">
                  <li>• 10 cryptocurrency pairs</li>
                  <li>• 5 exchanges monitored</li>
                  <li>• Real-time alerts</li>
                  <li>• Advanced analytics</li>
                  <li>• API access</li>
                </ul>
                <Button className="w-full mt-6 bg-purple-600 hover:bg-purple-700">Start Free Trial</Button>
              </CardContent>
            </Card>

            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white">Enterprise</CardTitle>
                <CardDescription className="text-gray-300">Maximum opportunities</CardDescription>
                <div className="text-3xl font-bold text-white mt-4">
                  $299<span className="text-lg text-gray-300">/month</span>
                </div>
              </CardHeader>
              <CardContent className="text-gray-300">
                <ul className="space-y-3">
                  <li>• Unlimited pairs</li>
                  <li>• All exchanges</li>
                  <li>• Instant notifications</li>
                  <li>• Custom alerts</li>
                  <li>• Priority support</li>
                </ul>
                <Button className="w-full mt-6 bg-purple-600 hover:bg-purple-700">Contact Sales</Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-black/20 backdrop-blur-sm py-12">
        <div className="container mx-auto px-4 text-center text-gray-300">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <TrendingUp className="h-6 w-6 text-purple-400" />
            <span className="text-xl font-bold text-white">ArbitrageAI</span>
          </div>
          <p>© 2024 ArbitrageAI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
