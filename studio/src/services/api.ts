import axios from 'axios';
import type { 
  SimulationRequest, 
  SimulationResult, 
  HealthCheck,
  Procedure,
  Automation,
  IntakeConfig,
  LeadsListResponse,
  LeadDetail,
  LeadsFilters,
  RAGKnowledgeBase,
  RAGPrompt,
  RAGModel,
  RAGParameters,
  RAGSimulationRequest,
  RAGSimulationResult,
  RAGPreset,
  RAGLogEvent,
  RAGLead,
  RAGLeadMessage,
  CreateRAGLeadRequest
} from '../types';

// Base URL do backend - usar caminhos relativos via proxy
const API_BASE_URL = '';

// Configurar axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para logs em modo dev
api.interceptors.request.use(request => {
  if (import.meta.env.DEV) {
    console.log('[API Request]', request.method?.toUpperCase(), request.url);
  }
  return request;
});

api.interceptors.response.use(
  response => {
    if (import.meta.env.DEV) {
      console.log('[API Response]', response.status, response.config.url);
    }
    return response;
  },
  error => {
    console.error('[API Error]', error.response?.status, error.config?.url, error.message);
    return Promise.reject(error);
  }
);

// Serviços da API
export const apiService = {
  // Health check
  async healthCheck(): Promise<HealthCheck> {
    const response = await api.get('/health');
    return response.data;
  },

  // Simulação (endpoint principal)
  async simulate(request: SimulationRequest): Promise<SimulationResult> {
    const response = await api.post('/engine/decide', request);
    return response.data;
  },

  // Aplicar plano (se necessário para testes reais)
  async applyPlan(plan: any, idempotencyKey?: string) {
    const headers = idempotencyKey ? { 'X-Idempotency-Key': idempotencyKey } : {};
    const response = await api.post('/api/tools/apply_plan', plan, { headers });
    return response.data;
  },

  // Info dos canais
  async getTelegramInfo() {
    const response = await api.get('/channels/telegram/info');
    return response.data;
  },

  async getWhatsappInfo() {
    const response = await api.get('/channels/whatsapp/info');
    return response.data;
  },

  // Endpoints futuros para CRUD (quando implementados no backend)
  async getProcedures(): Promise<Procedure[]> {
    // Por enquanto, retorna dados mock
    return mockProcedures;
  },

  async saveProcedure(procedure: Procedure): Promise<Procedure> {
    // TODO: Implementar quando backend tiver endpoint
    console.log('Salvando procedimento:', procedure);
    return procedure;
  },

  async getAutomations(): Promise<Automation[]> {
    // Por enquanto, retorna dados mock
    return mockAutomations;
  },

  async saveAutomation(automation: Automation): Promise<Automation> {
    // TODO: Implementar quando backend tiver endpoint
    console.log('Salvando automação:', automation);
    return automation;
  },

  async getIntakeConfig(): Promise<IntakeConfig> {
    // Por enquanto, retorna config mock
    return mockIntakeConfig;
  },

  async saveIntakeConfig(config: IntakeConfig): Promise<IntakeConfig> {
    // TODO: Implementar quando backend tiver endpoint
    console.log('Salvando config intake:', config);
    return config;
  },

  // Endpoints para Leads
  async getLeads(filters: LeadsFilters = {}): Promise<LeadsListResponse> {
    const params = new URLSearchParams();
    
    // Adicionar parâmetros de filtro
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(`${key}[]`, v.toString()));
        } else {
          params.append(key, value.toString());
        }
      }
    });

    const response = await api.get(`/api/leads?${params.toString()}`);
    return response.data;
  },

  async getLeadDetail(leadId: number): Promise<LeadDetail> {
    const response = await api.get(`/api/leads/${leadId}`);
    return response.data;
  },

  // Limpar sessão de um lead
  async clearLeadSession(leadId: number): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/api/leads/${leadId}/session`);
    return response.data;
  },

  // Deletar lead
  async deleteLead(leadId: number): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/api/leads/${leadId}`);
    return response.data;
  },

  // === RAG ENDPOINTS ===

  // Base de conhecimento
  async getRAGKnowledgeBase(): Promise<RAGKnowledgeBase> {
    const response = await api.get('/api/rag/knowledge-base');
    return response.data;
  },

  async updateRAGKnowledgeBase(kb: RAGKnowledgeBase): Promise<{ success: boolean; message: string }> {
    const response = await api.put('/api/rag/knowledge-base', kb);
    return response.data;
  },

  // Prompt RAG
  async getRAGPrompt(): Promise<RAGPrompt> {
    const response = await api.get('/api/rag/prompt');
    return response.data;
  },

  async updateRAGPrompt(prompt: RAGPrompt): Promise<{ success: boolean; message: string; warnings?: string }> {
    const response = await api.put('/api/rag/prompt', prompt);
    return response.data;
  },

  // Modelos disponíveis
  async getRAGModels(): Promise<RAGModel[]> {
    const response = await api.get('/api/rag/models');
    return response.data;
  },

  // Presets de configuração
  async getRAGPresets(): Promise<Record<RAGPreset, RAGParameters>> {
    const response = await api.get('/api/rag/presets');
    return response.data;
  },

  // Simulação RAG
  async simulateRAG(request: RAGSimulationRequest): Promise<RAGSimulationResult> {
    const response = await api.post('/api/rag/simulate', request);
    return response.data;
  },

  // Stream de simulação (para logs em tempo real)
  createRAGStreamConnection(message: string, safeMode: boolean = true, leadId?: number): EventSource {
    const params = new URLSearchParams({
      message,
      safe_mode: safeMode.toString()
    });
    
    if (leadId) {
      params.append('lead_id', leadId.toString());
    }
    
    return new EventSource(`/api/rag/simulate/stream?${params.toString()}`);
  },

  // === RAG LEADS ENDPOINTS ===

  // Gerenciar Leads RAG
  async getRAGLeads(): Promise<RAGLead[]> {
    const response = await api.get('/api/rag/leads');
    return response.data;
  },

  async createRAGLead(request: CreateRAGLeadRequest): Promise<RAGLead> {
    const response = await api.post('/api/rag/leads', request);
    return response.data;
  },

  async deleteRAGLead(leadId: number): Promise<{ message: string }> {
    const response = await api.delete(`/api/rag/leads/${leadId}`);
    return response.data;
  },

  async getRAGLead(leadId: number): Promise<RAGLead> {
    const response = await api.get(`/api/rag/leads/${leadId}`);
    return response.data;
  },

  async addMessageToRAGLead(leadId: number, message: RAGLeadMessage): Promise<{ message: string; total_messages: number }> {
    const response = await api.post(`/api/rag/leads/${leadId}/messages`, message);
    return response.data;
  },
};

