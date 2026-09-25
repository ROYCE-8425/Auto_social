import React, { useState, useEffect } from 'react'
import { useAuth } from './lib/auth'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Overview } from './pages/Overview'
import { Inbox } from './pages/Inbox'
import { Customers } from './pages/Customers'
import { Tasks } from './pages/Tasks'
import { Trends } from './pages/Trends'
import { AuditLog } from './pages/AuditLog'
import { UsersPage } from './pages/Users'
import { TikTokPage } from './pages/TikTok'
import { OperationsHub } from './pages/OperationsHub'
import { CareScopeProvider } from './lib/scope'

export const App: React.FC = () => {
  const { user, isLoading } = useAuth()
  const [currentTab, setCurrentTab] = useState<string>('overview')

  // Handle URL hash changes (e.g. #inbox, #customers, #tiktok, #hub)
  useEffect(() => {
    const handleHash = () => {
      const raw = window.location.hash.replace('#', '')
      const tab = raw.split('?')[0]
      if (['overview', 'inbox', 'customers', 'tasks', 'hub', 'trends', 'audit', 'users', 'tiktok'].includes(tab)) {
        setCurrentTab(tab)
      }
    }
    handleHash()
    window.addEventListener('hashchange', handleHash)
    return () => window.removeEventListener('hashchange', handleHash)
  }, [])

  const handleSelectTab = (tab: string) => {
    setCurrentTab(tab)
    window.location.hash = tab
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-saoviet-600 to-saoviet-400 flex items-center justify-center text-white font-black text-2xl animate-pulse shadow-xl shadow-saoviet-500/20">
          JO
        </div>
        <p className="text-xs text-slate-400 font-semibold tracking-wider uppercase">
          Đang nạp Javis Ops...
        </p>
      </div>
    )
  }

  if (!user) {
    return <Login />
  }

  return (
    <CareScopeProvider>
      <Layout currentTab={currentTab} onSelectTab={handleSelectTab}>
        {currentTab === 'overview' && <Overview onNavigate={handleSelectTab} />}
        {currentTab === 'inbox' && <Inbox />}
        {currentTab === 'customers' && <Customers />}
        {currentTab === 'tasks' && <Tasks />}
        {currentTab === 'hub' && <OperationsHub />}
        {currentTab === 'trends' && <Trends />}
        {currentTab === 'tiktok' && <TikTokPage />}
        {currentTab === 'audit' && <AuditLog />}
        {currentTab === 'users' && <UsersPage />}
      </Layout>
    </CareScopeProvider>
  )
}
