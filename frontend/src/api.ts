import { DashboardStats, Identity, EffectiveGrant, ReviewCampaign, ReviewItem, RevocationRequest, RiskFinding, AuditEvent, Connector, Policy, User } from './types'

const API_BASE = '/api/v1'

let authToken = localStorage.getItem('accesstrail_token') || ''

export const setAuthToken = (token: string) => {
  authToken = token
  localStorage.setItem('accesstrail_token', token)
}

export const getAuthToken = () => authToken

const request = async <T>(path: string, options: RequestInit = {}): Promise<T> => {
  const headers = new Headers(options.headers || {})
  if (authToken) {
    headers.set('Authorization', `Bearer ${authToken}`)
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    let errMessage = `HTTP ${res.status}: ${res.statusText}`
    try {
      const body = await res.json()
      if (body.detail) errMessage = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      // ignore
    }
    throw new Error(errMessage)
  }

  return res.json()
}

export const api = {
  login: async (email: string, password: string): Promise<{ access_token: string; user: User }> => {
    const data = await request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    setAuthToken(data.access_token)
    return data
  },

  getMe: () => request<User>('/auth/me'),

  getStats: () => request<DashboardStats>('/dashboard/stats'),

  getIdentities: (params: { search?: string; type?: string; status?: string; privileged?: boolean } = {}) => {
    const q = new URLSearchParams()
    if (params.search) q.set('search', params.search)
    if (params.type) q.set('identity_type', params.type)
    if (params.status) q.set('status', params.status)
    if (params.privileged !== undefined) q.set('is_privileged', String(params.privileged))
    return request<Identity[]>(`/identities?${q.toString()}`)
  },

  getIdentityDetails: (id: string) => request<{ identity: Identity; grants: EffectiveGrant[] }>(`/identities/${id}`),

  getCampaigns: () => request<ReviewCampaign[]>('/access-reviews/campaigns'),

  getCampaignItems: (id: string) => request<{ campaign: ReviewCampaign; items: ReviewItem[] }>(`/access-reviews/campaigns/${id}/items`),

  recordDecision: (data: { campaign_id: string; identity_id: string; grant_id: string; decision: string; comments?: string }) =>
    request('/access-reviews/decisions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  getRevocations: () => request<RevocationRequest[]>('/revocations'),

  executeRevocation: (id: string) =>
    request<RevocationRequest>(`/revocations/${id}/execute`, {
      method: 'POST',
    }),

  getFindings: () => request<RiskFinding[]>('/findings'),

  runRiskScan: () => request<RiskFinding[]>('/findings/scan', { method: 'POST' }),

  getAuditEvents: () => request<AuditEvent[]>('/audit-logs'),

  verifyAuditChain: () => request<{ total_events: number; is_valid: boolean; broken_event_id?: string; details: string }>('/audit-logs/verify'),

  getConnectors: () => request<Connector[]>('/connectors'),

  syncConnector: (id: string) => request(`/connectors/${id}/sync`, { method: 'POST' }),

  getPolicies: () => request<Policy[]>('/policies'),

  getEvidencePackage: () => request<any>('/reports/evidence-package'),

  importCsv: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const headers = new Headers()
    if (authToken) headers.set('Authorization', `Bearer ${authToken}`)
    const res = await fetch(`${API_BASE}/identities/import/csv`, {
      method: 'POST',
      headers,
      body: formData,
    })
    if (!res.ok) throw new Error(`Import failed: ${res.statusText}`)
    return res.json()
  },
}
