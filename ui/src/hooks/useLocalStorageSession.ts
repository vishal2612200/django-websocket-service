import { useEffect, useState } from 'react'

export interface LocalStorageSessionData {
  id: string
  count: number
  lastActivity: number
  createdAt: number
  messages: string[]
}

export interface LocalStorageSessionManager {
  storeSession: (sessionId: string, data: Partial<LocalStorageSessionData>) => void
  getSession: (sessionId: string) => LocalStorageSessionData | null
  updateSession: (sessionId: string, data: Partial<LocalStorageSessionData>) => void
  deleteSession: (sessionId: string) => void
  getAllSessions: () => LocalStorageSessionData[]
  clearAllSessions: () => void
}

export function useLocalStorageSession(): LocalStorageSessionManager {
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    setIsInitialized(true)
  }, [])

  const storeSession = (sessionId: string, data: Partial<LocalStorageSessionData>) => {
    if (!isInitialized) return

    try {
      const key = `ui:session:${sessionId}`
      const now = Date.now()
      
      const sessionData: LocalStorageSessionData = {
        id: sessionId,
        count: data.count || 0,
        lastActivity: now,
        createdAt: data.createdAt || now,
        messages: data.messages || []
      }
      
      localStorage.setItem(key, JSON.stringify(sessionData))
      console.log(`Session stored in localStorage: ${sessionId}`)
    } catch (error) {
      console.warn('Failed to store session in localStorage:', error)
    }
  }

  const getSession = (sessionId: string): LocalStorageSessionData | null => {
    if (!isInitialized) return null

    try {
      const key = `ui:session:${sessionId}`
      const data = localStorage.getItem(key)
      
      if (data) {
        const sessionData = JSON.parse(data) as LocalStorageSessionData
        console.log(`Session loaded from localStorage: ${sessionId}`)
        return sessionData
      }
      
      return null
    } catch (error) {
      console.warn('Failed to get session from localStorage:', error)
      return null
    }
  }

  const updateSession = (sessionId: string, data: Partial<LocalStorageSessionData>) => {
    if (!isInitialized) return

    try {
      const key = `ui:session:${sessionId}`
      const existing = getSession(sessionId)
      const now = Date.now()
      
      const sessionData: LocalStorageSessionData = {
        id: sessionId,
        count: data.count ?? existing?.count ?? 0,
        lastActivity: now,
        createdAt: existing?.createdAt ?? now,
        messages: data.messages ?? existing?.messages ?? []
      }
      
      localStorage.setItem(key, JSON.stringify(sessionData))
      console.log(`Session updated in localStorage: ${sessionId}`)
    } catch (error) {
      console.warn('Failed to update session in localStorage:', error)
    }
  }

  const deleteSession = (sessionId: string) => {
    if (!isInitialized) return

    try {
      const key = `ui:session:${sessionId}`
      localStorage.removeItem(key)
      console.log(`Session deleted from localStorage: ${sessionId}`)
    } catch (error) {
      console.warn('Failed to delete session from localStorage:', error)
    }
  }

  const getAllSessions = (): LocalStorageSessionData[] => {
    if (!isInitialized) return []

    try {
      const sessions: LocalStorageSessionData[] = []
      const keys = Object.keys(localStorage)
      
      for (const key of keys) {
        if (key.startsWith('ui:session:')) {
          try {
            const data = localStorage.getItem(key)
            if (data) {
              const sessionData = JSON.parse(data) as LocalStorageSessionData
              sessions.push(sessionData)
            }
          } catch (error) {
            console.warn(`Failed to parse session data for key: ${key}`, error)
          }
        }
      }
      
      // Sort by last activity (most recent first)
      return sessions.sort((a, b) => b.lastActivity - a.lastActivity)
    } catch (error) {
      console.warn('Failed to get all sessions from localStorage:', error)
      return []
    }
  }

  const clearAllSessions = () => {
    if (!isInitialized) return

    try {
      const keys = Object.keys(localStorage)
      
      for (const key of keys) {
        if (key.startsWith('ui:session:')) {
          localStorage.removeItem(key)
        }
      }
      
      console.log('All sessions cleared from localStorage')
    } catch (error) {
      console.warn('Failed to clear all sessions from localStorage:', error)
    }
  }

  return {
    storeSession,
    getSession,
    updateSession,
    deleteSession,
    getAllSessions,
    clearAllSessions
  }
}
