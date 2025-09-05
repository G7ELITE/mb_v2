/**
 * Sistema de configuração global compartilhada entre telas RAG e Equipe
 */

export interface RAGGlobalConfig {
  model_id: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  top_k: number;
  threshold: number;
  re_rank: boolean;
  enable_semantic_comparison: boolean;
}

// Configurações padrão (GPT-4o como default)
export const DEFAULT_RAG_CONFIG: RAGGlobalConfig = {
  model_id: 'gpt-4o',  // Alterado para GPT-4o como padrão
  temperature: 0.3,
  max_tokens: 800,
  top_p: 0.9,
  top_k: 5,
  threshold: 0.65,
  re_rank: true,
  enable_semantic_comparison: false
};

// Modelos disponíveis
export const AVAILABLE_MODELS = [
  { id: 'gpt-4o', name: 'GPT-4o', description: 'Modelo padrão otimizado' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', description: 'Versão compacta e rápida' },
  { id: 'gpt-5', name: 'GPT-5', description: 'Modelo mais avançado (quando disponível)' }
];

const CONFIG_KEY = 'mb_rag_global_config';

/**
 * Salva configurações globais no localStorage
 */
export const saveRAGConfig = (config: RAGGlobalConfig): void => {
  try {
    localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
    console.log('🎯 Configurações RAG salvas globalmente:', config);
  } catch (error) {
    console.error('Erro ao salvar configurações RAG:', error);
  }
};

/**
 * Carrega configurações globais do localStorage
 */
export const loadRAGConfig = (): RAGGlobalConfig => {
  try {
    const saved = localStorage.getItem(CONFIG_KEY);
    if (saved) {
      const config = JSON.parse(saved);
      console.log('🎯 Configurações RAG carregadas:', config);
      // Garantir que todas as propriedades existem
      return { ...DEFAULT_RAG_CONFIG, ...config };
    }
  } catch (error) {
    console.error('Erro ao carregar configurações RAG:', error);
  }
  
  console.log('🎯 Usando configurações RAG padrão');
  return DEFAULT_RAG_CONFIG;
};

/**
 * Reseta configurações para o padrão
 */
export const resetRAGConfig = (): RAGGlobalConfig => {
  localStorage.removeItem(CONFIG_KEY);
  console.log('🎯 Configurações RAG resetadas para o padrão');
  return DEFAULT_RAG_CONFIG;
};

/**
 * Hook para sincronizar configurações entre componentes
 */
export const useRAGConfigSync = () => {
  const handleConfigChange = (callback: (config: RAGGlobalConfig) => void) => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === CONFIG_KEY && e.newValue) {
        try {
          const newConfig = JSON.parse(e.newValue);
          callback({ ...DEFAULT_RAG_CONFIG, ...newConfig });
        } catch (error) {
          console.error('Erro ao sincronizar configurações:', error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  };

  return { handleConfigChange };
};

/**
 * Converte configuração global para formato da API RAG
 */
export const configToRAGParameters = (config: RAGGlobalConfig) => {
  return {
    model_id: config.model_id,
    temperature: config.temperature,
    max_tokens: config.max_tokens,
    top_p: config.top_p,
    top_k: config.top_k,
    threshold: config.threshold,
    re_rank: config.re_rank,
    enable_semantic_comparison: config.enable_semantic_comparison
  };
};

/**
 * Validação de configuração
 */
export const validateRAGConfig = (config: Partial<RAGGlobalConfig>): string[] => {
  const errors: string[] = [];
  
  if (config.temperature !== undefined && (config.temperature < 0 || config.temperature > 1)) {
    errors.push('Temperature deve estar entre 0 e 1');
  }
  
  if (config.max_tokens !== undefined && (config.max_tokens < 50 || config.max_tokens > 4000)) {
    errors.push('Max tokens deve estar entre 50 e 4000');
  }
  
  if (config.top_p !== undefined && (config.top_p < 0 || config.top_p > 1)) {
    errors.push('Top P deve estar entre 0 e 1');
  }
  
  if (config.threshold !== undefined && (config.threshold < 0 || config.threshold > 1)) {
    errors.push('Threshold deve estar entre 0 e 1');
  }
  
  if (config.top_k !== undefined && (config.top_k < 1 || config.top_k > 20)) {
    errors.push('Top K deve estar entre 1 e 20');
  }
  
  if (config.model_id && !AVAILABLE_MODELS.some(m => m.id === config.model_id)) {
    errors.push('Modelo selecionado não está disponível');
  }
  
  return errors;
};
