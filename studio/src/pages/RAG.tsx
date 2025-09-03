import { useState, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import {
  PlayIcon,
  DocumentTextIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  ArrowDownTrayIcon,
  PauseIcon,
  EyeIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  InformationCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/Toast';
import { InfoTooltip } from '../components/Tooltip';
import type { 
  RAGKnowledgeBase, 
  RAGPrompt, 
  RAGModel, 
  RAGParameters, 
  RAGSimulationRequest, 
  RAGSimulationResult,
  RAGLogEvent,
  RAGTopNResult,
  RAGPreset
} from '../types';

interface RAGForm {
  message: string;
  leadProfile: {
    hasAccount: boolean;
    hasDeposit: boolean;
    wantsTest: boolean;
  };
  selectedPreset: RAGPreset;
  useCustomParameters: boolean;
  customParameters: {
    model_id: string;
    creativity: number; // temperature
    response_length: number; // max_tokens
    focus: number; // top_p
    search_depth: number; // top_k
    relevance_filter: number; // threshold
    enable_rerank: boolean; // re_rank
  };
  safeMode: boolean;
}

export default function RAG() {
  // Hook de toast para feedbacks
  const toast = useToast();

  // Estados principais
  const [knowledgeBase, setKnowledgeBase] = useState<RAGKnowledgeBase | null>(null);
  const [prompt, setPrompt] = useState<RAGPrompt | null>(null);
  const [models, setModels] = useState<RAGModel[]>([]);
  const [presets, setPresets] = useState<Record<RAGPreset, RAGParameters> | null>(null);
  const [simulationResult, setSimulationResult] = useState<RAGSimulationResult | null>(null);

  // Estados de UI
  const [loading, setLoading] = useState(false);
  const [kbLoading, setKbLoading] = useState(false);
  const [promptLoading, setPromptLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [kbExpanded, setKbExpanded] = useState(false);
  const [promptExpanded, setPromptExpanded] = useState(false);
  const [parametersExpanded, setParametersExpanded] = useState(false);
  const [logsExpanded, setLogsExpanded] = useState(true);

  // Estados de logs em tempo real
  const [logs, setLogs] = useState<RAGLogEvent[]>([]);
  const [streamActive, setStreamActive] = useState(false);
  const [streamPaused, setStreamPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [logFilter, setLogFilter] = useState<string>('');

  // Referências
  const eventSourceRef = useRef<EventSource | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Form
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<RAGForm>({
    defaultValues: {
      message: '',
      leadProfile: {
        hasAccount: false,
        hasDeposit: false,
        wantsTest: false
      },
      selectedPreset: 'balanced',
      useCustomParameters: false,
      customParameters: {
        model_id: 'gpt-4o',
        creativity: 0.3,
        response_length: 400,
        focus: 1.0,
        search_depth: 3,
        relevance_filter: 0.05,
        enable_rerank: false
      },
      safeMode: true
    }
  });

  const selectedPreset = watch('selectedPreset');
  const useCustomParameters = watch('useCustomParameters');

  // Carregar dados iniciais
  useEffect(() => {
    loadInitialData();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // Auto scroll nos logs
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const loadInitialData = async (showSuccessToast = false) => {
    try {
      setLoading(true);
      const [kbData, promptData, modelsData, presetsData] = await Promise.all([
        apiService.getRAGKnowledgeBase(),
        apiService.getRAGPrompt(),
        apiService.getRAGModels(),
        apiService.getRAGPresets()
      ]);

      setKnowledgeBase(kbData);
      setPrompt(promptData);
      setModels(modelsData);
      setPresets(presetsData);
      
      if (showSuccessToast) {
        toast.success('Dados recarregados com sucesso!', `KB: ${kbData.sections_count} seções, ${modelsData.length} modelos disponíveis`);
      }
    } catch (err: any) {
      toast.error('Erro ao carregar configuração RAG', err.message);
      setError(`Erro ao carregar dados iniciais: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKBSave = async () => {
    if (!knowledgeBase) return;
    
    try {
      setKbLoading(true);
      await apiService.updateRAGKnowledgeBase(knowledgeBase);
      toast.success('Base de Conhecimento salva com sucesso!', 'Todas as alterações foram aplicadas.');
    } catch (err: any) {
      toast.error('Erro ao salvar Base de Conhecimento', err.message);
      setError(`Erro ao salvar KB: ${err.message}`);
    } finally {
      setKbLoading(false);
    }
  };

  const handlePromptSave = async () => {
    if (!prompt) return;
    
    try {
      setPromptLoading(true);
      const result = await apiService.updateRAGPrompt(prompt);
      
      if (result.warnings) {
        toast.warning('Prompt salvo com avisos', result.warnings);
      } else {
        toast.success('Prompt RAG salvo com sucesso!', 'Template do prompt foi atualizado.');
      }
    } catch (err: any) {
      toast.error('Erro ao salvar Prompt RAG', err.message);
      setError(`Erro ao salvar prompt: ${err.message}`);
    } finally {
      setPromptLoading(false);
    }
  };

  const handleSimulation = async (data: RAGForm) => {
    if (!presets) return;

    try {
      setLoading(true);
      setError('');
      setLogs([]);

      // Construir perfil do lead
      const leadProfile = {
        accounts: { 
          quotex: data.leadProfile.hasAccount ? 'com_conta' : 'nenhum',
          nyrion: 'desconhecido' 
        },
        deposit: { 
          status: data.leadProfile.hasDeposit ? 'confirmado' : 'nenhum',
          amount: data.leadProfile.hasDeposit ? 100 : null 
        },
        agreements: { 
          wants_test: data.leadProfile.wantsTest 
        },
        flags: { 
          explained: false 
        }
      };

      // Usar preset ou parâmetros customizados
      let parameters: RAGParameters;
      
      if (data.useCustomParameters) {
        parameters = {
          model_id: data.customParameters.model_id,
          temperature: data.customParameters.creativity,
          max_tokens: data.customParameters.response_length,
          top_p: data.customParameters.focus,
          top_k: data.customParameters.search_depth,
          threshold: data.customParameters.relevance_filter,
          re_rank: data.customParameters.enable_rerank
        };
      } else {
        parameters = presets[data.selectedPreset];
      }

      const request: RAGSimulationRequest = {
        message: data.message,
        lead_profile: leadProfile,
        parameters,
        safe_mode: data.safeMode
      };

      // Iniciar stream de logs se disponível
      if (data.safeMode) {
        startLogStream(data.message, data.safeMode);
      }

      const result = await apiService.simulateRAG(request);
      setSimulationResult(result);
      
      toast.success(
        'Simulação concluída com sucesso!', 
        `Processada em ${result.processing_time_ms}ms - Classificação: ${result.classification}`
      );

    } catch (err: any) {
      toast.error('Erro na simulação RAG', err.message);
      setError(`Erro na simulação: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const startLogStream = (message: string, safeMode: boolean) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const eventSource = apiService.createRAGStreamConnection(message, safeMode);
      eventSourceRef.current = eventSource;
      setStreamActive(true);

      eventSource.onmessage = (event) => {
        if (!streamPaused) {
          const logEvent: RAGLogEvent = JSON.parse(event.data);
          setLogs(prev => [...prev, logEvent]);
        }
      };

      eventSource.onerror = () => {
        setStreamActive(false);
        eventSource.close();
      };

      // Auto-close after 30s
      setTimeout(() => {
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          setStreamActive(false);
        }
      }, 30000);

    } catch (err) {
      console.error('Erro ao iniciar stream:', err);
    }
  };

  const exportLogs = () => {
    try {
      const logsJson = logs.map(log => JSON.stringify(log)).join('\n');
      const blob = new Blob([logsJson], { type: 'application/jsonl' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rag-logs-${Date.now()}.jsonl`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast.success('Logs exportados!', `${logs.length} eventos exportados em formato JSONL`);
    } catch (err: any) {
      toast.error('Erro ao exportar logs', err.message);
    }
  };

  const filteredLogs = logs.filter(log => 
    !logFilter || 
    log.stage.toLowerCase().includes(logFilter.toLowerCase()) ||
    log.event.toLowerCase().includes(logFilter.toLowerCase())
  );

  if (loading && !knowledgeBase) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Carregando configuração RAG...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">RAG - Retrieval Augmented Generation</h1>
          <p className="text-gray-600 dark:text-gray-400">Configure, simule e monitore o sistema RAG</p>
        </div>
        
        {/* Status do backend */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Backend conectado</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex">
            <ExclamationCircleIcon className="h-5 w-5 text-red-400 mr-2" />
            <div className="text-sm text-red-700 dark:text-red-400">{error}</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Coluna esquerda - Configurações */}
        <div className="xl:col-span-2 space-y-6">
          
          {/* Bloco: Base de Conhecimento */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div 
              className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between cursor-pointer"
              onClick={() => setKbExpanded(!kbExpanded)}
            >
              <div className="flex items-center">
                <DocumentTextIcon className="h-5 w-5 text-gray-400 mr-2" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Base de Conhecimento</h3>
                {knowledgeBase && (
                  <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                    ({knowledgeBase.sections_count || 0} seções)
                  </span>
                )}
              </div>
              {kbExpanded ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
            </div>
            
            {kbExpanded && knowledgeBase && (
              <div className="p-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Conteúdo (Markdown)
                  </label>
                  <textarea
                    value={knowledgeBase.content}
                    onChange={(e) => setKnowledgeBase({ ...knowledgeBase, content: e.target.value })}
                    className="w-full h-64 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white font-mono text-sm"
                    placeholder="# Título da seção

Conteúdo da base de conhecimento em Markdown..."
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    {knowledgeBase.content.length} caracteres
                  </p>
                </div>
                
                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={handleKBSave}
                    disabled={kbLoading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 flex items-center"
                  >
                    {kbLoading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    ) : (
                      <CheckCircleIcon className="h-4 w-4 mr-2" />
                    )}
                    Salvar KB
                  </button>
                  
                  <button
                    type="button"
                    onClick={() => loadInitialData(true)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    Recarregar
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Bloco: Prompt RAG */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div 
              className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between cursor-pointer"
              onClick={() => setPromptExpanded(!promptExpanded)}
            >
              <div className="flex items-center">
                <CpuChipIcon className="h-5 w-5 text-gray-400 mr-2" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Prompt RAG</h3>
                {prompt && !prompt.is_valid && (
                  <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500 ml-2" />
                )}
              </div>
              {promptExpanded ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
            </div>
            
            {promptExpanded && prompt && (
              <div className="p-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Template do Prompt
                  </label>
                  <textarea
                    value={prompt.template}
                    onChange={(e) => setPrompt({ ...prompt, template: e.target.value })}
                    className="w-full h-48 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white font-mono text-sm"
                    placeholder="Você é um assistente do ManyBlack...

Contexto: {kb_context}
Pergunta: {pergunta}

Resposta:"
                  />
                </div>

                {prompt.placeholders.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Placeholders disponíveis
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {prompt.placeholders.map((placeholder) => (
                        <span key={placeholder} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded">
                          {'{' + placeholder + '}'}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={handlePromptSave}
                    disabled={promptLoading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 flex items-center"
                  >
                    {promptLoading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    ) : (
                      <CheckCircleIcon className="h-4 w-4 mr-2" />
                    )}
                    Salvar Prompt
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Bloco: Modelos e Parâmetros */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div 
              className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between cursor-pointer"
              onClick={() => setParametersExpanded(!parametersExpanded)}
            >
              <div className="flex items-center">
                <CpuChipIcon className="h-5 w-5 text-gray-400 mr-2" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Modelos & Parâmetros</h3>
              </div>
              {parametersExpanded ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
            </div>
            
            {parametersExpanded && (
              <div className="p-4 space-y-4">
                {/* Toggle entre Preset e Custom */}
                <div className="flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      {...register('useCustomParameters')}
                      value="false"
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Usar Preset</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      {...register('useCustomParameters')}
                      value="true"
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Configuração Avançada</span>
                  </label>
                </div>

                {!useCustomParameters ? (
                  /* Presets */
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Preset de Configuração
                      </label>
                      <InfoTooltip content="Configurações pré-definidas para diferentes necessidades: rápido (velocidade), equilibrado (balanceado) ou preciso (máxima qualidade)" />
                    </div>
                    <select
                      {...register('selectedPreset')}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="fast">🚀 Rápido - Respostas ágeis com GPT-4o Mini</option>
                      <option value="balanced">⚖️ Equilibrado - Balanceado com GPT-4o</option>
                      <option value="precise">🎯 Preciso - Máxima qualidade com o1-preview</option>
                    </select>
                  </div>
                ) : (
                  /* Configurações Avançadas */
                  <div className="space-y-4 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 dark:text-white">Configuração Avançada</h4>
                    
                    {/* Modelo */}
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Modelo de IA
                        </label>
                        <InfoTooltip content="Escolha o modelo que processará as consultas. Modelos mais avançados são mais precisos mas podem ser mais lentos" />
                      </div>
                      <select
                        {...register('customParameters.model_id')}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      >
                        {models.map((model) => (
                          <option key={model.id} value={model.id}>
                            {model.name} {!model.available && '(indisponível)'}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Criatividade */}
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Criatividade: {watch('customParameters.creativity')}
                        </label>
                        <InfoTooltip content="Controla quão criativo o modelo será. Valores baixos (0.1) são mais objetivos, valores altos (0.8) são mais criativos" />
                      </div>
                      <input
                        type="range"
                        min="0.1"
                        max="1.0"
                        step="0.1"
                        {...register('customParameters.creativity')}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>Objetivo</span>
                        <span>Criativo</span>
                      </div>
                    </div>

                    {/* Tamanho da resposta */}
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Tamanho da Resposta: {watch('customParameters.response_length')} tokens
                        </label>
                        <InfoTooltip content="Máximo de palavras na resposta. Valores maiores permitem respostas mais detalhadas" />
                      </div>
                      <input
                        type="range"
                        min="50"
                        max="800"
                        step="50"
                        {...register('customParameters.response_length')}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>Conciso</span>
                        <span>Detalhado</span>
                      </div>
                    </div>

                    {/* Foco */}
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Foco: {watch('customParameters.focus')}
                        </label>
                        <InfoTooltip content="Controla o foco da resposta. 1.0 considera todas as possibilidades, valores menores se focam nas mais prováveis" />
                      </div>
                      <input
                        type="range"
                        min="0.1"
                        max="1.0"
                        step="0.1"
                        {...register('customParameters.focus')}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>Focado</span>
                        <span>Diverso</span>
                      </div>
                    </div>

                    {/* Profundidade de busca */}
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Profundidade de Busca: {watch('customParameters.search_depth')}
                        </label>
                        <InfoTooltip content="Quantos resultados da base de conhecimento serão considerados. Mais resultados = mais contexto, mas pode gerar confusão" />
                      </div>
                      <input
                        type="range"
                        min="1"
                        max="10"
                        step="1"
                        {...register('customParameters.search_depth')}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>Superficial</span>
                        <span>Profunda</span>
                      </div>
                    </div>

                    {/* Filtro de relevância */}
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Filtro de Relevância: {watch('customParameters.relevance_filter')}
                        </label>
                        <InfoTooltip content="Quão relevante um resultado precisa ser para ser considerado. Valores baixos incluem mais resultados, valores altos são mais seletivos" />
                      </div>
                      <input
                        type="range"
                        min="0.01"
                        max="0.5"
                        step="0.01"
                        {...register('customParameters.relevance_filter')}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>Inclusivo</span>
                        <span>Seletivo</span>
                      </div>
                    </div>

                    {/* Re-ranking */}
                    <div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          {...register('customParameters.enable_rerank')}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <label className="text-sm text-gray-700 dark:text-gray-300">
                          Otimização de Resultados
                        </label>
                        <InfoTooltip content="Reordena os resultados da busca usando algoritmos avançados para melhor relevância (mais lento, mas mais preciso)" />
                      </div>
                    </div>
                  </div>
                )}

                {/* Lista de modelos */}
                {models.length > 0 && (
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Modelos Disponíveis
                      </label>
                      <InfoTooltip content="Todos os modelos de IA disponíveis no sistema" />
                    </div>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {models.map((model) => (
                        <div key={model.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded border">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium text-gray-900 dark:text-white">{model.name}</span>
                              <div className={`w-2 h-2 rounded-full ${model.available ? 'bg-green-400' : 'bg-red-400'}`}></div>
                            </div>
                            {model.description && (
                              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 truncate">
                                {model.description}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Bloco: Simulação */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center">
                <PlayIcon className="h-5 w-5 text-gray-400 mr-2" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Simulação RAG</h3>
              </div>
            </div>
            
            <form onSubmit={handleSubmit(handleSimulation)} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Mensagem do Lead
                </label>
                <textarea
                  {...register('message', { required: 'Mensagem é obrigatória' })}
                  className="w-full h-20 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Como faço para depositar na Quotex?"
                />
                {errors.message && (
                  <p className="mt-1 text-sm text-red-600">{errors.message.message}</p>
                )}
              </div>

              {/* Perfil de teste */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Perfil do Lead (Teste)
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      {...register('leadProfile.hasAccount')}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Tem conta em corretora</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      {...register('leadProfile.hasDeposit')}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Já depositou</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      {...register('leadProfile.wantsTest')}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Quer testar o robô</span>
                  </label>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('safeMode')}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Modo seguro (sem efeitos colaterais)</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Simulando...
                  </>
                ) : (
                  <>
                    <PlayIcon className="h-4 w-4 mr-2" />
                    Executar Simulação
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Coluna direita - Resultados e Logs */}
        <div className="space-y-6">
          
          {/* Resultado da simulação */}
          {simulationResult && (
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
              <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Resultado</h3>
              </div>
              <div className="p-4 space-y-4">
                {/* Resumo */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Classificação:</span>
                    <div className="font-medium text-gray-900 dark:text-white">{simulationResult.classification}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Tempo:</span>
                    <div className="font-medium text-gray-900 dark:text-white">{simulationResult.processing_time_ms}ms</div>
                  </div>
                </div>

                {/* Resposta final */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Resposta Final
                  </label>
                  <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                    <p className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">{simulationResult.response}</p>
                  </div>
                </div>

                {/* Top-N Results */}
                {simulationResult.top_n_results.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Top-{simulationResult.top_n_results.length} Resultados RAG
                    </label>
                    <div className="space-y-2">
                      {simulationResult.top_n_results.map((result, index) => (
                        <TopNResultCard key={index} result={result} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Logs em tempo real */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div 
              className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between cursor-pointer"
              onClick={() => setLogsExpanded(!logsExpanded)}
            >
              <div className="flex items-center">
                <ClockIcon className="h-5 w-5 text-gray-400 mr-2" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Logs em Tempo Real</h3>
                {streamActive && (
                  <div className="ml-2 flex items-center">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="ml-1 text-xs text-gray-500">Ativo</span>
                  </div>
                )}
              </div>
              {logsExpanded ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
            </div>

            {logsExpanded && (
              <div className="p-4 space-y-4">
                {/* Controles dos logs */}
                <div className="flex items-center space-x-4">
                  <input
                    type="text"
                    placeholder="Filtrar logs..."
                    value={logFilter}
                    onChange={(e) => setLogFilter(e.target.value)}
                    className="flex-1 px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                  
                  <button
                    onClick={() => setStreamPaused(!streamPaused)}
                    className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 flex items-center"
                    disabled={!streamActive}
                  >
                    <PauseIcon className="h-3 w-3 mr-1" />
                    {streamPaused ? 'Retomar' : 'Pausar'}
                  </button>

                  <button
                    onClick={() => setLogs([])}
                    className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    Limpar
                  </button>

                  {logs.length > 0 && (
                    <button
                      onClick={exportLogs}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
                    >
                      <ArrowDownTrayIcon className="h-3 w-3 mr-1" />
                      Export
                    </button>
                  )}

                  <label className="flex items-center text-sm">
                    <input
                      type="checkbox"
                      checked={autoScroll}
                      onChange={(e) => setAutoScroll(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-1"
                    />
                    Auto-scroll
                  </label>
                </div>

                {/* Lista de logs */}
                <div className="max-h-96 overflow-y-auto border border-gray-200 dark:border-gray-600 rounded">
                  {filteredLogs.length === 0 && logs.length === 0 ? (
                    <div className="p-4 text-center text-gray-500">
                      Nenhum log ainda. Execute uma simulação para ver logs em tempo real.
                    </div>
                  ) : filteredLogs.length === 0 ? (
                    <div className="p-4 text-center text-gray-500">
                      Nenhum log corresponde ao filtro.
                    </div>
                  ) : (
                    <div className="divide-y divide-gray-200 dark:divide-gray-600">
                      {filteredLogs.map((log, index) => (
                        <LogEventCard key={index} event={log} />
                      ))}
                      <div ref={logsEndRef} />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Toast Container */}
      <ToastContainer toasts={toast.toasts} onRemove={toast.removeToast} />
    </div>
  );
}

// Componente para resultado Top-N
function TopNResultCard({ result }: { result: RAGTopNResult }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-gray-200 dark:border-gray-600 rounded p-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
            {result.score.toFixed(3)}
          </span>
          <span className="text-sm text-gray-600 dark:text-gray-400">{result.source}</span>
        </div>
        {result.full_content && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-blue-600 hover:text-blue-700 flex items-center"
          >
            <EyeIcon className="h-3 w-3 mr-1" />
            {expanded ? 'Menos' : 'Mais'}
          </button>
        )}
      </div>
      
      <div className="mt-2">
        <p className="text-sm text-gray-900 dark:text-white">
          {expanded && result.full_content ? result.full_content : result.snippet}
        </p>
      </div>
    </div>
  );
}

// Componente para evento de log
function LogEventCard({ event }: { event: RAGLogEvent }) {
  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = {
      start: 'bg-gray-100 text-gray-800',
      snapshot: 'bg-blue-100 text-blue-800',
      classify: 'bg-purple-100 text-purple-800',
      retrieve: 'bg-green-100 text-green-800',
      rank: 'bg-yellow-100 text-yellow-800',
      compose: 'bg-indigo-100 text-indigo-800',
      complete: 'bg-emerald-100 text-emerald-800',
      error: 'bg-red-100 text-red-800'
    };
    return colors[stage] || 'bg-gray-100 text-gray-800';
  };

  // Verificações de segurança para evitar erros
  const safeEvent = {
    stage: event?.stage || 'unknown',
    event: event?.event || 'unknown_event',
    timestamp: event?.timestamp || Date.now() / 1000,
    duration_ms: event?.duration_ms,
    data: event?.data || {}
  };

  return (
    <div className="p-3 text-sm">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs rounded ${getStageColor(safeEvent.stage)}`}>
            {safeEvent.stage}
          </span>
          <span className="text-gray-900 dark:text-white font-medium">{safeEvent.event}</span>
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          {new Date(safeEvent.timestamp * 1000).toLocaleTimeString()}
          {safeEvent.duration_ms && <span className="ml-1">({safeEvent.duration_ms}ms)</span>}
        </div>
      </div>
      
      {safeEvent.data && Object.keys(safeEvent.data).length > 0 && (
        <div className="mt-2 text-xs text-gray-900 dark:text-gray-100 font-mono bg-gray-50 dark:bg-gray-700 p-2 rounded border">
          {JSON.stringify(safeEvent.data, null, 2)}
        </div>
      )}
    </div>
  );
}
