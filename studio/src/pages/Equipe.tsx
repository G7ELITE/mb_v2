import { useState, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import {
  PlayIcon,
  DocumentTextIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  PauseIcon,
  EyeIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  InformationCircleIcon,
  ExclamationCircleIcon,
  UserGroupIcon,
  TrashIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { useToast } from '../hooks/useToast';
import PopupContainer from '../components/PopupContainer';
import { InfoTooltip } from '../components/Tooltip';
import EquipeLayout from '../components/EquipeLayout';
import { 
  loadRAGConfig, 
  configToRAGParameters,
  useRAGConfigSync,
  type RAGGlobalConfig 
} from '../utils/ragConfig';

// Tipos específicos para EQUIPE - IDÊNTICOS à API RAG
interface EquipeParameters {
  model_id: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  top_k: number;
  threshold: number;
  re_rank: boolean;
  enable_semantic_comparison: boolean;
}

interface EquipeSimulationRequest {
  message: string;
  parameters: EquipeParameters;  // Obrigatório - IGUAL à API RAG
  safe_mode: boolean;
  session_id?: string;
  funcionario_id?: string;
}

interface EquipeSimulationResult {
  response: string;
  kb_hits: any[];
  parameters_used: EquipeParameters;
  execution_time: number;
  session_id: string;
  interaction_id: number;
  created_at: string;
}

interface EquipeInteractionHistory {
  id: number;
  pergunta_funcionario: string;
  resposta_gerada: string;
  parametros_rag: EquipeParameters | null;
  fontes_kb: any;
  funcionario_id: string | null;
  sessao_id: string | null;
  criado_em: string;
}

interface EquipeForm {
  message: string;
  selectedPreset: string;
  useCustomParameters: boolean;
  customParameters: {
    model_id: string;
    temperature: number;
    max_tokens: number;
    top_p: number;
    top_k: number;
    threshold: number;
    re_rank: boolean;
  };
  safeMode: boolean;
}

export default function Equipe() {
  // Hook de toast para feedbacks
  const toast = useToast();

  // Estados principais
  const [knowledgeBase, setKnowledgeBase] = useState<any>(null);
  const [prompt, setPrompt] = useState<any>(null);
  const [models, setModels] = useState<any[]>([]);
  const [presets, setPresets] = useState<Record<string, EquipeParameters> | null>(null);
  const [simulationResult, setSimulationResult] = useState<EquipeSimulationResult | null>(null);
  const [history, setHistory] = useState<EquipeInteractionHistory[]>([]);

  // Estados de UI
  const [loading, setLoading] = useState(false);
  const [kbLoading, setKbLoading] = useState(false);
  const [promptLoading, setPromptLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [kbExpanded, setKbExpanded] = useState(false);
  const [promptExpanded, setPromptExpanded] = useState(false);
  const [parametersExpanded, setParametersExpanded] = useState(false);
  const [historyExpanded, setHistoryExpanded] = useState(true);
  
  // Sistema de admin (por enquanto simulado - você pode implementar autenticação real)
  const [isAdmin, setIsAdmin] = useState(false);

  // Referências
  const simulationEndRef = useRef<HTMLDivElement>(null);

  // Carregar configuração global (sincronizada com tela RAG)
  const [globalConfig, setGlobalConfig] = useState<RAGGlobalConfig>(loadRAGConfig());
  const { handleConfigChange } = useRAGConfigSync();

  // Form - sempre usa configuração global da tela RAG
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<EquipeForm>({
    defaultValues: {
      message: '',
      selectedPreset: 'balanced',
      useCustomParameters: true, // Sempre usar configuração global
      customParameters: {
        model_id: globalConfig.model_id,
        temperature: globalConfig.temperature,
        max_tokens: globalConfig.max_tokens,
        top_p: globalConfig.top_p,
        top_k: globalConfig.top_k,
        threshold: globalConfig.threshold,
        re_rank: globalConfig.re_rank,
        enable_semantic_comparison: globalConfig.enable_semantic_comparison
      },
      safeMode: false
    }
  });

  // Sincronizar com mudanças nas configurações da tela RAG
  useEffect(() => {
    const cleanup = handleConfigChange((newConfig) => {
      console.log('🔄 Equipe: Configurações atualizadas da tela RAG:', newConfig);
      setGlobalConfig(newConfig);
      
      // Atualizar valores do form
      setValue('customParameters.model_id', newConfig.model_id);
      setValue('customParameters.temperature', newConfig.temperature);
      setValue('customParameters.max_tokens', newConfig.max_tokens);
      setValue('customParameters.top_p', newConfig.top_p);
      setValue('customParameters.top_k', newConfig.top_k);
      setValue('customParameters.threshold', newConfig.threshold);
      setValue('customParameters.re_rank', newConfig.re_rank);
      setValue('customParameters.enable_semantic_comparison', newConfig.enable_semantic_comparison);
    });

    return cleanup;
  }, [handleConfigChange, setValue]);

  const watchAll = watch();

  // Carregar dados iniciais
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      // Carregar knowledge base
      setKbLoading(true);
      const kbResponse = await apiService.getEquipeKnowledgeBase();
      setKnowledgeBase(kbResponse);

      // Carregar prompt
      setPromptLoading(true);
      const promptResponse = await apiService.getEquipePrompt();
      setPrompt(promptResponse);

      // Carregar parâmetros e modelos
      const parametersResponse = await apiService.getEquipeParameters();
      setPresets(parametersResponse.presets);
      setModels(parametersResponse.models || []);

      // Carregar histórico
      await loadHistory();

    } catch (error: any) {
      console.error('Erro ao carregar dados:', error);
      toast.error('Erro ao carregar configurações da EQUIPE');
      setError(error?.response?.data?.detail || 'Erro interno');
    } finally {
      setKbLoading(false);
      setPromptLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      setHistoryLoading(true);
      const response = await apiService.getEquipeHistory({ limit: 50 });
      setHistory(response);
    } catch (error: any) {
      console.error('Erro ao carregar histórico:', error);
      toast.error('Erro ao carregar histórico da equipe');
    } finally {
      setHistoryLoading(false);
    }
  };

  const onSubmit = async (data: EquipeForm) => {
    if (!data.message.trim()) {
      toast.error('Digite uma pergunta para a equipe');
      return;
    }

    setLoading(true);
    setError('');
    setSimulationResult(null);

    try {
      // USAR CONFIGURAÇÃO GLOBAL SINCRONIZADA COM TELA RAG
      const request: EquipeSimulationRequest = {
        message: data.message.trim(),
        parameters: configToRAGParameters(globalConfig),
        safe_mode: data.safeMode
      };

      const response = await apiService.simulateEquipe(request);
      setSimulationResult(response);
      
      // Recarregar histórico após simulação
      await loadHistory();
      
      toast.success('Resposta gerada para a equipe!');

      // Auto-scroll para resultado
      setTimeout(() => {
        simulationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);

    } catch (error: any) {
      console.error('Erro na simulação da equipe:', error);
      const errorMessage = error?.response?.data?.detail || 'Erro interno na simulação';
      setError(errorMessage);
      toast.error(`Erro na simulação: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const deleteInteraction = async (interactionId: number) => {
    try {
      await apiService.deleteEquipeInteraction(interactionId);
      await loadHistory();
      toast.success('Interação removida do histórico');
    } catch (error: any) {
      console.error('Erro ao remover interação:', error);
      toast.error('Erro ao remover interação');
    }
  };


  const toggleAdmin = () => {
    setIsAdmin(!isAdmin);
    toast.info(`Modo admin ${!isAdmin ? 'ativado' : 'desativado'}`);
  };

  return (
    <EquipeLayout showSidebar={isAdmin}>
      <div className={`${isAdmin ? 'py-8' : 'py-8'} bg-gray-50 dark:bg-gray-900 min-h-screen`}>
        <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <UserGroupIcon className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Sistema EQUIPE</h1>
                <p className="text-gray-600">Ferramenta RAG dedicada para equipe de atendimento</p>
              </div>
            </div>
            
            {/* Toggle Admin - Botão Discreto/Secreto */}
            <div
              onClick={toggleAdmin}
              className="cursor-pointer opacity-30 hover:opacity-100 transition-opacity text-xs text-gray-400 hover:text-gray-600 dark:text-gray-600 dark:hover:text-gray-400 select-none"
              title={isAdmin ? 'Modo Admin Ativo' : 'Clique para ativar modo admin'}
            >
              {isAdmin ? '●' : '○'} {isAdmin ? 'Admin' : 'User'}
            </div>
          </div>
        </div>

        {/* Sistema de Informações (só para admin) */}
        {isAdmin && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* Knowledge Base Status */}
            <div 
              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                kbExpanded ? 'border-blue-300 bg-blue-50 dark:bg-blue-900 dark:border-blue-600' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
              onClick={() => setKbExpanded(!kbExpanded)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <DocumentTextIcon className="w-6 h-6 text-green-600" />
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Knowledge Base</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {kbLoading ? 'Carregando...' : 
                        knowledgeBase ? `${knowledgeBase.topics} tópicos` : 'Não carregado'}
                    </p>
                  </div>
                </div>
                {kbExpanded ? <ChevronUpIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" /> : <ChevronDownIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" />}
              </div>
              
              {kbExpanded && knowledgeBase && (
                <div className="mt-4 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">Status:</span>
                    <span className={`font-medium ${knowledgeBase.status === 'loaded' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {knowledgeBase.status === 'loaded' ? 'Carregado' : 'Vazio'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">Tópicos:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{knowledgeBase.topics}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Prompt Status */}
            <div 
              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                promptExpanded ? 'border-purple-300 bg-purple-50 dark:bg-purple-900 dark:border-purple-600' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
              onClick={() => setPromptExpanded(!promptExpanded)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <CpuChipIcon className="w-6 h-6 text-purple-600" />
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Prompt</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {promptLoading ? 'Carregando...' :
                        prompt ? (prompt.is_custom ? 'Customizado' : 'Padrão') : 'Não carregado'}
                    </p>
                  </div>
                </div>
                {promptExpanded ? <ChevronUpIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" /> : <ChevronDownIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" />}
              </div>
              
              {promptExpanded && prompt && (
                <div className="mt-4">
                  <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded text-sm font-mono max-h-40 overflow-y-auto text-gray-900 dark:text-gray-100">
                    {prompt.content?.substring(0, 200)}...
                  </div>
                </div>
              )}
            </div>

            {/* Parâmetros */}
            <div 
              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                parametersExpanded ? 'border-orange-300 bg-orange-50 dark:bg-orange-900 dark:border-orange-600' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
              onClick={() => setParametersExpanded(!parametersExpanded)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <CpuChipIcon className="w-6 h-6 text-orange-600" />
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Parâmetros</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">{watchAll.selectedPreset || 'balanced'}</p>
                  </div>
                </div>
                {parametersExpanded ? <ChevronUpIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" /> : <ChevronDownIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" />}
              </div>
              
              {parametersExpanded && presets && (
                <div className="mt-4 space-y-2 text-sm">
                  {Object.entries(presets).map(([key, preset]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-300 capitalize">{key}:</span>
                      <span className="font-medium text-gray-900 dark:text-white">T:{preset.temperature} | K:{preset.top_k}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Seção de Simulação (sempre visível) */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center space-x-3 mb-6">
              <PlayIcon className="w-6 h-6 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Simulação para Equipe</h2>
              <InfoTooltip content="Digite a pergunta do lead para gerar uma resposta usando o sistema RAG" />
            </div>

            <div className="space-y-4">
              {/* Mensagem do Lead */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Pergunta do Lead <span className="text-red-500">*</span>
                </label>
                <textarea
                  {...register('message', { required: 'Digite a pergunta do lead' })}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                  rows={4}
                  placeholder="Ex: Quero saber sobre como funciona o depósito..."
                />
                {errors.message && (
                  <p className="text-red-500 text-sm mt-1">{errors.message.message}</p>
                )}
              </div>

              {/* Configurações (só para admin) */}
              {/* Indicador de Configuração Global */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
                <div className="flex items-center space-x-2">
                  <div className="flex-shrink-0">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-200">
                      Configurações Sincronizadas
                    </p>
                  </div>
                  {isAdmin && (
                    <div className="flex-shrink-0">
                      <button
                        type="button"
                        onClick={() => window.open('/rag', '_blank')}
                        className="text-blue-600 hover:text-blue-800 text-xs underline"
                      >
                        Configurar na tela RAG
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Botão de Enviar */}
              <div className="flex justify-between items-center pt-4">
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {loading ? 'Gerando resposta...' : 'Pronto para gerar resposta'}
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-2 rounded-md font-medium flex items-center space-x-2"
                >
                  {loading ? <ClockIcon className="w-5 h-5 animate-spin" /> : <PlayIcon className="w-5 h-5" />}
                  <span>{loading ? 'Processando...' : 'Gerar Resposta'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Resultado da Simulação */}
          {(simulationResult || error) && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <div className="flex items-center space-x-3 mb-4">
                {error ? (
                  <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                ) : (
                  <CheckCircleIcon className="w-6 h-6 text-green-600" />
                )}
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {error ? 'Erro na Simulação' : 'Resposta para Equipe'}
                </h2>
              </div>

              {error ? (
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <p className="text-red-800">{error}</p>
                </div>
              ) : simulationResult ? (
                <div className="space-y-4">
                  {/* Resposta Principal */}
                  <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-md p-4">
                    <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-2">Resposta Sugerida:</h3>
                    <div className="text-blue-800 dark:text-blue-200 whitespace-pre-wrap">
                      {simulationResult.response}
                    </div>
                  </div>

                  {/* Informações da Execução (só para admin) */}
                  {isAdmin && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded">
                        <span className="text-gray-600 dark:text-gray-300">Tempo de execução:</span>
                        <div className="font-medium text-gray-900 dark:text-white">
                          {simulationResult.execution_time.toFixed(2)}s
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded">
                        <span className="text-gray-600 dark:text-gray-300">Fontes encontradas:</span>
                        <div className="font-medium text-gray-900 dark:text-white">
                          {simulationResult.kb_hits.length}
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded">
                        <span className="text-gray-600 dark:text-gray-300">ID da interação:</span>
                        <div className="font-medium text-gray-900 dark:text-white">
                          #{simulationResult.interaction_id}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Fontes da KB (só para admin) */}
                  {isAdmin && simulationResult.kb_hits.length > 0 && (
                    <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                      <h3 className="font-medium text-gray-900 dark:text-white mb-3">Fontes Consultadas:</h3>
                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {simulationResult.kb_hits.map((hit, index) => (
                          <div key={index} className="bg-gray-50 dark:bg-gray-700 p-3 rounded text-sm">
                            <div className="flex justify-between items-start mb-2">
                              <span className="font-medium text-gray-900 dark:text-white">
                                {hit.fonte || `Fonte ${index + 1}`}
                              </span>
                              <span className="text-gray-600 dark:text-gray-300">
                                Score: {(hit.score * 100).toFixed(1)}%
                              </span>
                            </div>
                            <p className="text-gray-700 dark:text-gray-300 line-clamp-3">
                              {hit.texto?.substring(0, 200)}...
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : null}
              <div ref={simulationEndRef} />
            </div>
          )}

          {/* Histórico de Interações */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <ClockIcon className="w-6 h-6 text-gray-600" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Histórico da Equipe</h2>
                <span className="bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 px-2 py-1 rounded-full text-sm">
                  {history.length}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={loadHistory}
                  disabled={historyLoading}
                  className="text-gray-600 hover:text-gray-900 p-2"
                  title="Atualizar histórico"
                >
                  <ClockIcon className={`w-5 h-5 ${historyLoading ? 'animate-spin' : ''}`} />
                </button>
                
                <button
                  type="button"
                  onClick={() => setHistoryExpanded(!historyExpanded)}
                  className="text-gray-600 hover:text-gray-900 p-2"
                >
                  {historyExpanded ? <ChevronUpIcon className="w-5 h-5" /> : <ChevronDownIcon className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {historyExpanded && (
              <div className="space-y-4">
                {historyLoading ? (
                  <div className="flex justify-center py-8">
                    <ClockIcon className="w-8 h-8 text-gray-400 animate-spin" />
                  </div>
                ) : history.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <UserGroupIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Nenhuma interação da equipe encontrada</p>
                    <p className="text-sm">Faça uma pergunta para começar o histórico</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {history.slice(0, 3).map((interaction) => (
                      <div key={interaction.id} className="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              #{interaction.id}
                            </span>
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              {new Date(interaction.criado_em).toLocaleString('pt-BR')}
                            </span>
                          </div>
                          
                          {isAdmin && (
                            <button
                              onClick={() => deleteInteraction(interaction.id)}
                              className="text-red-600 hover:text-red-800 p-1"
                              title="Remover interação"
                            >
                              <TrashIcon className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                        
                        <div className="space-y-3">
                          <div>
                            <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Pergunta:</div>
                            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded text-sm text-gray-900 dark:text-gray-100">
                              {interaction.pergunta_funcionario}
                            </div>
                          </div>
                          
                          <div>
                            <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Resposta:</div>
                            <div className="bg-blue-50 dark:bg-blue-900/30 p-3 rounded text-sm text-gray-900 dark:text-blue-100">
                              {interaction.resposta_gerada}
                            </div>
                          </div>
                          
                          {isAdmin && interaction.fontes_kb && (
                            <details className="text-sm">
                              <summary className="cursor-pointer text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100">
                                Fontes ({interaction.fontes_kb.total || 0})
                              </summary>
                              <div className="mt-2 space-y-1">
                                {interaction.fontes_kb.hits?.map((hit: any, idx: number) => (
                                  <div key={idx} className="bg-gray-100 dark:bg-gray-700 p-2 rounded text-xs">
                                    <div className="font-medium text-gray-900 dark:text-white">{hit.fonte}</div>
                                    <div className="text-gray-600 dark:text-gray-300">{hit.texto?.substring(0, 100)}...</div>
                                  </div>
                                ))}
                              </div>
                            </details>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </form>
      </div>
      </div>
    </EquipeLayout>
  );
}