// Dados mock para desenvolvimento
const mockProcedures: Procedure[] = [
  {
    id: 'liberar_teste',
    title: 'Liberar acesso ao teste',
    description: 'Procedimento para liberar acesso de teste do robô',
    steps: [
      {
        name: 'Concorda em depositar',
        condition: 'o lead concordou em depositar ou já depositou',
        if_missing: { automation: 'ask_deposit_for_test' }
      },
      {
        name: 'Criou conta',
        condition: 'tem conta em alguma corretora suportada',
        if_missing: { automation: 'signup_link' }
      },
      {
        name: 'Depósito confirmado',
        condition: 'depósito confirmado',
        if_missing: { automation: 'prompt_deposit' }
      },
      {
        name: 'Liberar',
        condition: 'todas as etapas anteriores cumpridas',
        do: { automation: 'trial_unlock' }
      }
    ]
  }
];

const mockAutomations: Automation[] = [
  {
    id: 'ask_deposit_for_test',
    topic: 'teste',
    eligibility: 'não concordou em depositar e não depositou',
    priority: 0.85,
    cooldown: '24h',
    output: {
      type: 'message',
      text: 'Para liberar o teste, você consegue fazer um pequeno depósito? 💰',
      buttons: [
        {
          id: 'btn_yes_deposit',
          label: 'Sim, consigo',
          kind: 'callback',
          set_facts: { 'agreements.can_deposit': true },
          track: { event: 'click_yes_deposit', utm_passthrough: true }
        },
        {
          id: 'btn_help_deposit',
          label: 'Como deposito?',
          kind: 'url',
          url: '${deposit_help_link}',
          track: { event: 'open_deposit_help' }
        }
      ]
    }
  },
  {
    id: 'signup_link',
    topic: 'conta',
    eligibility: 'não tem conta em alguma corretora suportada',
    priority: 0.90,
    cooldown: '12h',
    output: {
      type: 'message',
      text: 'Primeiro você precisa criar uma conta na corretora! 📊\n\nRecomendo a Quotex - é mais fácil para iniciantes:',
      buttons: [
        {
          id: 'btn_quotex_signup',
          label: 'Criar conta Quotex',
          kind: 'url',
          url: 'https://quotex.io/pt/?lid=123456',
          track: { event: 'signup_quotex_click' }
        }
      ]
    }
  }
];

const mockIntakeConfig: IntakeConfig = {
  llm_budget: 1,
  tool_budget: 2,
  max_latency_ms: 3000,
  thresholds: {
    direct: 0.80,
    parallel: 0.60
  },
  anchors: {
    teste: ['quero testar', 'teste grátis', 'liberar teste', 'começar agora'],
    ajuda: ['não consigo', 'como faço', 'preciso de ajuda', 'dúvida'],
    conta: ['criar conta', 'cadastro', 'abrir conta']
  },
  id_patterns: {
    quotex: ['\\b[a-zA-Z0-9]{6,16}\\b'],
    nyrion: ['\\b[0-9]{6,12}\\b']
  }
};

export default apiService;
