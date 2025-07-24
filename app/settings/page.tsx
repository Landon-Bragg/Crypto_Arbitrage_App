"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { TrendingUp, Save, Bell, Mail, Smartphone } from "lucide-react"

export default function Settings() {
  const [settings, setSettings] = useState({
    minSpreadPercent: 0.2,
    maxSpreadPercent: 5.0,
    minVolume: 1.0,
    emailAlerts: true,
    pushNotifications: false,
    smsAlerts: false,
    alertFrequency: "immediate",
    exchanges: ["coinbase", "kraken"],
    symbols: ["BTC/USD", "ETH/USD"],
  })

  const handleSave = () => {
    // Save settings to backend
    console.log("Saving settings:", settings)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-8 w-8 text-purple-400" />
            <span className="text-2xl font-bold text-white">ArbitrageAI</span>
          </div>
          <Button onClick={handleSave} className="bg-purple-600 hover:bg-purple-700">
            <Save className="h-4 w-4 mr-2" />
            Save Settings
          </Button>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <h1 className="text-3xl font-bold text-white mb-8">Settings</h1>

        <div className="grid gap-6">
          {/* Alert Thresholds */}
          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white">Alert Thresholds</CardTitle>
              <CardDescription className="text-gray-300">
                Configure when you want to be notified about arbitrage opportunities
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="minSpread" className="text-gray-300">
                    Minimum Spread (%)
                  </Label>
                  <Input
                    id="minSpread"
                    type="number"
                    step="0.1"
                    value={settings.minSpreadPercent}
                    onChange={(e) => setSettings({ ...settings, minSpreadPercent: Number.parseFloat(e.target.value) })}
                    className="bg-white/10 border-white/20 text-white"
                  />
                </div>
                <div>
                  <Label htmlFor="maxSpread" className="text-gray-300">
                    Maximum Spread (%)
                  </Label>
                  <Input
                    id="maxSpread"
                    type="number"
                    step="0.1"
                    value={settings.maxSpreadPercent}
                    onChange={(e) => setSettings({ ...settings, maxSpreadPercent: Number.parseFloat(e.target.value) })}
                    className="bg-white/10 border-white/20 text-white"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="minVolume" className="text-gray-300">
                  Minimum Volume
                </Label>
                <Input
                  id="minVolume"
                  type="number"
                  step="0.1"
                  value={settings.minVolume}
                  onChange={(e) => setSettings({ ...settings, minVolume: Number.parseFloat(e.target.value) })}
                  className="bg-white/10 border-white/20 text-white"
                />
              </div>
            </CardContent>
          </Card>

          {/* Notification Settings */}
          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white">Notifications</CardTitle>
              <CardDescription className="text-gray-300">Choose how you want to receive alerts</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Mail className="h-5 w-5 text-purple-400" />
                  <div>
                    <Label className="text-white">Email Alerts</Label>
                    <p className="text-sm text-gray-400">Receive opportunities via email</p>
                  </div>
                </div>
                <Switch
                  checked={settings.emailAlerts}
                  onCheckedChange={(checked) => setSettings({ ...settings, emailAlerts: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Bell className="h-5 w-5 text-purple-400" />
                  <div>
                    <Label className="text-white">Push Notifications</Label>
                    <p className="text-sm text-gray-400">Browser notifications</p>
                  </div>
                </div>
                <Switch
                  checked={settings.pushNotifications}
                  onCheckedChange={(checked) => setSettings({ ...settings, pushNotifications: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Smartphone className="h-5 w-5 text-purple-400" />
                  <div>
                    <Label className="text-white">SMS Alerts</Label>
                    <p className="text-sm text-gray-400">Text message notifications</p>
                  </div>
                </div>
                <Switch
                  checked={settings.smsAlerts}
                  onCheckedChange={(checked) => setSettings({ ...settings, smsAlerts: checked })}
                />
              </div>

              <div>
                <Label className="text-gray-300">Alert Frequency</Label>
                <Select
                  value={settings.alertFrequency}
                  onValueChange={(value) => setSettings({ ...settings, alertFrequency: value })}
                >
                  <SelectTrigger className="bg-white/10 border-white/20 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="immediate">Immediate</SelectItem>
                    <SelectItem value="every-5min">Every 5 minutes</SelectItem>
                    <SelectItem value="every-15min">Every 15 minutes</SelectItem>
                    <SelectItem value="hourly">Hourly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Trading Pairs */}
          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white">Monitored Assets</CardTitle>
              <CardDescription className="text-gray-300">Select which cryptocurrency pairs to monitor</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {["BTC/USD", "ETH/USD", "XRP/USD", "ADA/USD", "DOT/USD", "LINK/USD"].map((symbol) => (
                  <div key={symbol} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={symbol}
                      checked={settings.symbols.includes(symbol)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSettings({ ...settings, symbols: [...settings.symbols, symbol] })
                        } else {
                          setSettings({ ...settings, symbols: settings.symbols.filter((s) => s !== symbol) })
                        }
                      }}
                      className="rounded border-white/20"
                    />
                    <Label htmlFor={symbol} className="text-white">
                      {symbol}
                    </Label>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
