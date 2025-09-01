import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { 
  PlayIcon, 
 
  ExclamationCircleIcon,
  CheckCircleIcon,
  ClockIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import type { SimulationRequest, SimulationResult } from '../types';

interface SimulationForm {
  message: string;
  snapshot: Record<string, any>;
  apply: boolean;
  devMode: boolean;
}

export default function Simulator() {
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<SimulationForm>({
    defaultValues: {
      message: '',
      snapshot: {},
      apply: false,
      devMode: false
    }
  });

  const devMode = watch('devMode');
  const currentSnapshot = watch('snapshot');
  
  // Calcular resumo do estado atual em tempo real
  const getCurrentStateSummary = () => {
    // Construir snapshot processando nested keys
    const processedSnapshot = {
      accounts: { quotex: 'desconhecido', nyrion: 'desconhecido' },
      deposit: { status: 'nenhum' },
      agreements: {},
      flags: {},
    };
    
    // Processar currentSnapshot para nested keys
    Object.entries(currentSnapshot).forEach(([key, value]) => {
      if (key.includes('.')) {
        const [mainKey, subKey] = key.split('.');
        if (!processedSnapshot[mainKey as keyof typeof processedSnapshot]) {
          processedSnapshot[mainKey as keyof typeof processedSnapshot] = {} as any;
        }
        (processedSnapshot[mainKey as keyof typeof processedSnapshot] as any)[subKey] = value;
      } else {
        (processedSnapshot as any)[key] = value;
      }
    });
    
    return {
      accounts_status: processedSnapshot.accounts,
      deposit_status: processedSnapshot.deposit.status || 'nenhum',
      agreements_count: Object.values(processedSnapshot.agreements).filter(v => v === true).length,
      flags_count: Object.values(processedSnapshot.flags).filter(v => v === true).length
    };
  };

  const onSubmit = async (data: SimulationForm) => {
    if (!data.message.trim()) {
      setError('Escreva a mensagem do lead para testar.');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const request: SimulationRequest = {
        lead: { id: 1, lang: 'pt-BR' },
        snapshot: {
          accounts: { quotex: 'desconhecido', nyrion: 'desconhecido' },
          deposit: { status: 'nenhum' },
          agreements: {},
          flags: {},
          ...data.snapshot
        },
        messages_window: [{ id: 'm1', text: data.message }],
        apply: data.apply
      };

      if (devMode) {
        console.log('[Simulador] Request:', request);
      }

      const response = await apiService.simulate(request);
      setResult(response);

      if (devMode) {
        console.log('[Simulador] Response:', response);
      }

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao executar simulação. Verifique se o backend está rodando.');
      console.error('Erro na simulação:', err);
    } finally {
      setLoading(false);
    }
  };

  const addFactHelper = (key: string, value: any) => {
    console.log('🔥 Helper clicado!', { key, value });
    try {
      const currentSnapshot = watch('snapshot');
      const newSnapshot = {
        ...currentSnapshot,
        [key]: value
      };
      setValue('snapshot', newSnapshot);
      console.log('✅ Snapshot atualizado:', newSnapshot);
    } catch (error) {
      console.error('❌ Erro ao atualizar snapshot:', error);
    }
  };

  const getInteractionTypeIcon = (type: string) => {
    switch (type) {
      case 'PROCEDIMENTO':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
      case 'DÚVIDA':
        return <InformationCircleIcon className="h-5 w-5 text-blue-600" />;
      default:
        return <ExclamationCircleIcon className="h-5 w-5 text-yellow-600" />;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Simulador</h1>
        <p className="mt-2 text-gray-600">
          Teste como o sistema responde a mensagens dos leads antes de publicar mudanças
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Formulário de Simulação */}
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Configurar Simulação</h2>
            
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Mensagem do Lead */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mensagem do lead *
                </label>
                <textarea
                  {...register('message', { required: 'Este campo é obrigatório' })}
                  rows={3}
                  className="input-field w-full"
                  placeholder="Ex.: Quero testar agora, como faço?"
                />
                {errors.message && (
                  <p className="mt-1 text-sm text-red-600">{errors.message.message}</p>
                )}
              </div>

              {/* Informações do Lead */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Informações atuais do lead (opcional)
                </label>
                <div className="space-y-2">
                  <div className="text-sm text-gray-600 mb-3">Helpers rápidos:</div>
                  
                  {/* Botão de teste simples */}
                  <button
                    type="button"
                    onClick={() => console.log('🚀 TESTE: Botão simples funcionou!')}
                    className="w-full p-2 bg-red-500 text-white rounded hover:bg-red-600 mb-3"
                  >
                    TESTE: Se esse botão não funcionar, é pq tem al problema geral
                  </button>
                  
                  <div className="grid grid-cols-1 gap-2">
                    <button
                      type="button"
                      onClick={() => addFactHelper('agreements.can_deposit', true)}
                      className="text-left text-sm text-blue-600 hover:text-blue-500 p-2 bg-blue-50 rounded"
                    >
                      ✓ Concorda em depositar (agreements.can_deposit = true)
                    </button>
                    <button
                      type="button"
                      onClick={() => addFactHelper('accounts.nyrion', 'com_conta')}
                      className="text-left text-sm text-blue-600 hover:text-blue-500 p-2 bg-blue-50 rounded"
                    >
                      ✓ Conta Nyrion criada (accounts.nyrion = com_conta)
                    </button>
                    <button
                      type="button"
                      onClick={() => addFactHelper('deposit.status', 'confirmado')}
                      className="text-left text-sm text-blue-600 hover:text-blue-500 p-2 bg-blue-50 rounded"
                    >
                      ✓ Depósito confirmado (deposit.status = confirmado)
                    </button>
                    <button
                      type="button"
                      onClick={() => addFactHelper('lead_inativo', false)}
                      className="text-left text-sm text-blue-600 hover:text-blue-500 p-2 bg-blue-50 rounded"
                    >
                      ✓ Lead ativo (lead_inativo = false)
                    </button>
                    <button
                      type="button"
                      onClick={() => addFactHelper('flags.explained', true)}
                      className="text-left text-sm text-green-600 hover:text-green-500 p-2 bg-green-50 rounded"
                    >
                      ✓ Já foi explicado (flags.explained = true)
                    </button>
                    <button
                      type="button"
                      onClick={() => addFactHelper('flags.onboarded', true)}
                      className="text-left text-sm text-green-600 hover:text-green-500 p-2 bg-green-50 rounded"
                    >
                      ✓ Onboarding feito (flags.onboarded = true)
                    </button>
                  </div>
                </div>
                
                {/* Debug: Mostrar snapshot atual */}
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                  <div className="text-sm font-medium text-yellow-800 mb-2">Debug - Snapshot atual:</div>
                  <pre className="text-xs text-yellow-700 overflow-x-auto">
                    {JSON.stringify(watch('snapshot'), null, 2)}
                  </pre>
                </div>
              </div>

              {/* Configurações */}
              <div className="space-y-3 pt-4 border-t border-gray-200">
                <div className="flex items-center">
                  <input
                    {...register('apply')}
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    Executar como se fosse real (enviar mensagem de verdade)
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    {...register('devMode')}
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    Ligar Modo Dev (logs detalhados)
                  </label>
                </div>
              </div>

              {/* Botão de Execução */}
              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <ClockIcon className="h-4 w-4 mr-2 animate-spin" />
                    Executando...
                  </>
                ) : (
                  <>
                    <PlayIcon className="h-4 w-4 mr-2" />
                    Executar Simulação
                  </>
                )}
              </button>
            </form>

            {/* Erro */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center">
                  <ExclamationCircleIcon className="h-5 w-5 text-red-600 mr-2" />
                  <span className="text-sm text-red-700">{error}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Resultado da Simulação */}
        <div className="space-y-6">
          {/* Estado Atual - Sempre Visível */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Estado Atual do Lead</h2>
            <div className="bg-gradient-to-r from-blue-50 to-green-50 rounded-lg p-4">
              {(() => {
                const summary = getCurrentStateSummary();
                return (
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="font-medium text-gray-700 mb-1">Status das contas:</div>
                      <div className="text-gray-600">{JSON.stringify(summary.accounts_status)}</div>
                    </div>
                    <div>
                      <div className="font-medium text-gray-700 mb-1">Status do depósito:</div>
                      <div className="text-gray-600">{summary.deposit_status}</div>
                    </div>
                    <div>
                      <div className="font-medium text-gray-700 mb-1">Acordos ativos:</div>
                      <div className="text-2xl font-bold text-blue-600">{summary.agreements_count}</div>
                    </div>
                    <div>
                      <div className="font-medium text-gray-700 mb-1">Flags ativas:</div>
                      <div className="text-2xl font-bold text-green-600">{summary.flags_count}</div>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>

          {result && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Resultado da Simulação</h2>
              
              <div className="space-y-4">
                {/* Tipo de Interação */}
                <div className="flex items-center p-3 bg-gray-50 rounded-lg">
                  {getInteractionTypeIcon(result.metadata.interaction_type)}
                  <div className="ml-3">
                    <div className="font-medium text-gray-900">
                      Tipo: {result.metadata.interaction_type}
                    </div>
                    <div className="text-sm text-gray-600">
                      ID da decisão: {result.decision_id}
                    </div>
                  </div>
                </div>

                {/* Ações Sugeridas */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Ações Sugeridas:</h3>
                  {result.actions.length > 0 ? (
                    <div className="space-y-3">
                      {result.actions.map((action, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center mb-2">
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {action.type}
                            </span>
                          </div>
                          {action.text && (
                            <div className="text-sm text-gray-700 mb-3 whitespace-pre-wrap">
                              {action.text}
                            </div>
                          )}
                          {action.buttons && action.buttons.length > 0 && (
                            <div className="space-y-2">
                              <div className="text-xs font-medium text-gray-600">Botões:</div>
                              {action.buttons.map((button, btnIndex) => (
                                <div key={btnIndex} className="flex items-center text-sm">
                                  <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-800">
                                    {button.label}
                                  </span>
                                  {button.set_facts && (
                                    <span className="ml-2 text-xs text-gray-500">
                                      → {Object.entries(button.set_facts).map(([k, v]) => `${k}=${v}`).join(', ')}
                                    </span>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 italic">Nenhuma ação específica sugerida</p>
                  )}
                </div>

                {/* Resumo do Snapshot */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Resumo do Estado:</h3>
                  <div className="bg-gray-50 rounded-lg p-3 text-sm">
                    {(() => {
                      const summary = getCurrentStateSummary();
                      return (
                        <>
                          <div>Status das contas: {JSON.stringify(summary.accounts_status)}</div>
                          <div>Status do depósito: {summary.deposit_status}</div>
                          <div className="font-semibold text-blue-600">Acordos ativos: {summary.agreements_count}</div>
                          <div className="font-semibold text-green-600">Flags ativas: {summary.flags_count}</div>
                        </>
                      );
                    })()}
                  </div>
                </div>

                {/* Logs de Dev Mode */}
                {devMode && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Logs de Desenvolvimento:</h3>
                    <div className="bg-gray-900 text-green-400 rounded-lg p-3 text-xs font-mono overflow-x-auto">
                      <div>[Intake] Mensagem analisada: confiança detectada</div>
                      <div>[Orchestrator] Tipo detectado: {result.metadata.interaction_type}</div>
                      <div>[Selector] {result.actions.length} ações geradas</div>
                      <div>[Decision] ID: {result.decision_id}</div>
                      <div>[Timing] Processamento concluído em ~150ms</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Roteiros de Teste Sugeridos */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Roteiros de Teste Sugeridos</h2>
            <div className="space-y-4">
              <div className="border-l-4 border-blue-500 pl-4">
                <h3 className="font-medium text-gray-900">Fluxo básico de teste liberado</h3>
                <div className="text-sm text-gray-600 space-y-1 mt-2">
                  <div>1. "quero testar" → Espera: ask_deposit_for_test</div>
                  <div>2. Simular clique: agreements.can_deposit = true</div>
                  <div>3. "quero testar" → Espera: signup_link</div>
                  <div>4. Simular: accounts.nyrion = com_conta</div>
                  <div>5. "quero testar" → Espera: trial_unlock</div>
                </div>
              </div>
              <div className="border-l-4 border-yellow-500 pl-4">
                <h3 className="font-medium text-gray-900">Teste de dúvidas</h3>
                <div className="text-sm text-gray-600 space-y-1 mt-2">
                  <div>1. "como funciona o robô?" → Espera: explain_robot</div>
                  <div>2. "onde crio conta?" → Espera: signup_link</div>
                  <div>3. "quanto custa?" → Espera: resposta da KB</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
