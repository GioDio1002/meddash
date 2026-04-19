export type AgentStatus = {
  name: string
  state: 'idle' | 'running' | 'blocked' | 'waiting'
  currentTask: string
  latencyMs: number
}

export type ChatMessage = {
  id: string
  role: 'user' | 'agent'
  author: string
  body: string
  at: string
}

export type Citation = {
  id: string
  title: string
  sourceType: 'guideline' | 'drug-label' | 'case'
  excerpt: string
}

export type MedicationAlert = {
  id: string
  severity: 'high' | 'medium' | 'low'
  title: string
  detail: string
}

export type WorkflowTask = {
  id: string
  title: string
  owner: string
  stage: 'queued' | 'active' | 'review' | 'done'
}

export type DiagnosisCandidate = {
  name: string
  confidence: number
  rationale: string
}

export type SessionStatus = 'active' | 'needs_handoff' | 'completed'

export type BackendCitation = {
  citation_id: string
  title: string
  source_type: 'guideline' | 'drug_label' | 'case'
  snippet: string
  relevance: number
}

export type BackendMedicationAlert = {
  alert_id: string
  medication: string
  severity: 'info' | 'warning' | 'blocking'
  message: string
}

export type BackendDiagnosisCandidate = {
  label: string
  confidence: number
  rationale: string
}

export type BackendWorkflowEvent = {
  event_id: string
  session_id: string
  step: string
  agent: string
  state: 'idle' | 'running' | 'completed'
  detail: string
  payload: Record<string, unknown>
  created_at: string
}

export type BackendSession = {
  session_id: string
  patient: {
    patient_id: string
    full_name: string | null
    age: number | null
    allergies: string[]
  }
  status: SessionStatus
  messages: {
    message_id: string
    role: 'patient' | 'assistant' | 'system' | 'agent'
    content: string
    created_at: string
  }[]
  intake: {
    symptoms: string[]
    allergies: string[]
    red_flags: string[]
  }
  triage: {
    department: string
    urgency: 'low' | 'medium' | 'high' | 'critical'
    rationale: string
    handoff_required: boolean
  }
  citations: BackendCitation[]
  medication_alerts: BackendMedicationAlert[]
  care_plan: null | {
    summary: string
    differential: BackendDiagnosisCandidate[]
    recommended_tests: string[]
    follow_up_plan: string
    citations: BackendCitation[]
    medication_alerts: BackendMedicationAlert[]
  }
  workflow_events: BackendWorkflowEvent[]
}
