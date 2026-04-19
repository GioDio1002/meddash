import type {
  AgentStatus,
  ChatMessage,
  Citation,
  DiagnosisCandidate,
  MedicationAlert,
  WorkflowTask,
} from './types'

export const metrics = {
  consultationsToday: 148,
  avgResponseSeconds: 18,
  triageAccuracy: 96.2,
  medicationInterventions: 14,
}

export const agentStatuses: AgentStatus[] = [
  {
    name: 'TriageAgent',
    state: 'running',
    currentTask: 'Classifying chest pain urgency',
    latencyMs: 840,
  },
  {
    name: 'KnowledgeRAGAgent',
    state: 'waiting',
    currentTask: 'Queued for evidence retrieval',
    latencyMs: 1240,
  },
  {
    name: 'MedicationSafetyAgent',
    state: 'blocked',
    currentTask: 'Awaiting allergy confirmation',
    latencyMs: 680,
  },
  {
    name: 'HandoffAgent',
    state: 'idle',
    currentTask: 'No active escalation',
    latencyMs: 210,
  },
]

export const consultationMessages: ChatMessage[] = [
  {
    id: 'm1',
    role: 'user',
    author: 'Patient',
    body: 'I have had chest tightness, dizziness, and shortness of breath for about 40 minutes.',
    at: '09:22',
  },
  {
    id: 'm2',
    role: 'agent',
    author: 'IntakeAgent',
    body: 'Collected symptom onset, severity, medication history, and cardiac risk factors. Waiting on allergy confirmation.',
    at: '09:23',
  },
  {
    id: 'm3',
    role: 'agent',
    author: 'TriageAgent',
    body: 'Escalation candidate: red-flag cardiopulmonary symptoms with acute onset. Emergency pathway recommended.',
    at: '09:24',
  },
]

export const citations: Citation[] = [
  {
    id: 'c1',
    title: 'ACC/AHA Acute Coronary Syndrome Guideline',
    sourceType: 'guideline',
    excerpt:
      'Immediate urgent evaluation is recommended for acute chest pain with dyspnea or presyncope.',
  },
  {
    id: 'c2',
    title: 'Aspirin Prescribing Information',
    sourceType: 'drug-label',
    excerpt:
      'Check hypersensitivity history and active gastrointestinal bleeding before recommendation.',
  },
  {
    id: 'c3',
    title: 'Internal Similar Case Review - ED Transfer',
    sourceType: 'case',
    excerpt:
      'Patients with chest tightness and dizziness were routed to urgent transfer pending ECG and troponin.',
  },
]

export const medicationAlerts: MedicationAlert[] = [
  {
    id: 'a1',
    severity: 'high',
    title: 'Aspirin recommendation blocked',
    detail: 'Allergy status is incomplete. Medication cannot be suggested until intolerance is ruled out.',
  },
  {
    id: 'a2',
    severity: 'medium',
    title: 'Beta blocker review',
    detail: 'Check baseline blood pressure and heart rate before adding rate-control guidance.',
  },
]

export const workflowTasks: WorkflowTask[] = [
  { id: 'w1', title: 'Chest pain intake packet', owner: 'AI', stage: 'done' },
  { id: 'w2', title: 'Urgency classification', owner: 'AI', stage: 'active' },
  { id: 'w3', title: 'ED handoff review', owner: 'Cardiology RN', stage: 'review' },
  { id: 'w4', title: 'Final disposition note', owner: 'Attending MD', stage: 'queued' },
]

export const diagnosisCandidates: DiagnosisCandidate[] = [
  {
    name: 'Acute coronary syndrome',
    confidence: 0.82,
    rationale: 'Symptom timing and red-flag cardiopulmonary presentation support immediate escalation.',
  },
  {
    name: 'Pulmonary embolism',
    confidence: 0.44,
    rationale: 'Dyspnea and acute onset remain concerning without a completed risk review.',
  },
  {
    name: 'Anxiety-related chest pain',
    confidence: 0.12,
    rationale: 'Not safe to prioritize before emergent causes are excluded.',
  },
]
