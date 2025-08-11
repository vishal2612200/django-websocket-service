import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocalStorageSession } from './useLocalStorageSession'
import { 
  getRedisMessagesPollingInterval, 
  getFallbackPollingInterval, 
  isRedisMessagesPollingEnabled, 
  isServerTriggeredPollingEnabled, 
  isFallbackPollingEnabled,
  getMessageHistoryLimit,
  isMessageHistoryLimitEnabled
} from '../config/api'

export type ConnectionStatus = 'connecting' | 'open' | 'closed'

// Message persistence interface
interface PersistedMessage {
  content: string
  timestamp: number
  sessionId: string
  isSent?: boolean
}

// Message display interface
interface DisplayMessage {
  content: string
  isSent: boolean
  timestamp: number
  id: string // Unique identifier to prevent duplicates
  isBroadcast?: boolean // Mark as broadcast message
  broadcastLevel?: 'info' | 'warning' | 'error' | 'success' // Broadcast message level
}

interface BroadcastMessage {
  type: 'broadcast'
  message: string
  title: string
  level: 'info' | 'warning' | 'error' | 'success'
  timestamp: number
}

export default function useWebSocket(
  path: string, 
  autoReconnect: boolean, 
  sessionId?: string, 
  persistMessages: boolean = true, 
  sessionPersistenceType: 'localStorage' | 'redis' | 'none' = 'none'
) {
  const [status, setStatus] = useState<ConnectionStatus>('connecting')
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [heartbeats, setHeartbeats] = useState<string[]>([])
  const [count, setCount] = useState<number>(0)
  const [lastHeartbeatAt, setLastHeartbeatAt] = useState<number | null>(null)
  const [nextRetryMs, setNextRetryMs] = useState<number | null>(null)
  const [heartbeatStats, setHeartbeatStats] = useState<{
    total: number
    missed: number
    avgLatency: number
    lastReceived: number | null
  }>({
    total: 0,
    missed: 0,
    avgLatency: 0,
    lastReceived: null
  })

  const localStorageSession = useLocalStorageSession()

  const wsRef = useRef<WebSocket | null>(null)
  const backoffRef = useRef(500)
  const isFetchingRef = useRef(false)
  const lastFetchTimeRef = useRef(0)

  const url = useMemo(() => {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const params = new URLSearchParams()
    if (sessionId) {
      params.append('session', sessionId)
    }
    if (sessionPersistenceType === 'redis') {
      params.append('redis_persistence', 'true')
      console.log(`Setting Redis persistence for session: ${sessionId}`)
    }
    const qs = params.toString()
    const finalUrl = `${proto}://${window.location.host}${path}${qs ? `?${qs}` : ''}`
    console.log(`WebSocket URL: ${finalUrl}`)
    return finalUrl
  }, [path, sessionId, sessionPersistenceType])

  // Load persisted messages and session data
  useEffect(() => {
    if (!sessionId) return
    
    console.log(`Loading data for session: ${sessionId}`)
    
    // Load messages if persistence is enabled
    if (persistMessages) {
      // For Redis persistence, fetch messages from API
      if (sessionPersistenceType === 'redis') {
        // Initial fetch only - no polling here
        fetchMessagesFromRedis(sessionId)
      } else {
        // Load from localStorage
        try {
          const persistedMessages = localStorage.getItem(`ui:messages:${sessionId}`)
          if (persistedMessages) {
            const parsed: PersistedMessage[] = JSON.parse(persistedMessages)
            console.log(`Found ${parsed.length} persisted messages for session ${sessionId}`)
            
            // Remove duplicates from persisted messages based on content only
            const uniqueMessages = parsed.reduce((acc: PersistedMessage[], current) => {
              const isDuplicate = acc.some(msg => msg.content === current.content)
              if (!isDuplicate) {
                acc.push(current)
              } else {
                console.warn('Duplicate message detected in localStorage:', current.content)
              }
              return acc
            }, [])
            
            // Sort by timestamp and convert to display format
            const sortedMessages = uniqueMessages
              .sort((a, b) => a.timestamp - b.timestamp) // Oldest first for proper display order
              .map(msg => ({
                content: msg.content,
                isSent: msg.isSent || false,
                timestamp: msg.timestamp,
                id: `${msg.timestamp}-${msg.content.slice(0, 10)}` // Create unique ID
              }))
            
            // Apply message limit if enabled
            const limitedMessages = isMessageHistoryLimitEnabled() 
              ? sortedMessages.slice(-getMessageHistoryLimit())
              : sortedMessages
            
            setMessages(limitedMessages)
            console.log(`Loaded ${limitedMessages.length} messages for session ${sessionId} (limit: ${getMessageHistoryLimit()})`)
            
            // Update localStorage with deduplicated messages
            if (uniqueMessages.length !== parsed.length) {
              const deduplicatedPersisted = uniqueMessages
                .sort((a, b) => a.timestamp - b.timestamp)
              // Apply limit to localStorage as well
              const limitedPersisted = isMessageHistoryLimitEnabled()
                ? deduplicatedPersisted.slice(-getMessageHistoryLimit())
                : deduplicatedPersisted
              localStorage.setItem(`ui:messages:${sessionId}`, JSON.stringify(limitedPersisted))
              console.log(`Removed ${parsed.length - uniqueMessages.length} duplicate messages from session ${sessionId}`)
            }
          } else {
            console.log(`No persisted messages found for session ${sessionId}`)
          }
        } catch (error) {
          console.warn('Failed to load persisted messages:', error)
        }
      }
    }
    
    // Load session data based on persistence type
    if (sessionPersistenceType === 'localStorage') {
      const sessionData = localStorageSession.getSession(sessionId)
      if (sessionData) {
        setCount(sessionData.count)
        console.log(`Session count loaded from localStorage: ${sessionData.count}`)
      } else {
        console.log(`No session data found for session ${sessionId}`)
      }
    }
  }, [sessionId, persistMessages, sessionPersistenceType, localStorageSession])

  // Separate useEffect for hybrid Redis polling
  useEffect(() => {
    if (!sessionId || sessionPersistenceType !== 'redis' || !persistMessages) {
      return
    }

    console.log(`Setting up hybrid Redis polling for session: ${sessionId}`)
    
    let fallbackInterval: number | null = null
    
    // Set up fallback polling (only if enabled)
    if (isFallbackPollingEnabled()) {
      fallbackInterval = setInterval(() => {
        console.log(`Fallback polling triggered for session: ${sessionId}`)
        fetchMessagesFromRedis(sessionId)
      }, getFallbackPollingInterval())
    }
    
    return () => {
      console.log(`Clearing hybrid Redis polling for session: ${sessionId}`)
      if (fallbackInterval) {
        clearInterval(fallbackInterval)
      }
    }
  }, [sessionId, sessionPersistenceType, persistMessages]) // Minimal dependencies

  // Function to fetch messages from Redis
  const fetchMessagesFromRedis = async (sessionId: string) => {
    // Skip if WebSocket is not connected
    if (status !== 'open') {
      console.log(`Skipping Redis fetch - WebSocket status: ${status}`)
      return
    }
    
    // Skip if we're already fetching (prevent concurrent requests)
    if (isFetchingRef.current) {
      console.log(`Skipping Redis fetch - already in progress`)
      return
    }
    
    // Skip if we fetched recently (debounce mechanism)
    const now = Date.now()
    const timeSinceLastFetch = now - lastFetchTimeRef.current
    const minInterval = 1000 // 1 second minimum interval
    
    if (timeSinceLastFetch < minInterval) {
      console.log(`Skipping Redis fetch - too soon (${timeSinceLastFetch}ms < ${minInterval}ms)`)
      return
    }
    
    isFetchingRef.current = true
    lastFetchTimeRef.current = now
    
    try {
      console.log(`Fetching messages from Redis for session: ${sessionId}`)
      const response = await fetch(`/chat/api/sessions/${sessionId}/messages/`)
      
      console.log(`Redis API response status: ${response.status}`)
      
      if (response.ok) {
        const data = await response.json()
        console.log(`Redis API response data:`, data)
        
        if (data.success && data.messages) {
          console.log(`Found ${data.messages.length} messages in Redis for session ${sessionId}`)
          
          // Convert Redis messages to display format with deduplication
          const uniqueMessages = data.messages.reduce((acc: any[], current: any) => {
            // Check if this content already exists
            // const isDuplicate = acc.some(msg => msg.content === current.content && msg.isSent === current.isSent)
            // if (!isDuplicate) {
              const messageObj: any = {
                content: current.content,
                isSent: current.isSent || false,
                timestamp: current.timestamp,
                id: `${current.timestamp}-${current.content.slice(0, 10)}`
              }
              
              // Add broadcast-specific fields if present
              if (current.isBroadcast) {
                messageObj.isBroadcast = true
                messageObj.broadcastLevel = current.broadcastLevel || 'info'
              }
              
              acc.push(messageObj)
            // } else {
            //   console.warn('Duplicate message detected in Redis:', current.content)
            // }
            return acc
          }, [])
          
          // Sort by timestamp (oldest first)
          uniqueMessages.sort((a: any, b: any) => b.timestamp - a.timestamp)
          
          // Apply message limit if enabled
          const limitedMessages = isMessageHistoryLimitEnabled()
            ? uniqueMessages.slice(-getMessageHistoryLimit())
            : uniqueMessages
          
          setMessages(limitedMessages)
          console.log(`Loaded ${limitedMessages.length} messages from Redis for session ${sessionId} (limit: ${getMessageHistoryLimit()})`)
        } else {
          console.log(`No messages found in Redis for session ${sessionId}`)
          setMessages([])
        }
      } else {
        const errorText = await response.text()
        console.warn(`Failed to fetch messages from Redis for session ${sessionId}: ${response.status} - ${errorText}`)
        setMessages([])
      }
    } catch (error) {
      console.error(`Error fetching messages from Redis for session ${sessionId}:`, error)
      setMessages([])
    } finally {
      // Always reset the fetching flag
      isFetchingRef.current = false
    }
  }

  // Helper function to apply message limit
  const applyMessageLimit = (messages: DisplayMessage[]) => {
    return isMessageHistoryLimitEnabled() 
      ? messages.slice(-getMessageHistoryLimit())
      : messages
  }

  // Persist messages to localStorage with deduplication
  const persistMessage = (content: string, isSent: boolean = false, isBroadcast: boolean = false) => {
    if (!sessionId || !persistMessages) return
    
    // Don't persist broadcast messages to localStorage when using Redis persistence
    // since they're already stored in Redis
    if (isBroadcast && sessionPersistenceType === 'redis') {
      console.log('Skipping localStorage persistence for broadcast message (using Redis)')
      return
    }
    
    try {
      const persistedMessages = localStorage.getItem(`ui:messages:${sessionId}`)
      const existing: PersistedMessage[] = persistedMessages ? JSON.parse(persistedMessages) : []
      
      // Check if this content already exists (regardless of isSent status)
      const isDuplicate = existing.some(msg => msg.content === content)
      
      if (isDuplicate) {
        console.warn('Duplicate content detected in persistence:', content)
        return
      }
      
      const newMessage: PersistedMessage = {
        content,
        timestamp: Date.now(),
        sessionId,
        isSent
      }
      
      const updated = [newMessage, ...existing]
      // Apply message limit if enabled
      const limitedUpdated = isMessageHistoryLimitEnabled()
        ? updated.slice(-getMessageHistoryLimit())
        : updated
      localStorage.setItem(`ui:messages:${sessionId}`, JSON.stringify(limitedUpdated))
    } catch (error) {
      console.warn('Failed to persist message:', error)
    }
  }

  // Clear persisted messages for this session
  const clearPersistedMessages = () => {
    if (!sessionId) return
    
    try {
      localStorage.removeItem(`ui:messages:${sessionId}`)
      setMessages([])
    } catch (error) {
      console.warn('Failed to clear persisted messages:', error)
    }
  }

  useEffect(() => {
    let cancelled = false

    function connect() {
      setStatus('connecting')
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setStatus('open')
        backoffRef.current = 500
        setNextRetryMs(null)
      }
      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data)
          if (data.ts) {
            const heartbeatTime = parseInt(data.ts)
            const now = Date.now()
            const latency = now - heartbeatTime
            
            // Debug logging
            console.log('Heartbeat received:', {
              serverTimestamp: data.ts,
              heartbeatTime,
              now,
              latency,
              latencySeconds: latency / 1000
            })
            
            // Store heartbeat with latency information
            setHeartbeats((h: string[]) => {
              // Check if this heartbeat timestamp is already in the list
              const existingTimestamps = h.map(heartbeatStr => {
                try {
                  const heartbeat = JSON.parse(heartbeatStr)
                  return heartbeat.timestamp
                } catch {
                  return heartbeatStr // fallback for old format
                }
              })
              
              if (existingTimestamps.includes(data.ts)) {
                console.warn('Duplicate heartbeat detected:', data.ts)
                return h
              }
              
              // Store timestamp and latency as JSON string
              const heartbeatData = JSON.stringify({
                timestamp: data.ts,
                latency: latency,
                receivedAt: now
              })
              return [heartbeatData, ...h].slice(0, 30)
            })
            setLastHeartbeatAt(heartbeatTime)
            
            // Update heartbeat statistics
            setHeartbeatStats((prev: any) => {
              const newTotal = prev.total + 1
              
              // Calculate average latency properly (not cumulative)
              const newAvgLatency = prev.avgLatency === 0 ? latency : 
                ((prev.avgLatency * prev.total) + latency) / newTotal
              
              // Calculate missed heartbeats
              const timeSinceLast = prev.lastReceived ? now - prev.lastReceived : 0
              const missed = prev.lastReceived ? Math.max(0, Math.floor(timeSinceLast / 30000) - 1) : 0
              
              return {
                total: newTotal,
                missed: prev.missed + missed,
                avgLatency: newAvgLatency,
                lastReceived: heartbeatTime
              }
            })
          } else if (typeof data.count === 'number') {
            // Store the original message content, not just the count
            const messageContent = typeof data.echo === 'string' && data.echo.length > 0 ? data.echo : `Server Message #${data.count}`
            const now = Date.now()
            const messageId = `${now}-${messageContent.slice(0, 10)}`
            
            // Check for duplicates before adding (by content only)
            setMessages((m: DisplayMessage[]) => {
              const isDuplicateByContent = m.some(msg => msg.content === messageContent)
              
              if (isDuplicateByContent) {
                console.warn('Duplicate content detected:', messageContent)
                return m
              }
              
              const receivedMessage: DisplayMessage = { 
                content: messageContent, 
                isSent: false, 
                timestamp: now,
                id: messageId
              }
              return applyMessageLimit([...m, receivedMessage])
            })
            
            // Persist the message
            persistMessage(messageContent, false)
            
            setCount(data.count)
            
            // Persist session data based on persistence type
            if (sessionId) {
              if (sessionPersistenceType === 'localStorage') {
                localStorageSession.updateSession(sessionId, {
                  count: data.count,
                  messages: messages.map((m: DisplayMessage) => m.content)
                })
              }
            }
          } else if (data.bye) {
            const byeMessage = `bye total=${data.total}`
            const now = Date.now()
            const messageId = `${now}-${byeMessage.slice(0, 10)}`
            
            setMessages((m: DisplayMessage[]) => {
              const isDuplicate = m.some(msg => msg.content === byeMessage)
              if (isDuplicate) return m
              
              const receivedMessage: DisplayMessage = { 
                content: byeMessage, 
                isSent: false, 
                timestamp: now,
                id: messageId
              }
              return applyMessageLimit([...m, receivedMessage])
            })
            persistMessage(byeMessage, false)
          }
        } catch {
          const now = Date.now()
          const messageId = `${now}-${ev.data.slice(0, 10)}`
          
          setMessages((m: DisplayMessage[]) => {
            const isDuplicate = m.some(msg => msg.content === ev.data)
            if (isDuplicate) return m
            
            const receivedMessage: DisplayMessage = { 
              content: ev.data, 
              isSent: false, 
              timestamp: now,
              id: messageId
            }
            return applyMessageLimit([...m, receivedMessage])
          })
          persistMessage(ev.data, false)
        }
      }
      ws.onclose = () => {
        setStatus('closed')
        if (!cancelled && autoReconnect) {
          const wait = Math.min(backoffRef.current, 10000)
          setTimeout(connect, wait)
          backoffRef.current = Math.min(wait * 2, 10000)
          setNextRetryMs(wait)
        }
      }
      ws.onerror = () => {
        setStatus('closed')
        ws.close()
      }
    }

    connect()
    return () => {
      cancelled = true
      wsRef.current?.close()
    }
  }, [url, autoReconnect])

  function send(text: string) {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(text)
      // Add sent message to display
      const now = Date.now()
      const messageId = `${now}-${text.slice(0, 10)}`
      
      setMessages((m: DisplayMessage[]) => {
        const isDuplicateByContent = m.some(msg => msg.content === text)
        
        if (isDuplicateByContent) {
          console.warn('Duplicate content detected:', text)
          return m
        }
        
        const sentMessage: DisplayMessage = { 
          content: text, 
          isSent: true, 
          timestamp: now,
          id: messageId
        }
                    const newMessages = applyMessageLimit([...m, sentMessage])
        
        // Persist session data based on persistence type
        if (sessionId && sessionPersistenceType === 'localStorage') {
          localStorageSession.updateSession(sessionId, {
            count: count + 1,
            messages: newMessages.map((msg: DisplayMessage) => msg.content)
          })
        }
        
        return newMessages
      })
      persistMessage(text, true)
    }
  }
  function reconnect() {
    try { 
      console.log('Manual reconnect triggered')
      // Close current connection
      wsRef.current?.close() 
      
      // Force immediate reconnection by creating a new WebSocket
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          console.log('Creating new WebSocket connection')
          const ws = new WebSocket(url)
          wsRef.current = ws
          
          ws.onopen = () => {
            setStatus('open')
            backoffRef.current = 500
            setNextRetryMs(null)
            console.log('Manual reconnect successful')
          }
          ws.onmessage = (ev) => {
            try {
              const data = JSON.parse(ev.data)
              if (data.ts) {
                const heartbeatTime = parseInt(data.ts)
                const now = Date.now()
                const latency = now - heartbeatTime
                
                setHeartbeats((h: string[]) => {
                  const existingTimestamps = h.map(heartbeatStr => {
                    try {
                      const heartbeat = JSON.parse(heartbeatStr)
                      return heartbeat.timestamp
                    } catch {
                      return heartbeatStr
                    }
                  })
                  
                  if (existingTimestamps.includes(data.ts)) {
                    return h
                  }
                  
                  const heartbeatData = JSON.stringify({
                    timestamp: data.ts,
                    latency: latency,
                    receivedAt: now
                  })
                  return [heartbeatData, ...h].slice(0, 30)
                })
                setLastHeartbeatAt(heartbeatTime)
                
                setHeartbeatStats((prev: any) => {
                  const newTotal = prev.total + 1
                  const newAvgLatency = prev.avgLatency === 0 ? latency : 
                    ((prev.avgLatency * prev.total) + latency) / newTotal
                  const timeSinceLast = prev.lastReceived ? now - prev.lastReceived : 0
                  const missed = prev.lastReceived ? Math.max(0, Math.floor(timeSinceLast / 30000) - 1) : 0
                  
                  return {
                    total: newTotal,
                    missed: prev.missed + missed,
                    avgLatency: newAvgLatency,
                    lastReceived: heartbeatTime
                  }
                })
              } else if (typeof data.count === 'number') {
                const messageContent = typeof data.echo === 'string' && data.echo.length > 0 ? data.echo : `Server Message #${data.count}`
                const now = Date.now()
                const messageId = `${now}-${messageContent.slice(0, 10)}`
                
                setMessages((m: DisplayMessage[]) => {
                  const isDuplicateByContent = m.some(msg => msg.content === messageContent)
                  
                  if (isDuplicateByContent) {
                    return m
                  }
                  
                  const receivedMessage: DisplayMessage = { 
                    content: messageContent, 
                    isSent: false, 
                    timestamp: now,
                    id: messageId
                  }
                  return applyMessageLimit([...m, receivedMessage])
                })
                
                persistMessage(messageContent, false)
                setCount(data.count)
                
                if (sessionId && sessionPersistenceType === 'localStorage') {
                  localStorageSession.updateSession(sessionId, {
                    count: data.count,
                    messages: messages.map((m: DisplayMessage) => m.content)
                  })
                }
              } else if (data.type === 'broadcast') {
                // Handle broadcast messages (deployment notifications, etc.)
                // Add broadcast messages directly to message history
                const broadcastContent = `[${data.title}] ${data.message}`
                const now = Date.now()
                const messageId = `${now}-${broadcastContent.slice(0, 10)}`
                
                setMessages((m: DisplayMessage[]) => {
                  // Check for duplicates based on message content and timestamp
                  const isDuplicate = m.some(msg => 
                    msg.content === broadcastContent && 
                    Math.abs(msg.timestamp - now) < 5000 // Within 5 seconds
                  )
                  if (isDuplicate) return m
                  
                  const receivedMessage: DisplayMessage = { 
                    content: broadcastContent, 
                    isSent: false, 
                    timestamp: now,
                    id: messageId,
                    isBroadcast: true, // Mark as broadcast message
                    broadcastLevel: data.level // Store the level for styling
                  }
                  return applyMessageLimit([...m, receivedMessage])
                })
                
                // Persist broadcast message
                persistMessage(broadcastContent, false, true)
              } else if (data.type === 'new_messages_available') {
                // Handle server notification that new messages are available in Redis
                console.log(`Server notification: new messages available for session ${data.sessionId}`)
                
                // Trigger immediate fetch from Redis
                if (isServerTriggeredPollingEnabled()) {
                  console.log(`Server-triggered polling for session: ${data.sessionId}`)
                  fetchMessagesFromRedis(data.sessionId)
                }
              } else if (data.bye) {
                const byeMessage = data.message || `Server shutdown - total messages: ${data.total}`
                const now = Date.now()
                const messageId = `${now}-${byeMessage.slice(0, 10)}`
                
                setMessages((m: DisplayMessage[]) => {
                  const isDuplicate = m.some(msg => msg.content === byeMessage)
                  if (isDuplicate) return m
                  
                  const receivedMessage: DisplayMessage = { 
                    content: byeMessage, 
                    isSent: false, 
                    timestamp: now,
                    id: messageId,
                    isBroadcast: true, // Mark as broadcast message
                    broadcastLevel: 'warning' // Shutdown is a warning
                  }
                  return applyMessageLimit([...m, receivedMessage])
                })
                persistMessage(byeMessage, false, true)
              }
            } catch {
              const now = Date.now()
              const messageId = `${now}-${ev.data.slice(0, 10)}`
              
              setMessages((m: DisplayMessage[]) => {
                const isDuplicate = m.some(msg => msg.content === ev.data)
                if (isDuplicate) return m
                
                const receivedMessage: DisplayMessage = { 
                  content: ev.data, 
                  isSent: false, 
                  timestamp: now,
                  id: messageId
                }
                return applyMessageLimit([...m, receivedMessage])
              })
              persistMessage(ev.data, false)
            }
          }
          ws.onclose = () => {
            setStatus('closed')
            if (autoReconnect) {
              const wait = Math.min(backoffRef.current, 10000)
              setTimeout(() => {
                if (wsRef.current?.readyState === WebSocket.CLOSED) {
                  const newWs = new WebSocket(url)
                  wsRef.current = newWs
                }
              }, wait)
              backoffRef.current = Math.min(wait * 2, 10000)
              setNextRetryMs(wait)
            }
          }
          ws.onerror = () => {
            setStatus('closed')
            ws.close()
          }
        }
      }, 100)
    } catch (error) {
      console.error('Error during reconnect:', error)
    }
  }

  // Manual refresh function for Redis messages
  const refreshMessages = () => {
    if (sessionId && sessionPersistenceType === 'redis' && persistMessages) {
      console.log(`Manual refresh requested for session: ${sessionId}`)
      fetchMessagesFromRedis(sessionId)
    }
  }

  return { 
    status, 
    messages, 
    heartbeats, 
    count, 
    send, 
    reconnect, 
    lastHeartbeatAt, 
    nextRetryMs,
    heartbeatStats,
    clearPersistedMessages,
    refreshMessages
  }
}


