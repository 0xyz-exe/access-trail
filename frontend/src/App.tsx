import { useEffect, useState } from 'react'
import {
  ShieldCheck,
  Users,
  KeyRound,
  FileCheck2,
  Undo2,
  AlertTriangle,
  History,
  Download,
  Upload,
  Play,
  RefreshCw,
  Search,
  ChevronRight,
  Database,
  CheckCircle2,
  XCircle,
  FileText
} from 'lucide-react'
import { api } from './api'
import {
  DashboardStats,
  Identity,
  EffectiveGrant,
  ReviewCampaign,
  ReviewItem,
  RevocationRequest,
  RiskFinding,
  AuditEvent,
  Connector,
  Policy,
  User
} from './types'

export default function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'identities' | 'reviews' | 'revocations' | 'findings' | 'audit' | 'governance' | 'reports'>('dashboard')
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // Module states
  const [identities, setIdentities] = useState<Identity[]>([])
  const [identitySearch, setIdentitySearch] = useState('')
  const [identityFilterType, setIdentityFilterType] = useState('')
  const [selectedIdentity, setSelectedIdentity] = useState<{ identity: Identity; grants: EffectiveGrant[] } | null>(null)

  const [campaigns, setCampaigns] = useState<ReviewCampaign[]>([])
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null)
  const [campaignItems, setCampaignItems] = useState<ReviewItem[]>([])

  const [revocations, setRevocations] = useState<RevocationRequest[]>([])
  const [findings, setFindings] = useState<RiskFinding[]>([])
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [auditVerification, setAuditVerification] = useState<{ total_events: number; is_valid: boolean; details: string } | null>(null)
  const [connectors, setConnectors] = useState<Connector[]>([])
  const [policies, setPolicies] = useState<Policy[]>([])

  const showNotice = (type: 'success' | 'error', message: string) => {
    setNotice({ type, message })
    setTimeout(() => setNotice(null), 4000)
  }

  // Initial auto-login with platform_owner demo credentials
  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true)
        const res = await api.login('admin@acme.corp', 'Password123!')
        setCurrentUser(res.user)
        await refreshAll()
      } catch (err: any) {
        showNotice('error', err.message || 'Failed to authenticate')
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  const switchUser = async (email: string) => {
    try {
      setLoading(true)
      const res = await api.login(email, 'Password123!')
      setCurrentUser(res.user)
      showNotice('success', `Switched role to: ${res.user.role} (${res.user.full_name})`)
      await refreshAll()
    } catch (err: any) {
      showNotice('error', err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const refreshAll = async () => {
    try {
      const [s, idns, camps, revs, fnds, logs, conns, pols, verify] = await Promise.all([
        api.getStats().catch(() => null),
        api.getIdentities().catch(() => []),
        api.getCampaigns().catch(() => []),
        api.getRevocations().catch(() => []),
        api.getFindings().catch(() => []),
        api.getAuditEvents().catch(() => []),
        api.getConnectors().catch(() => []),
        api.getPolicies().catch(() => []),
        api.verifyAuditChain().catch(() => null),
      ])
      if (s) setStats(s)
      setIdentities(idns)
      setCampaigns(camps)
      if (camps.length > 0 && !selectedCampaignId) {
        setSelectedCampaignId(camps[0].id)
        loadCampaignItems(camps[0].id)
      }
      setRevocations(revs)
      setFindings(fnds)
      setAuditEvents(logs)
      setConnectors(conns)
      setPolicies(pols)
      setAuditVerification(verify)
    } catch (e: any) {
      console.error(e)
    }
  }

  const loadCampaignItems = async (cid: string) => {
    try {
      const data = await api.getCampaignItems(cid)
      setCampaignItems(data.items)
    } catch (err: any) {
      showNotice('error', err.message)
    }
  }

  const handleDecision = async (grantId: string, identityId: string, decision: string) => {
    if (!selectedCampaignId) return
    try {
      await api.recordDecision({
        campaign_id: selectedCampaignId,
        identity_id: identityId,
        grant_id: grantId,
        decision,
        comments: `Reviewer verdict: ${decision.toUpperCase()} recorded.`,
      })
      showNotice('success', `Decision '${decision.toUpperCase()}' recorded.`)
      await loadCampaignItems(selectedCampaignId)
      await refreshAll()
    } catch (err: any) {
      showNotice('error', err.message)
    }
  }

  const handleExecuteRevocation = async (reqId: string) => {
    try {
      await api.executeRevocation(reqId)
      showNotice('success', `Revocation ${reqId} successfully executed across connector.`)
      await refreshAll()
    } catch (err: any) {
      showNotice('error', err.message)
    }
  }

  const handleScanRisks = async () => {
    try {
      setLoading(true)
      const res = await api.runRiskScan()
      showNotice('success', `Risk scan completed. ${res.length} deterministic findings generated.`)
      await refreshAll()
    } catch (err: any) {
      showNotice('error', err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyAudit = async () => {
    try {
      const res = await api.verifyAuditChain()
      setAuditVerification(res)
      if (res.is_valid) {
        showNotice('success', `Cryptographic chain valid: all ${res.total_events} events verified.`)
      } else {
        showNotice('error', `Integrity check failed: ${res.details}`)
      }
    } catch (err: any) {
      showNotice('error', err.message)
    }
  }

  const handleSyncConnector = async (id: string) => {
    try {
      await api.syncConnector(id)
      showNotice('success', `Connector ${id} synchronized successfully.`)
      await refreshAll()
    } catch (err: any) {
      showNotice('error', err.message)
    }
  }

  const handleExportEvidence = async () => {
    try {
      const pkg = await api.getEvidencePackage()
      const blob = new Blob([JSON.stringify(pkg, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `AccessTrail-Audit-Evidence-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      showNotice('success', 'Compliance audit evidence package exported.')
    } catch (err: any) {
      showNotice('error', err.message)
    }
  }

  const filteredIdentities = identities.filter((idn) => {
    const matchSearch =
      idn.username.toLowerCase().includes(identitySearch.toLowerCase()) ||
      idn.full_name.toLowerCase().includes(identitySearch.toLowerCase()) ||
      (idn.email && idn.email.toLowerCase().includes(identitySearch.toLowerCase()))
    const matchType = !identityFilterType || idn.identity_type === identityFilterType
    return matchSearch && matchType
  })

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/50 p-4 flex flex-col justify-between shrink-0">
        <div>
          <div className="flex items-center gap-3 px-2 py-3 border-b border-slate-800 mb-6">
            <div className="p-2 bg-blue-600/20 text-blue-400 rounded-lg border border-blue-500/30">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight text-white flex items-center gap-1.5">
                AccessTrail
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                  v0.1.0
                </span>
              </h1>
              <p className="text-xs text-slate-400">Identity & Access Review</p>
            </div>
          </div>

          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 px-3 mb-2">Governance Console</div>
          <nav className="space-y-1">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: ShieldCheck },
              { id: 'identities', label: 'Identity Inventory', icon: Users, badge: identities.length },
              { id: 'reviews', label: 'Access Reviews', icon: FileCheck2, badge: campaigns.length },
              { id: 'revocations', label: 'Revocation Center', icon: Undo2, badge: revocations.filter(r => r.status === 'requested').length },
              { id: 'findings', label: 'Risk Findings', icon: AlertTriangle, badge: findings.length },
              { id: 'audit', label: 'Audit Chain', icon: History },
              { id: 'governance', label: 'Policies & IdP', icon: Database },
              { id: 'reports', label: 'Evidence Package', icon: FileText },
            ].map((tab) => {
              const Icon = tab.icon
              const active = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition ${
                    active
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </div>
                  {tab.badge !== undefined && tab.badge > 0 && (
                    <span className={`text-[11px] px-1.5 py-0.2 rounded-full font-mono ${active ? 'bg-blue-500/30 text-white' : 'bg-slate-800 text-slate-400'}`}>
                      {tab.badge}
                    </span>
                  )}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Current Tenant & RBAC Profile */}
        <div className="pt-4 border-t border-slate-800">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
            <div className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold mb-1">Active Tenant</div>
            <div className="text-xs font-medium text-slate-300 truncate">Acme Financial Corp</div>
            <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between">
              <div className="truncate pr-1">
                <div className="text-xs font-semibold text-white truncate">{currentUser?.full_name || 'Loading...'}</div>
                <div className="text-[10px] text-blue-400 font-mono capitalize">{currentUser?.role.replace('_', ' ')}</div>
              </div>
            </div>

            {/* Quick Role Switcher for Demo & Testing */}
            <div className="mt-3">
              <label className="text-[10px] text-slate-400 block mb-1">Switch RBAC Persona:</label>
              <select
                className="w-full text-xs bg-slate-950 border border-slate-700 text-slate-300 rounded px-2 py-1 outline-none"
                value={currentUser?.email || ''}
                onChange={(e) => switchUser(e.target.value)}
              >
                <option value="admin@acme.corp">Alice Vance (Platform Owner)</option>
                <option value="secadmin@acme.corp">Marcus Ray (Security Admin)</option>
                <option value="reviewer@acme.corp">Elena Rostova (Access Reviewer)</option>
                <option value="auditor@acme.corp">David Thorne (External Auditor)</option>
                <option value="analyst@acme.corp">Sophie Lin (SOC Analyst)</option>
              </select>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top bar */}
        <header className="h-14 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/30 shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold capitalize text-slate-200">
              {activeTab === 'reviews' ? 'Access Reviews & Certification' : activeTab.replace('-', ' ')}
            </h2>
          </div>

          <div className="flex items-center gap-3">
            {/* Audit Chain Cryptographic Status Badge */}
            <button
              onClick={handleVerifyAudit}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition ${
                auditVerification?.is_valid
                  ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-400 hover:bg-emerald-900/30'
                  : 'bg-rose-950/40 border-rose-500/40 text-rose-400 hover:bg-rose-900/30'
              }`}
            >
              {auditVerification?.is_valid ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
              <span>Audit Chain: {auditVerification?.is_valid ? 'Tamper-Evident Verified' : 'Corrupted / Broken'}</span>
            </button>

            <button
              onClick={refreshAll}
              disabled={loading}
              className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title="Refresh Data"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </header>

        {/* Global Notice Toast */}
        {notice && (
          <div
            className={`mx-6 mt-4 p-3 rounded-lg border text-xs font-medium flex items-center gap-2 ${
              notice.type === 'success'
                ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300'
                : 'bg-rose-950/60 border-rose-500/40 text-rose-300'
            }`}
          >
            {notice.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            <span>{notice.message}</span>
          </div>
        )}

        <div className="p-6 space-y-6">
          {/* TAB 1: DASHBOARD */}
          {activeTab === 'dashboard' && stats && (
            <div className="space-y-6">
              {/* Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                    <span>Identities Monitored</span>
                    <Users className="w-4 h-4 text-blue-400" />
                  </div>
                  <div className="text-2xl font-bold text-white">{stats.total_identities}</div>
                  <div className="mt-1 text-xs text-slate-400 flex items-center gap-2">
                    <span className="text-emerald-400">{stats.active_identities} active</span>
                    <span>•</span>
                    <span className="text-amber-400">{stats.privileged_identities} privileged</span>
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                    <span>Active Entitlement Grants</span>
                    <KeyRound className="w-4 h-4 text-purple-400" />
                  </div>
                  <div className="text-2xl font-bold text-white">{stats.total_grants}</div>
                  <div className="mt-1 text-xs text-slate-400">Direct & Role-based associations</div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                    <span>Certification Campaigns</span>
                    <FileCheck2 className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div className="text-2xl font-bold text-white">{stats.active_campaigns}</div>
                  <div className="mt-1 text-xs text-slate-400 flex items-center gap-2">
                    <span className={stats.overdue_reviews > 0 ? 'text-rose-400 font-semibold' : 'text-slate-400'}>
                      {stats.overdue_reviews} overdue
                    </span>
                    <span>•</span>
                    <span className="text-amber-400">{stats.pending_revocations} pending revocations</span>
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                    <span>Excessive Privilege Findings</span>
                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                  </div>
                  <div className="text-2xl font-bold text-rose-400">{findings.length}</div>
                  <div className="mt-1 text-xs text-slate-400 flex items-center gap-2">
                    <span className="text-rose-500 font-semibold">{stats.critical_findings} critical</span>
                    <span>•</span>
                    <span className="text-amber-500">{stats.high_findings} high</span>
                  </div>
                </div>
              </div>

              {/* Security Health & Findings Quick Overview */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      Priority Deterministic Risk Findings
                    </h3>
                    <button
                      onClick={handleScanRisks}
                      className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 transition flex items-center gap-1.5"
                    >
                      <Play className="w-3 h-3 text-blue-400" />
                      Re-evaluate Rules
                    </button>
                  </div>

                  <div className="space-y-2.5">
                    {findings.slice(0, 4).map((f) => (
                      <div key={f.id} className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded font-mono ${
                                f.severity === 'critical'
                                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                  : f.severity === 'high'
                                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                  : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                              }`}
                            >
                              {f.severity}
                            </span>
                            <span className="text-xs font-semibold text-slate-200">{f.rule_name}</span>
                          </div>
                          <p className="text-xs text-slate-400">{f.evidence}</p>
                        </div>
                        <span className="text-[11px] text-slate-500 shrink-0 font-mono">Status: {f.status}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Cryptographic Chain Card */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-2">
                      <History className="w-4 h-4 text-blue-400" />
                      Tamper-Evident Audit Chain
                    </h3>
                    <p className="text-xs text-slate-400 mb-4">
                      Every administrative, access review, and permission change is cryptographically SHA-256 chained in canonical order.
                    </p>
                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2 font-mono text-[11px]">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Chained Events:</span>
                        <span className="text-slate-200">{auditEvents.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Latest Hash:</span>
                        <span className="text-blue-400 truncate max-w-[140px]">
                          {auditEvents[0]?.event_hash ? `${auditEvents[0].event_hash.slice(0, 16)}...` : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Integrity:</span>
                        <span className={auditVerification?.is_valid ? 'text-emerald-400' : 'text-rose-400'}>
                          {auditVerification?.is_valid ? '100% UNBROKEN' : 'CORRUPTED'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-slate-800 flex gap-2">
                    <button
                      onClick={handleVerifyAudit}
                      className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition"
                    >
                      Run Full Verification
                    </button>
                    <button
                      onClick={handleExportEvidence}
                      className="p-2 border border-slate-700 hover:bg-slate-800 text-slate-300 rounded-lg"
                      title="Export Evidence Package"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: IDENTITIES */}
          {activeTab === 'identities' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <div className="relative w-full sm:w-72">
                    <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      placeholder="Search username, name, email..."
                      value={identitySearch}
                      onChange={(e) => setIdentitySearch(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg pl-9 pr-3 py-2 text-slate-200 placeholder-slate-500 outline-none focus:border-blue-500"
                    />
                  </div>
                  <select
                    value={identityFilterType}
                    onChange={(e) => setIdentityFilterType(e.target.value)}
                    className="bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-2 text-slate-300 outline-none"
                  >
                    <option value="">All Identity Types</option>
                    <option value="human">Human Users</option>
                    <option value="admin">Administrators</option>
                    <option value="service_account">Service Accounts</option>
                    <option value="contractor">Contractors</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <a
                    href="/api/v1/identities/export/csv"
                    download
                    className="flex items-center gap-1.5 px-3 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg text-xs font-medium transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Safe CSV Export
                  </a>
                  <label className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium cursor-pointer transition">
                    <Upload className="w-3.5 h-3.5" />
                    Import CSV
                    <input
                      type="file"
                      accept=".csv"
                      className="hidden"
                      onChange={async (e) => {
                        const file = e.target.files?.[0]
                        if (file) {
                          try {
                            const res = await api.importCsv(file)
                            showNotice('success', `Imported ${res.created_count} identities successfully.`)
                            await refreshAll()
                          } catch (err: any) {
                            showNotice('error', err.message)
                          }
                        }
                      }}
                    />
                  </label>
                </div>
              </div>

              {/* Table */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/70 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                    <tr>
                      <th className="py-3 px-4">Identity</th>
                      <th className="py-3 px-4">Type</th>
                      <th className="py-3 px-4">Department</th>
                      <th className="py-3 px-4">Manager / Owner</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Risk Score</th>
                      <th className="py-3 px-4 text-right">Effective Access</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-normal">
                    {filteredIdentities.map((idn) => (
                      <tr key={idn.id} className="hover:bg-slate-800/30 transition">
                        <td className="py-3 px-4">
                          <div className="font-semibold text-white flex items-center gap-2">
                            {idn.full_name}
                            {idn.is_privileged && (
                              <span className="text-[10px] bg-amber-500/20 text-amber-400 border border-amber-500/30 px-1.5 py-0.2 rounded font-mono">
                                Privileged
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-slate-500 font-mono">{idn.username}</div>
                        </td>
                        <td className="py-3 px-4 font-mono capitalize text-slate-400">{idn.identity_type.replace('_', ' ')}</td>
                        <td className="py-3 px-4">{idn.department || '—'}</td>
                        <td className="py-3 px-4 text-slate-400">{idn.manager_email || <span className="text-rose-400 font-mono">None (Orphaned)</span>}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase font-mono ${
                              idn.status === 'active'
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {idn.status}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <span
                              className={`font-mono font-bold text-xs ${
                                idn.risk_score >= 60 ? 'text-rose-400' : idn.risk_score >= 20 ? 'text-amber-400' : 'text-slate-400'
                              }`}
                            >
                              {idn.risk_score}
                            </span>
                            <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${idn.risk_score >= 60 ? 'bg-rose-500' : idn.risk_score >= 20 ? 'bg-amber-500' : 'bg-blue-500'}`}
                                style={{ width: `${idn.risk_score}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={async () => {
                              const details = await api.getIdentityDetails(idn.id)
                              setSelectedIdentity(details)
                            }}
                            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[11px] font-medium border border-slate-700 transition"
                          >
                            Inspect Grants
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Identity Detail Modal */}
              {selectedIdentity && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
                  <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 space-y-4 shadow-2xl">
                    <div className="flex items-start justify-between border-b border-slate-800 pb-3">
                      <div>
                        <h3 className="text-base font-bold text-white flex items-center gap-2">
                          {selectedIdentity.identity.full_name}
                          {selectedIdentity.identity.is_privileged && (
                            <span className="text-[10px] bg-amber-500/20 text-amber-400 border border-amber-500/30 px-1.5 py-0.5 rounded font-mono">
                              Privileged
                            </span>
                          )}
                        </h3>
                        <p className="text-xs text-slate-400 font-mono">
                          {selectedIdentity.identity.username} • {selectedIdentity.identity.email || 'No email'}
                        </p>
                      </div>
                      <button
                        onClick={() => setSelectedIdentity(null)}
                        className="text-slate-500 hover:text-white text-lg font-bold"
                      >
                        ✕
                      </button>
                    </div>

                    <div>
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Effective Permissions & Entitlements</h4>
                      <div className="space-y-2 max-h-72 overflow-y-auto">
                        {selectedIdentity.grants.length === 0 ? (
                          <div className="text-xs text-slate-500 p-4 text-center">No active permissions assigned.</div>
                        ) : (
                          selectedIdentity.grants.map((g) => (
                            <div key={g.id} className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between text-xs">
                              <div>
                                <div className="font-semibold text-slate-200 flex items-center gap-2">
                                  <span>{g.application_name}</span>
                                  <ChevronRight className="w-3 h-3 text-slate-600" />
                                  <span className="text-blue-400">{g.entitlement_name || g.role_name}</span>
                                </div>
                                <div className="text-[11px] text-slate-500 mt-0.5">
                                  Provenance: {g.is_direct ? 'Direct Grant' : 'Inherited Role'} • Granted: {g.grant_date.split('T')[0]}
                                  {g.justification && ` • Justification: ${g.justification}`}
                                </div>
                              </div>
                              <span
                                className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded ${
                                  g.risk_level === 'critical'
                                    ? 'bg-rose-500/20 text-rose-400'
                                    : g.risk_level === 'high'
                                    ? 'bg-amber-500/20 text-amber-400'
                                    : 'bg-blue-500/20 text-blue-400'
                                }`}
                              >
                                {g.risk_level}
                              </span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    <div className="flex justify-end pt-2">
                      <button
                        onClick={() => setSelectedIdentity(null)}
                        className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
                      >
                        Close
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: ACCESS REVIEWS */}
          {activeTab === 'reviews' && (
            <div className="space-y-6">
              {/* Campaign Selector / Progress */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {campaigns.map((cmp) => {
                  const pct = cmp.total_items > 0 ? Math.round((cmp.reviewed_items / cmp.total_items) * 100) : 100
                  const active = selectedCampaignId === cmp.id
                  return (
                    <div
                      key={cmp.id}
                      onClick={() => {
                        setSelectedCampaignId(cmp.id)
                        loadCampaignItems(cmp.id)
                      }}
                      className={`cursor-pointer p-4 rounded-xl border transition ${
                        active ? 'bg-slate-900 border-blue-500 shadow-md' : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-bold text-white truncate">{cmp.name}</span>
                        <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono uppercase ${cmp.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}`}>
                          {cmp.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 line-clamp-2 mb-3">{cmp.description}</p>
                      <div>
                        <div className="flex justify-between text-[11px] text-slate-500 font-mono mb-1">
                          <span>Progress: {cmp.reviewed_items} / {cmp.total_items} items</span>
                          <span>{pct}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Active Review Certification Workbench */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="text-sm font-semibold text-white">Certification Workbench</h3>
                    <p className="text-xs text-slate-400">Review privileged entitlements and submit audit-binding certification verdicts.</p>
                  </div>
                  <div className="text-xs text-slate-500 font-mono">
                    Enforcing: Separation of Duties (Anti-Self Approval)
                  </div>
                </div>

                <div className="space-y-3">
                  {campaignItems.length === 0 ? (
                    <div className="p-8 text-center text-xs text-slate-500">No review items in scope.</div>
                  ) : (
                    campaignItems.map((item) => (
                      <div
                        key={item.grant_id}
                        className="p-4 bg-slate-950 border border-slate-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-white">{item.full_name}</span>
                            <span className="text-[11px] text-slate-500 font-mono">({item.username})</span>
                            {item.is_privileged && (
                              <span className="text-[10px] bg-amber-500/20 text-amber-400 px-1.5 py-0.2 rounded font-mono">
                                Privileged
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-slate-300 flex items-center gap-2">
                            <span className="text-slate-400 font-medium">{item.application_name}:</span>
                            <span className="text-blue-400 font-mono font-semibold">{item.entitlement_name}</span>
                            <span className="text-slate-600">•</span>
                            <span className="text-slate-500 font-mono text-[11px] capitalize">{item.permission_type}</span>
                          </div>
                          {item.decision && (
                            <div className="text-[11px] font-mono mt-1">
                              Status:{' '}
                              <span className={item.decision === 'approve' ? 'text-emerald-400 font-bold uppercase' : 'text-rose-400 font-bold uppercase'}>
                                {item.decision}
                              </span>
                              {item.decision_comment && <span className="text-slate-400"> — {item.decision_comment}</span>}
                            </div>
                          )}
                        </div>

                        {/* Decision Action Buttons */}
                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            onClick={() => handleDecision(item.grant_id, item.identity_id, 'approve')}
                            className="px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600 text-emerald-300 hover:text-white border border-emerald-500/40 rounded-lg text-xs font-semibold transition"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleDecision(item.grant_id, item.identity_id, 'revoke')}
                            className="px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/40 rounded-lg text-xs font-semibold transition"
                          >
                            Revoke Access
                          </button>
                          <button
                            onClick={() => handleDecision(item.grant_id, item.identity_id, 'escalate')}
                            className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-lg text-xs transition"
                          >
                            Escalate
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: REVOCATION CENTER */}
          {activeTab === 'revocations' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">Revocation Workflow & Execution Center</h3>
                  <p className="text-xs text-slate-400">Tracks revocation requests resulting from certification reviews and executes idempotent de-provisioning.</p>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/70 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                    <tr>
                      <th className="py-3 px-4">Request ID</th>
                      <th className="py-3 px-4">Target Identity / System</th>
                      <th className="py-3 px-4">Grant ID</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Created Date</th>
                      <th className="py-3 px-4 text-right">Execution Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {revocations.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="text-center py-8 text-slate-500 text-xs">
                          No revocation requests currently queued.
                        </td>
                      </tr>
                    ) : (
                      revocations.map((rev) => (
                        <tr key={rev.id} className="hover:bg-slate-800/30 transition">
                          <td className="py-3 px-4 font-mono font-semibold text-white">{rev.id}</td>
                          <td className="py-3 px-4">
                            <div className="font-medium text-slate-200">{rev.identity_id}</div>
                            <div className="text-[11px] text-slate-500 font-mono">System: {rev.target_system}</div>
                          </td>
                          <td className="py-3 px-4 font-mono text-slate-400">{rev.grant_id}</td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
                                rev.status === 'completed'
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                  : rev.status === 'failed'
                                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                              }`}
                            >
                              {rev.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">{rev.created_at.split('T')[0]}</td>
                          <td className="py-3 px-4 text-right">
                            {rev.status !== 'completed' ? (
                              <button
                                onClick={() => handleExecuteRevocation(rev.id)}
                                className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs font-semibold shadow-sm transition"
                              >
                                Execute Revocation
                              </button>
                            ) : (
                              <span className="text-[11px] text-emerald-400 font-mono flex items-center justify-end gap-1">
                                <CheckCircle2 className="w-3.5 h-3.5" /> De-provisioned
                              </span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: RISK FINDINGS */}
          {activeTab === 'findings' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">Excessive Privilege & Risk Engine</h3>
                  <p className="text-xs text-slate-400">Deterministic detection rules identifying orphaned accounts, dormant admins, and ungoverned grants.</p>
                </div>
                <button
                  onClick={handleScanRisks}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition flex items-center gap-1.5"
                >
                  <Play className="w-3.5 h-3.5" />
                  Execute Full Scan
                </button>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {findings.map((f) => (
                  <div key={f.id} className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded font-mono ${
                            f.severity === 'critical'
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : f.severity === 'high'
                              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                              : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          }`}
                        >
                          {f.severity}
                        </span>
                        <span className="text-xs font-bold text-white">{f.rule_name}</span>
                        {f.identity_id && (
                          <span className="text-[11px] text-slate-500 font-mono">Target: {f.identity_id}</span>
                        )}
                      </div>
                      <span className="text-xs text-slate-400 font-mono">{f.created_at.split('T')[0]}</span>
                    </div>

                    <p className="text-xs text-slate-300">{f.evidence}</p>

                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 text-xs text-slate-400 flex items-center gap-2">
                      <span className="font-semibold text-slate-300">Suggested Remediation:</span>
                      <span>{f.remediation}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 6: AUDIT CHAIN */}
          {activeTab === 'audit' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">Cryptographic Tamper-Evident Audit Trail</h3>
                  <p className="text-xs text-slate-400">Append-only SHA-256 chained security event ledger.</p>
                </div>
                <button
                  onClick={handleVerifyAudit}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Verify Full Hash Chain
                </button>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/70 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                    <tr>
                      <th className="py-3 px-4">Timestamp</th>
                      <th className="py-3 px-4">Actor</th>
                      <th className="py-3 px-4">Action</th>
                      <th className="py-3 px-4">Target Entity</th>
                      <th className="py-3 px-4">Event Hash (SHA-256)</th>
                      <th className="py-3 px-4">Prev Hash</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    {auditEvents.map((e) => (
                      <tr key={e.id} className="hover:bg-slate-800/30 transition">
                        <td className="py-3 px-4 text-slate-400 whitespace-nowrap">{e.timestamp.replace('T', ' ').slice(0, 19)}</td>
                        <td className="py-3 px-4 text-slate-200">{e.actor_name}</td>
                        <td className="py-3 px-4 text-blue-400 font-semibold">{e.action}</td>
                        <td className="py-3 px-4 text-slate-300">{e.target_entity}</td>
                        <td className="py-3 px-4 text-emerald-400 truncate max-w-[140px]" title={e.event_hash}>
                          {e.event_hash.slice(0, 16)}...
                        </td>
                        <td className="py-3 px-4 text-slate-500 truncate max-w-[140px]" title={e.prev_hash}>
                          {e.prev_hash.slice(0, 16)}...
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 7: GOVERNANCE & CONNECTORS */}
          {activeTab === 'governance' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Policies */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-blue-400" />
                  Active Governance Policies
                </h3>
                <div className="space-y-3">
                  {policies.map((p) => (
                    <div key={p.id} className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-200">{p.name}</span>
                        <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.2 rounded font-mono uppercase">
                          Enforced
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 font-mono">Rule Type: {p.rule_type}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Connectors */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Database className="w-4 h-4 text-purple-400" />
                  Identity Providers & System Connectors
                </h3>
                <div className="space-y-3">
                  {connectors.map((c) => (
                    <div key={c.id} className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between">
                      <div>
                        <div className="text-xs font-bold text-slate-200">{c.name}</div>
                        <div className="text-[11px] text-slate-500 font-mono">
                          Type: {c.connector_type} • Synced records: {c.sync_count}
                        </div>
                      </div>
                      <button
                        onClick={() => handleSyncConnector(c.id)}
                        className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs font-medium border border-slate-700 transition"
                      >
                        Trigger Sync
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 8: REPORTS & EVIDENCE */}
          {activeTab === 'reports' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6 max-w-2xl">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-400" />
                  Audit Evidence Export & Compliance Package
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Generate signed evidence bundles documenting completed certification campaigns, reviewer verdicts, de-provisioning records, and cryptographic audit integrity verification.
                </p>
              </div>

              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3 text-xs">
                <div className="font-semibold text-slate-300">Package Inclusions:</div>
                <ul className="list-disc list-inside space-y-1 text-slate-400 font-mono text-[11px]">
                  <li>Campaign manifests & review progress metrics</li>
                  <li>Attributed reviewer decisions & rationales</li>
                  <li>Revocation audit receipts & timestamps</li>
                  <li>Cryptographic SHA-256 chain verification stamp</li>
                  <li>Sanitized CSV & JSON data dumps</li>
                </ul>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleExportEvidence}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-sm transition"
                >
                  <Download className="w-4 h-4" />
                  Download Evidence Package (.json)
                </button>
                <a
                  href="/api/v1/identities/export/csv"
                  download
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold flex items-center gap-2 border border-slate-700 transition"
                >
                  <Download className="w-4 h-4" />
                  Download Identities (.csv)
                </a>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
