import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api, CareConfig, CareState } from './api'

export type ScopeType = 'all' | 'brand' | 'page'

export interface CareScopeContextType {
  scope: ScopeType
  scopeBrand: string
  scopePageId: string
  eligiblePages: NonNullable<CareState['eligible_pages']>
  careConfig: CareConfig | null
  careState: CareState | null
  loading: boolean
  scopedPageIds: string[]
  activeBrand: 'all' | 'bsn' | 'saoviet' | 'page'
  scopeLabel: string
  setScope: (scope: ScopeType, scopeBrand?: string, scopePageId?: string) => Promise<void>
  refreshScopeState: () => Promise<void>
}

const CareScopeContext = createContext<CareScopeContextType | null>(null)

export const CareScopeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [scope, setScopeState] = useState<ScopeType>('all')
  const [scopeBrand, setScopeBrand] = useState<string>('')
  const [scopePageId, setScopePageId] = useState<string>('')
  const [careState, setCareState] = useState<CareState | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  const refreshScopeState = useCallback(async () => {
    try {
      const state = await api.getCareState()
      setCareState(state)
      if (state?.config) {
        if (state.config.scope) setScopeState(state.config.scope as ScopeType)
        if (state.config.scope_brand !== undefined) setScopeBrand(state.config.scope_brand)
        if (state.config.scope_page_id !== undefined) setScopePageId(state.config.scope_page_id)
      }
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshScopeState()
    const t = setInterval(refreshScopeState, 30000)
    return () => clearInterval(t)
  }, [refreshScopeState])

  const setScope = async (newScope: ScopeType, newBrand = '', newPageId = '') => {
    setScopeState(newScope)
    setScopeBrand(newBrand)
    setScopePageId(newPageId)

    try {
      await api.saveCareSettings({
        scope: newScope,
        scope_brand: newBrand,
        scope_page_id: newPageId,
      })
      await refreshScopeState()
    } catch (e) {
      console.error('Lỗi lưu phạm vi:', e)
    }
  }

  const eligiblePages = careState?.eligible_pages || []

  // Compute page IDs matching the active scope
  const scopedPageIds: string[] = (() => {
    if (scope === 'brand') {
      const b = scopeBrand.toLowerCase().trim()
      return eligiblePages
        .filter((p) => (p.brand || '').toLowerCase().trim() === b)
        .map((p) => p.page_id || p.id || '')
        .filter(Boolean)
    }
    if (scope === 'page' && scopePageId) {
      return [scopePageId]
    }
    return eligiblePages.map((p) => p.page_id || p.id || '').filter(Boolean)
  })()

  const activeBrand: 'all' | 'bsn' | 'saoviet' | 'page' = (() => {
    if (scope === 'brand') {
      return scopeBrand === 'bsn' ? 'bsn' : 'saoviet'
    }
    if (scope === 'page') {
      const p = eligiblePages.find((x) => (x.page_id || x.id) === scopePageId)
      return (p?.brand as any) || 'page'
    }
    return 'all'
  })()

  const scopeLabel: string = (() => {
    if (scope === 'brand') {
      return scopeBrand === 'bsn' ? 'Nhóm Game BSN' : 'Nhóm Sao Việt'
    }
    if (scope === 'page' && scopePageId) {
      const p = eligiblePages.find((x) => (x.page_id || x.id) === scopePageId)
      return p ? p.name : `Page ${scopePageId.slice(-6)}`
    }
    return 'Tất cả Fanpage'
  })()

  return (
    <CareScopeContext.Provider
      value={{
        scope,
        scopeBrand,
        scopePageId,
        eligiblePages,
        careConfig: careState?.config || null,
        careState,
        loading,
        scopedPageIds,
        activeBrand,
        scopeLabel,
        setScope,
        refreshScopeState,
      }}
    >
      {children}
    </CareScopeContext.Provider>
  )
}

export const useCareScope = () => {
  const ctx = useContext(CareScopeContext)
  if (!ctx) {
    throw new Error('useCareScope must be used within a CareScopeProvider')
  }
  return ctx
}
