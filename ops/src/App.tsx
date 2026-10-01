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
import { PublishingPage, SocialChannelsPage } from './pages/Publishing'
import { SettingsPage } from './pages/Settings'
import { OperationsHub } from './pages/OperationsHub'
import { OrdersPage } from './pages/Orders'
import { DocumentsPage } from './pages/Documents'
import { ProductCatalogSettings } from './components/ProductCatalogSettings'
import { AutomationRulesSettings } from './components/AutomationRulesSettings'
import { CareScopeProvider } from './lib/scope'

export const App: React.FC = () => {
  const { user, isLoading } = useAuth()
  const [currentTab, setCurrentTab] = useState<string>('overview')

  // Handle URL hash changes (e.g. #/inbox, #/orders, #/tasks, etc.)
  useEffect(() => {
    const handleHash = () => {
      const raw = window.location.hash.replace(/^#\/?/, '')
      const tab = raw.split('?')[0]
      if (['overview', 'inbox', 'orders', 'customers', 'products', 'automation', 'tasks', 'hub', 'documents', 'trends', 'audit', 'users', 'tiktok', 'channels', 'publishing', 'settings'].includes(tab)) {
        setCurrentTab(tab)
      }
    }
    handleHash()
    window.addEventListener('hashchange', handleHash)
    return () => window.removeEventListener('hashchange', handleHash)
  }, [])

  const handleSelectTab = (tab: string) => {
    setCurrentTab(tab)
    window.location.hash = `#/${tab}`
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-saoviet-600 to-saoviet-400 flex items-center justify-center text-white font-black text-2xl animate-pulse shadow-xl shadow-saoviet-500/20">
          ST
        </div>
        <p className="text-xs text-slate-400 font-semibold tracking-wider uppercase">
          Đang nạp Sèo Trum Ops...
        </p>
      </div>
    )
  }

  // Yêu cầu đăng nhập an toàn khi chưa xác thực
  if (!user) return <Login />

  return (
    <CareScopeProvider>
      <Layout currentTab={currentTab} onSelectTab={handleSelectTab}>
        {currentTab === 'overview' && <Overview onNavigate={handleSelectTab} />}
        {currentTab === 'inbox' && <Inbox />}
        {currentTab === 'orders' && <OrdersPage />}
        {currentTab === 'customers' && <Customers />}
        {currentTab === 'products' && (
          <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs animate-fade-in">
            <ProductCatalogSettings />
          </div>
        )}
        {currentTab === 'automation' && (
          <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs animate-fade-in">
            <AutomationRulesSettings />
          </div>
        )}
        {currentTab === 'tasks' && <Tasks />}
        {currentTab === 'hub' && <OperationsHub onNavigate={handleSelectTab} />}
        {currentTab === 'documents' && <DocumentsPage />}
        {currentTab === 'trends' && <Trends />}
        {(currentTab === 'publishing' || currentTab === 'tiktok' || currentTab === 'channels') && <PublishingPage />}
        {currentTab === 'audit' && <AuditLog />}
        {currentTab === 'users' && <UsersPage />}
        {currentTab === 'settings' && <SettingsPage />}
      </Layout>
    </CareScopeProvider>
  )
}
