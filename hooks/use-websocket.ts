"use client"

import { useState, useEffect, useRef, useCallback } from "react"

type WebSocketStatus = "connecting" | "open" | "closed" | "error"

interface UseWebSocketOptions {
  onOpen?: (event: WebSocketEventMap["open"]) => void
  onMessage?: (event: WebSocketEventMap["message"]) => void
  onClose?: (event: WebSocketEventMap["close"]) => void
  onError?: (event: WebSocketEventMap["error"]) => void
  reconnectInterval?: number
  reconnectAttempts?: number
  autoReconnect?: boolean
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const [status, setStatus] = useState<WebSocketStatus>("connecting")
  const [data, setData] = useState<any>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const reconnectAttemptsRef = useRef(0)

  const {
    onOpen,
    onMessage,
    onClose,
    onError,
    reconnectInterval = 3000,
    reconnectAttempts = 5,
    autoReconnect = true,
  } = options

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = (event) => {
        setStatus("open")
        reconnectAttemptsRef.current = 0
        if (onOpen) onOpen(event)
      }

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data)
          setData(parsed)
          if (onMessage) onMessage(event)
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error)
        }
      }

      ws.onclose = (event) => {
        setStatus("closed")
        if (onClose) onClose(event)

        if (autoReconnect && reconnectAttemptsRef.current < reconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1
            connect()
          }, reconnectInterval)
        }
      }

      ws.onerror = (event) => {
        setStatus("error")
        if (onError) onError(event)
        ws.close()
      }
    } catch (error) {
      console.error("Failed to connect WebSocket:", error)
      setStatus("error")
    }
  }, [url, onOpen, onMessage, onClose, onError, reconnectInterval, reconnectAttempts, autoReconnect])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const send = useCallback((data: string | ArrayBufferLike | Blob | ArrayBufferView) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data)
      return true
    }
    return false
  }, [])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return { status, data, send }
}
