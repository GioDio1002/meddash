import {
  Alert,
  Avatar,
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  Form,
  Input,
  message,
  Progress,
  Row,
  Select,
  Space,
  Statistic,
  Steps,
  Tabs,
  Tag,
  Timeline,
  Typography,
} from 'antd'
import {
  AlertOutlined,
  ApartmentOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DashboardOutlined,
  ExperimentOutlined,
  FileSearchOutlined,
  MedicineBoxOutlined,
  RadarChartOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useMutation, useQuery } from '@tanstack/react-query'
import { startTransition, useDeferredValue, useEffect, useMemo, useState } from 'react'
import './App.css'
import {
  agentStatuses,
  citations,
  consultationMessages,
  diagnosisCandidates,
  medicationAlerts,
  metrics,
  workflowTasks,
} from './mock-data'
import type { AgentStatus, BackendSession, BackendWorkflowEvent } from './types'

const { Paragraph, Text, Title } = Typography

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [sourceQuery, setSourceQuery] = useState('')
  const [runtimeSession, setRuntimeSession] = useState<BackendSession | null>(null)
  const [runtimeEvents, setRuntimeEvents] = useState<BackendWorkflowEvent[]>([])
  const [patientName, setPatientName] = useState('Jamie Chen')
  const [openingMessage, setOpeningMessage] = useState(
    'I have chest pain and shortness of breath.'
  )
  const [followupMessage, setFollowupMessage] = useState(
    'I am allergic to penicillin and was prescribed amoxicillin.'
  )
  const deferredQuery = useDeferredValue(sourceQuery)
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
  const runtimeSessionId = runtimeSession?.session_id

  const agentStatusQuery = useQuery({
    queryKey: ['agent-status'],
    queryFn: async () => {
      const response = await fetch(`${apiBaseUrl}/api/agents/status`)
      if (!response.ok) {
        throw new Error('Failed to fetch agent status')
      }
      const payload = await response.json()
      const items = Array.isArray(payload.agents) ? payload.agents : payload
      return items.map((item: Record<string, string>): AgentStatus => ({
        name: item.name ?? item.agent ?? 'UnknownAgent',
        state: (item.state as AgentStatus['state']) ?? 'idle',
        currentTask: item.currentTask ?? item.current_task ?? 'Waiting for workload',
        latencyMs: Number(item.latencyMs ?? item.latency_ms ?? 0),
      }))
    },
    retry: false,
  })

  const liveAgentStatuses = agentStatusQuery.data ?? agentStatuses

  const startConsultMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${apiBaseUrl}/api/consult/start`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          patient: { full_name: patientName, age: 58, allergies: ['penicillin'] },
          opening_message: openingMessage,
        }),
      })
      if (!response.ok) {
        throw new Error('Failed to start consultation')
      }
      return (await response.json()) as BackendSession
    },
    onSuccess: (session) => {
      setRuntimeSession(session)
      setRuntimeEvents([])
      setActiveTab('consultation')
      void agentStatusQuery.refetch()
      message.success('Consultation session started')
    },
    onError: () => {
      message.error('Could not start consultation session')
    },
  })

  const followupMutation = useMutation({
    mutationFn: async () => {
      if (!runtimeSession) {
        throw new Error('No active session')
      }
      const response = await fetch(
        `${apiBaseUrl}/api/consult/chat?session_id=${runtimeSession.session_id}`,
        {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ message: followupMessage }),
        }
      )
      if (!response.ok) {
        throw new Error('Failed to send follow-up')
      }
      return (await response.json()) as BackendSession
    },
    onSuccess: (session) => {
      setRuntimeSession(session)
      void agentStatusQuery.refetch()
      message.success('Follow-up message processed')
    },
    onError: () => {
      message.error('Could not send follow-up message')
    },
  })

  useEffect(() => {
    if (!runtimeSessionId) {
      return
    }

    const source = new EventSource(`${apiBaseUrl}/api/consult/${runtimeSessionId}/events`)

    const onWorkflowStep = (event: MessageEvent<string>) => {
      try {
        const parsed = JSON.parse(event.data) as BackendWorkflowEvent
        setRuntimeEvents((current) => {
          if (current.some((item) => item.event_id === parsed.event_id)) {
            return current
          }
          return [...current, parsed]
        })
      } catch {
        // Ignore malformed events in the local prototype.
      }
    }

    source.addEventListener('workflow.step', onWorkflowStep as EventListener)
    source.onerror = () => {
      source.close()
    }

    return () => {
      source.removeEventListener('workflow.step', onWorkflowStep as EventListener)
      source.close()
    }
  }, [apiBaseUrl, runtimeSessionId])

  const displayedMessages = runtimeSession
    ? runtimeSession.messages.map((messageItem) => ({
        id: messageItem.message_id,
        role: messageItem.role === 'patient' ? 'user' : 'agent',
        author:
          messageItem.role === 'patient'
            ? runtimeSession.patient.full_name || 'Patient'
            : 'MedDash Agent',
        body: messageItem.content,
        at: new Date(messageItem.created_at).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      }))
    : consultationMessages

  const displayedSources = runtimeSession
    ? runtimeSession.citations.map((item) => ({
        id: item.citation_id,
        title: item.title,
        sourceType:
          item.source_type === 'drug_label' ? 'drug-label' : item.source_type,
        excerpt: item.snippet,
      }))
    : citations

  const displayedMedicationAlerts = runtimeSession
    ? runtimeSession.medication_alerts.map((item) => ({
        id: item.alert_id,
        severity:
          item.severity === 'blocking'
            ? 'high'
            : item.severity === 'warning'
              ? 'medium'
              : 'low',
        title: `${item.medication} safety alert`,
        detail: item.message,
      }))
    : medicationAlerts

  const displayedDiagnosisCandidates = runtimeSession?.care_plan
    ? runtimeSession.care_plan.differential.map((item) => ({
        name: item.label,
        confidence: item.confidence,
        rationale: item.rationale,
      }))
    : diagnosisCandidates

  const filteredSources = useMemo(() => {
    const query = deferredQuery.trim().toLowerCase()
    if (!query) {
      return displayedSources
    }
    return displayedSources.filter((item) => {
      return (
        item.title.toLowerCase().includes(query) ||
        item.excerpt.toLowerCase().includes(query)
      )
    })
  }, [deferredQuery, displayedSources])

  const workflowColumns = [
    ['queued', 'Queued'],
    ['active', 'In Progress'],
    ['review', 'Clinician Review'],
    ['done', 'Completed'],
  ] as const

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand-lockup">
          <div className="brand-badge">
            <MedicineBoxOutlined />
          </div>
          <div className="brand-copy">
            <h1>MedDash</h1>
            <p>Clinician-assistive command center for triage, safety, and evidence-backed care plans.</p>
          </div>
        </div>

        <div className="header-metrics">
          <div className="metric-chip">
            <strong>{metrics.consultationsToday}</strong>
            <span>consultations today</span>
          </div>
          <div className="metric-chip">
            <strong>{metrics.triageAccuracy}%</strong>
            <span>triage accuracy</span>
          </div>
          <div className="metric-chip">
            <strong>{metrics.avgResponseSeconds}s</strong>
            <span>avg response latency</span>
          </div>
        </div>
      </header>

      <main className="content-wrap">
        <Card className="hero-card">
          <div className="hero-grid">
            <div className="hero-text">
              <Space wrap size={[8, 8]}>
                <Tag color="processing">Live Consult</Tag>
                <Tag color="error">Urgent escalation candidate</Tag>
                <Tag color="gold">Medication review gated</Tag>
              </Space>
              <Title level={2} style={{ color: 'white', marginTop: 16 }}>
                {runtimeSession
                  ? `${runtimeSession.patient.full_name || 'Patient'} is in a live clinician-assistive workflow.`
                  : 'Acute chest pain workflow is active with triage, evidence retrieval, and safety review in flight.'}
              </Title>
              <Paragraph>
                The current shell focuses on fast clinician visibility: what the agents are doing, why they are doing it,
                what evidence supports the recommendation, and where human takeover must happen.
              </Paragraph>

              <div className="hero-summary">
                <Card>
                  <Statistic title="Safety interventions" value={metrics.medicationInterventions} prefix={<SafetyCertificateOutlined />} />
                </Card>
                <Card>
                  <Statistic
                    title="Evidence hits"
                    value={displayedSources.length}
                    prefix={<FileSearchOutlined />}
                  />
                </Card>
              </div>
            </div>

            <div className="hero-status">
              <Title level={4} style={{ color: 'white', marginTop: 0 }}>
                Agent execution status
              </Title>
              {liveAgentStatuses.map((agent: AgentStatus) => (
                <Card
                  key={agent.name}
                  size="small"
                  style={{ marginBottom: 10, background: 'rgba(255,255,255,0.08)', borderColor: 'rgba(255,255,255,0.12)' }}
                >
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Space>
                      <Avatar icon={<RadarChartOutlined />} style={{ background: '#4f9dff' }} />
                      <Space orientation="vertical" size={0}>
                        <Text strong style={{ color: 'white' }}>
                          {agent.name}
                        </Text>
                        <Text style={{ color: 'rgba(255,255,255,0.72)' }}>{agent.currentTask}</Text>
                      </Space>
                    </Space>
                    <Tag
                      color={
                        agent.state === 'running'
                          ? 'processing'
                          : agent.state === 'blocked'
                            ? 'error'
                            : agent.state === 'waiting'
                              ? 'gold'
                              : 'default'
                      }
                    >
                      {agent.state}
                    </Tag>
                  </Space>
                </Card>
              ))}
            </div>
          </div>
        </Card>

        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            startTransition(() => setActiveTab(key))
          }}
          items={[
            {
              key: 'dashboard',
              label: (
                <span>
                  <DashboardOutlined /> Dashboard
                </span>
              ),
              children: (
                <div className="stack">
                  <Row gutter={[20, 20]}>
                    <Col xs={24} xl={8}>
                      <Card className="panel-card">
                        <Statistic title="Today consultations" value={metrics.consultationsToday} />
                        <Progress percent={78} strokeColor="#1668dc" showInfo={false} />
                      </Card>
                    </Col>
                    <Col xs={24} xl={8}>
                      <Card className="panel-card">
                        <Statistic title="Average response" value={metrics.avgResponseSeconds} suffix="sec" />
                        <Progress percent={64} status="active" showInfo={false} />
                      </Card>
                    </Col>
                    <Col xs={24} xl={8}>
                      <Card className="panel-card">
                        <Statistic title="Medication safety reminders" value={metrics.medicationInterventions} />
                        <Progress percent={88} strokeColor="#13a452" showInfo={false} />
                      </Card>
                    </Col>
                  </Row>

                  <div className="surface-grid">
                    <Card className="surface-card" title="Live care pathway">
                      <Steps
                        orientation="vertical"
                        current={2}
                        items={[
                          {
                            title: 'Structured intake complete',
                            content: 'Symptoms, history, and risk flags collected.',
                            icon: <CheckCircleOutlined />,
                          },
                          {
                            title: 'Urgency triage running',
                            content: 'Cardiopulmonary symptoms are being escalated.',
                            icon: <ClockCircleOutlined />,
                          },
                          {
                            title: 'Medication safety blocked',
                            content: 'Allergy status must be verified before suggestions are shown.',
                            icon: <AlertOutlined />,
                          },
                          {
                            title: 'Clinician handoff pending',
                            content: 'Final confirmation requires human review.',
                            icon: <ApartmentOutlined />,
                          },
                        ]}
                      />
                    </Card>

                  <Card className="surface-card" title="Triage and safety signal">
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="Department">
                        {runtimeSession?.triage.department ?? 'Emergency / Cardiology'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Priority">
                        {runtimeSession?.triage.urgency ?? 'Immediate evaluation'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Risk note">
                        {runtimeSession?.triage.rationale ??
                          'Chest tightness with dizziness and dyspnea should not be handled as routine outpatient follow-up.'}
                      </Descriptions.Item>
                    </Descriptions>
                      <Alert
                        style={{ marginTop: 16 }}
                        type="warning"
                        showIcon
                        title="Assistive-only mode"
                        description="Recommendations remain draft guidance until a clinician takes ownership or confirms disposition."
                      />
                    </Card>
                  </div>
                </div>
              ),
            },
            {
              key: 'consultation',
              label: (
                <span>
                  <RadarChartOutlined /> Patient Consultation
                </span>
              ),
              children: (
                <div className="consultation-grid">
                  <Card className="surface-card" title="Multi-agent consultation stream">
                    <Space orientation="vertical" style={{ width: '100%', marginBottom: 16 }}>
                      <Input
                        value={patientName}
                        onChange={(event) => setPatientName(event.target.value)}
                        placeholder="Patient name"
                      />
                      <Input.TextArea
                        value={openingMessage}
                        onChange={(event) => setOpeningMessage(event.target.value)}
                        rows={3}
                        placeholder="Opening clinical complaint"
                      />
                      <Space>
                        <Button
                          type="primary"
                          onClick={() => startConsultMutation.mutate()}
                          loading={startConsultMutation.isPending}
                        >
                          Start real consultation
                        </Button>
                        <Button
                          onClick={() => followupMutation.mutate()}
                          disabled={!runtimeSession}
                          loading={followupMutation.isPending}
                        >
                          Send follow-up
                        </Button>
                      </Space>
                      <Input.TextArea
                        value={followupMessage}
                        onChange={(event) => setFollowupMessage(event.target.value)}
                        rows={2}
                        placeholder="Follow-up message"
                      />
                    </Space>
                    <div className="stack">
                      {displayedMessages.map((message) => (
                        <div key={message.id} className={`chat-bubble ${message.role}`}>
                          <Space orientation="vertical" size={6}>
                            <Text strong style={{ color: message.role === 'user' ? 'white' : undefined }}>
                              {message.author}
                            </Text>
                            <Text style={{ color: message.role === 'user' ? 'white' : undefined }}>{message.body}</Text>
                            <Text type={message.role === 'user' ? undefined : 'secondary'} style={{ color: message.role === 'user' ? 'rgba(255,255,255,0.78)' : undefined }}>
                              {message.at}
                            </Text>
                          </Space>
                        </div>
                      ))}
                    </div>
                  </Card>

                  <div className="stack">
                    <Card className="surface-card" title="Intake completeness">
                      <Descriptions column={1} size="small">
                        <Descriptions.Item label="Symptoms">
                          {runtimeSession?.intake.symptoms.join(', ') ||
                            'Chest tightness, dizziness, shortness of breath'}
                        </Descriptions.Item>
                        <Descriptions.Item label="Allergies">
                          {runtimeSession?.intake.allergies.join(', ') || 'Incomplete'}
                        </Descriptions.Item>
                        <Descriptions.Item label="Red flags">
                          {runtimeSession?.intake.red_flags.join(', ') || 'None'}
                        </Descriptions.Item>
                        <Descriptions.Item label="Disposition flag">
                          {runtimeSession?.status ?? 'Escalate to clinician'}
                        </Descriptions.Item>
                      </Descriptions>
                    </Card>
                    <Card className="surface-card" title="Agent monitor">
                      <Timeline
                        items={(
                          runtimeEvents.length ? runtimeEvents : liveAgentStatuses
                        ).map((item: BackendWorkflowEvent | AgentStatus) =>
                            'event_id' in item
                              ? {
                                  color: item.state === 'completed' ? 'green' : 'blue',
                                  content: `${item.agent}: ${item.step} - ${item.detail}`,
                                }
                              : {
                                  color:
                                    item.state === 'blocked'
                                      ? 'red'
                                      : item.state === 'running'
                                        ? 'blue'
                                        : 'gray',
                                  content: `${item.name}: ${item.currentTask} (${item.latencyMs}ms)`,
                                }
                        )}
                      />
                    </Card>
                  </div>
                </div>
              ),
            },
            {
              key: 'knowledge',
              label: (
                <span>
                  <FileSearchOutlined /> Knowledge & RAG
                </span>
              ),
              children: (
                <div className="stack">
                  <Card className="surface-card" title="Evidence retrieval">
                    <Space orientation="vertical" style={{ width: '100%' }}>
                      <Input.Search
                        allowClear
                        placeholder="Filter by guideline, label, or case note"
                        onChange={(event) => setSourceQuery(event.target.value)}
                      />
                      <div className="stack">
                        {filteredSources.map((item) => (
                          <div key={item.id} className="source-item">
                            <Space>
                              <Tag
                                color={
                                  item.sourceType === 'guideline'
                                    ? 'processing'
                                    : item.sourceType === 'drug-label'
                                      ? 'orange'
                                      : 'purple'
                                }
                              >
                                {item.sourceType}
                              </Tag>
                              <Text strong>{item.title}</Text>
                            </Space>
                            <Text>{item.excerpt}</Text>
                          </div>
                        ))}
                      </div>
                    </Space>
                  </Card>
                </div>
              ),
            },
            {
              key: 'diagnosis',
              label: (
                <span>
                  <ExperimentOutlined /> Diagnosis & Treatment
                </span>
              ),
              children: (
                <div className="surface-grid">
                  <Card className="surface-card" title="Differential candidates">
                    <div className="stack">
                      {displayedDiagnosisCandidates.map((item) => (
                        <Card key={item.name} size="small">
                          <Space orientation="vertical" style={{ width: '100%' }}>
                            <Space>
                              <Text strong>{item.name}</Text>
                              <Badge color="#1668dc" text={`${Math.round(item.confidence * 100)}% confidence`} />
                            </Space>
                            <Text type="secondary">{item.rationale}</Text>
                          </Space>
                        </Card>
                      ))}
                    </div>
                  </Card>

                  <Card className="surface-card" title="Medication safety alerts">
                    <div className="stack">
                      {displayedMedicationAlerts.map((alert) => (
                        <Alert
                          key={alert.id}
                          style={{ width: '100%' }}
                          type={
                            alert.severity === 'high'
                              ? 'error'
                              : alert.severity === 'medium'
                                ? 'warning'
                                : 'info'
                          }
                          showIcon
                          title={alert.title}
                          description={alert.detail}
                        />
                      ))}
                    </div>
                  </Card>
                </div>
              ),
            },
            {
              key: 'workflow',
              label: (
                <span>
                  <ApartmentOutlined /> Workflow & Task Center
                </span>
              ),
              children: (
                <div className="workflow-board">
                  {workflowColumns.map(([stage, label]) => (
                    <div key={stage} className="workflow-column">
                      <Space orientation="vertical" style={{ width: '100%' }}>
                        <Text strong>{label}</Text>
                        {workflowTasks
                          .filter((task) => task.stage === stage)
                          .map((task) => (
                            <Card key={task.id} size="small">
                            <Space orientation="vertical" size={2}>
                                <Text strong>{task.title}</Text>
                                <Text type="secondary">{task.owner}</Text>
                              </Space>
                            </Card>
                          ))}
                      </Space>
                    </div>
                  ))}
                </div>
              ),
            },
            {
              key: 'settings',
              label: (
                <span>
                  <SettingOutlined /> Settings & Prompt Ops
                </span>
              ),
              children: (
                <div className="settings-grid">
                  <Card className="surface-card" title="Provider and prompt routing">
                    <Form layout="vertical" initialValues={{ provider: 'openai', agentaEnabled: 'false' }}>
                      <Form.Item label="Primary provider" name="provider">
                        <Select
                          options={[
                            { value: 'openai', label: 'OpenAI' },
                            { value: 'deepseek', label: 'DeepSeek' },
                            { value: 'kimi', label: 'Kimi' },
                          ]}
                        />
                      </Form.Item>
                      <Form.Item label="Agenta adapter" name="agentaEnabled">
                        <Select
                          options={[
                            { value: 'false', label: 'Disabled by default' },
                            { value: 'true', label: 'Enabled when credentials are added' },
                          ]}
                        />
                      </Form.Item>
                      <Form.Item label="Prompt release train">
                        <Select
                          options={[
                            { value: 'stable', label: 'Stable' },
                            { value: 'canary', label: 'Canary' },
                            { value: 'ab', label: 'A/B experiment' },
                          ]}
                        />
                      </Form.Item>
                      <Button type="primary">Save local settings</Button>
                    </Form>
                  </Card>

                  <Card className="surface-card" title="Operational controls">
                    <Space orientation="vertical" size="middle" style={{ width: '100%' }}>
                      <Alert
                        type="info"
                        showIcon
                        title="Prompt operations remain local-first"
                        description="The app is prepared for Agenta sync, but no credentials are stored in source control."
                      />
                      <Alert
                        type="warning"
                        showIcon
                        title="Human review remains mandatory"
                        description="Unsafe triage, medication conflicts, and disposition overrides require clinician acknowledgement."
                      />
                    </Space>
                  </Card>
                </div>
              ),
            },
          ]}
        />
      </main>
    </div>
  )
}

export default App
