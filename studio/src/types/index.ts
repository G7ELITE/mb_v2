// Tipos para o ManyBlack Studio

export interface Lead {
  id?: number;
  nome?: string;
  lang: string;
}

export interface Snapshot {
  accounts: Record<string, string>;
  deposit: Record<string, any>;
  agreements: Record<string, any>;
  flags: Record<string, any>;
  history_summary?: string;
}

export interface Message {
  id: string;
  text: string;
}

export interface Env {
  lead: Lead;
  snapshot: Snapshot;
  candidates?: Record<string, any>;
  messages_window: Message[];
  apply: boolean;
}

export interface Action {
  type: string;
  text?: string;
  buttons?: Button[];
  url?: string;
  media?: Record<string, any>;
  track?: Record<string, any>;
  set_facts?: Record<string, any>;
}

export interface Button {
  id: string;
  label: string;
  kind: 'callback' | 'url' | 'quick_reply';
  set_facts?: Record<string, any>;
  url?: string;
  track?: Record<string, any>;
}

export interface Plan {
  decision_id: string;
  actions: Action[];
  metadata?: Record<string, any>;
}

export interface Procedure {
  id: string;
  title: string;
  description?: string;
  steps: ProcedureStep[];
  settings?: {
    max_procedure_time?: string;
    procedure_cooldown?: string;
    allow_nested_procedures?: boolean;
  };
}

export interface ProcedureStep {
  name: string;
  condition: string;
  if_missing?: {
    automation?: string;
    procedure?: string;
  };
  do?: {
    automation?: string;
    procedure?: string;
  };
}

export interface Automation {
  id: string;
  topic: string;
  use_when?: string;
  eligibility: string;
  priority: number;
  cooldown: string;
  expects_reply?: {
    target: string;
  };
  output: {
    type: string;
    text: string;
    buttons?: Button[];
    track?: Record<string, any>;
  };
}

export interface IntakeConfig {
  llm_budget: number;
  tool_budget: number;
  max_latency_ms: number;
  thresholds: {
    direct: number;
    parallel: number;
  };
  anchors: Record<string, string[]>;
  id_patterns?: Record<string, string[]>;
}

export interface SimulationRequest {
  lead: Lead;
  snapshot: Snapshot;
  messages_window: Message[];
  apply: boolean;
}

export interface SimulationResult {
  decision_id: string;
  actions: Action[];
  metadata: {
    interaction_type: string;
    snapshot_summary: Record<string, any>;
  };
}

export interface HealthCheck {
  status: string;
  env: string;
}

// Tipos para a página de Leads
export interface LeadListItem {
  id: number;
  name?: string;
  channel: string;
  platform_user_id: string;
  lang: string;
  created_at?: string;
  last_activity_at?: string;
  events_24h: number;
  accounts: Record<string, string>;
  deposit: Record<string, any>;
  agreements: Record<string, any>;
  flags: Record<string, any>;
  tags: string[];
  procedure: {
    active?: string;
    step?: string;
  };
}

export interface LeadDetail extends LeadListItem {
  snapshot: {
    accounts: Record<string, string>;
    deposit: Record<string, any>;
    agreements: Record<string, any>;
    flags: Record<string, any>;
    tags: string[];
  };
  procedure: {
    active?: string;
    step?: string;
    waiting?: any;
  };
  events_recent: Array<{
    id: number;
    event_type: string;
    payload: any;
    created_at: string;
  }>;
}

export interface LeadsListResponse {
  items: LeadListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface LeadsFilters {
  q?: string;
  created_from?: string;
  created_to?: string;
  last_active_from?: string;
  last_active_to?: string;
  channel?: string;
  lang?: string;
  deposit_status?: string;
  accounts_quotex?: string;
  accounts_nyrion?: string;
  agreements_can_deposit?: boolean;
  agreements_wants_test?: boolean;
  tags?: string[];
  not_tags?: string[];
  procedure_active?: string;
  procedure_step?: string;
  inactive_gt_hours?: number;
  pending_ops?: boolean;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  mock?: boolean;
  min_events_24h?: number;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
}

// Tipos para autocomplete
export interface AutocompleteOption {
  value: string;
  label: string;
  description?: string;
}

export interface ValidationError {
  field: string;
  message: string;
}

// Constantes para autocomplete
export const FACT_KEYS = [
  'agreements.can_deposit',
  'agreements.wants_test',
  'deposit.status',
  'accounts.quotex',
  'accounts.nyrion',
  'lead_inativo',
  'viu_video_robo'
] as const;

export const FACT_VALUES: Record<string, (string | boolean)[]> = {
  'agreements.can_deposit': [true, false],
  'agreements.wants_test': [true, false],
  'deposit.status': ['nenhum', 'pending', 'confirmado'],
  'accounts.quotex': ['nenhum', 'reported', 'com_conta'],
  'accounts.nyrion': ['nenhum', 'reported', 'com_conta'],
  'lead_inativo': [true, false],
  'viu_video_robo': [true, false]
};

export const COMMON_CONDITIONS = [
  'o lead concordou em depositar',
  'o lead concordou em depositar ou já depositou',
  'tem conta em alguma corretora suportada',
  'depósito confirmado',
  'todas as etapas anteriores cumpridas',
  'lead tem corretora definida',
  'robô foi explicado para o lead',
  'manifestou interesse em testar'
] as const;

export const AUTOMATION_IDS = [
  'ask_deposit_for_test',
  'signup_link',
  'prompt_deposit',
  'trial_unlock',
  'explain_robot',
  'ask_broker_preference',
  'deposit_help_detailed'
] as const;

export const TOPICS = [
  'teste',
  'conta',
  'deposito',
  'liberacao',
  'como funciona',
  'ajuda deposito',
  'reativacao'
] as const;

export const COOLDOWN_OPTIONS = [
  '0h',
  '1h',
  '6h',
  '12h',
  '24h',
  '48h'
] as const;
