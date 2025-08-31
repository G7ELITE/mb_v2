import { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { 
  PlusIcon, 
  TrashIcon, 
  CheckIcon,
  InformationCircleIcon,
  LightBulbIcon,
  CogIcon,
  AdjustmentsHorizontalIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import CollapsibleSection from '../components/CollapsibleSection';


interface IntakeForm {
  llm_budget: number;
  tool_budget: number;
  max_latency_ms: number;
  direct_threshold: number;
  parallel_threshold: number;
  anchors: { group: string; words: string[] }[];
  id_patterns: { broker: string; pattern: string }[];
}

export default function Intake() {
  const [saved, setSaved] = useState(false);

  const { register, control, handleSubmit, watch, setValue } = useForm<IntakeForm>({
    defaultValues: {
      llm_budget: 1,
      tool_budget: 2,
      max_latency_ms: 3000,
      direct_threshold: 0.80,
      parallel_threshold: 0.60,
      anchors: [
        { group: 'teste', words: ['quero testar', 'teste grátis', 'liberar teste', 'começar agora'] },
        { group: 'ajuda', words: ['não consigo', 'como faço', 'preciso de ajuda', 'dúvida'] },
        { group: 'conta', words: ['criar conta', 'cadastro', 'abrir conta'] }
      ],
      id_patterns: [
        { broker: 'quotex', pattern: '\\b[a-zA-Z0-9]{6,16}\\b' },
        { broker: 'nyrion', pattern: '\\b[0-9]{6,12}\\b' }
      ]
    }
  });

  const { fields: anchorFields, append: appendAnchor, remove: removeAnchor } = useFieldArray({
    control,
    name: 'anchors'
  });

  const { fields: patternFields, append: appendPattern, remove: removePattern } = useFieldArray({
    control,
    name: 'id_patterns'
  });

  const onSubmit = async (data: IntakeForm) => {
    // TODO: Salvar via API
    console.log('Salvando config intake:', data);
    
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const addAnchorGroup = () => {
    appendAnchor({ group: '', words: [] });
  };

  const addPattern = () => {
    appendPattern({ broker: '', pattern: '' });
  };

  const updateAnchorWords = (index: number, wordsText: string) => {
    const words = wordsText.split(',').map(w => w.trim()).filter(w => w);
    setValue(`anchors.${index}.words`, words);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Intake & Âncoras</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-300">
          Ajude o sistema a entender melhor as mensagens dos leads
        </p>
      </div>

      {/* Explicação */}
      <div className="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="flex items-start">
          <InformationCircleIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-3 mt-0.5" />
          <div>
            <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-1">Como funciona o Intake Agent</h3>
            <p className="text-sm text-blue-800 dark:text-blue-200">
              O Intake Agent analisa mensagens dos leads e pode executar até 2 ferramentas por turno para enriquecer informações. 
              Configure palavras-chave e patterns para melhorar a detecção automática.
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Configurações de Precisão vs Custo */}
        <CollapsibleSection 
          title="Precisão vs. Custo" 
          icon={AdjustmentsHorizontalIcon}
          description="Configure como o sistema usa IA e ferramentas"
          defaultExpanded={false}
        >
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Usar IA quando estiver ambíguo
              </label>
              <select {...register('llm_budget')} className="input-field w-full">
                <option value={0}>Nunca (mais rápido, menos preciso)</option>
                <option value={1}>Quando necessário (recomendado)</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                LLM ajuda a interpretar mensagens complexas
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ferramentas máximas por turno
              </label>
              <select {...register('tool_budget')} className="input-field w-full">
                <option value={1}>1 ferramenta</option>
                <option value={2}>2 ferramentas (recomendado)</option>
                <option value={3}>3 ferramentas</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Verificações de cadastro e depósito
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tempo máximo de resposta
              </label>
              <select {...register('max_latency_ms')} className="input-field w-full">
                <option value={1000}>1 segundo (mais rápido)</option>
                <option value={2000}>2 segundos</option>
                <option value={3000}>3 segundos (recomendado)</option>
                <option value={5000}>5 segundos (mais completo)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Estratégia de execução
              </label>
              <div className="space-y-2 text-sm">
                <div>
                  <label className="flex items-center">
                    <span className="w-24 text-gray-600">Direta:</span>
                    <input
                      {...register('direct_threshold')}
                      type="range"
                      min="0.5"
                      max="1.0"
                      step="0.05"
                      className="mx-3 flex-1"
                    />
                    <span className="w-12 text-right">{watch('direct_threshold')}</span>
                  </label>
                </div>
                <div>
                  <label className="flex items-center">
                    <span className="w-24 text-gray-600">Paralela:</span>
                    <input
                      {...register('parallel_threshold')}
                      type="range"
                      min="0.3"
                      max="0.8"
                      step="0.05"
                      className="mx-3 flex-1"
                    />
                    <span className="w-12 text-right">{watch('parallel_threshold')}</span>
                  </label>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Thresholds de confiança para estratégias
              </p>
            </div>
          </div>
        </CollapsibleSection>

        {/* Âncoras de Intenção */}
        <CollapsibleSection 
          title="Palavras que sinalizam intenção" 
          icon={TagIcon}
          description="Configure palavras-chave que seus leads costumam usar"
          defaultExpanded={true}
        >
          <div className="flex justify-end mb-4">
            <button
              type="button"
              onClick={addAnchorGroup}
              className="btn-secondary"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Adicionar grupo
            </button>
          </div>
          
          <p className="text-sm text-gray-600 mb-4">
            Adicione as palavras que seus leads costumam usar. Ex.: "quero testar"
          </p>

          <div className="space-y-4">
            {anchorFields.map((field, index) => (
              <div key={field.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <input
                    {...register(`anchors.${index}.group`)}
                    placeholder="Nome do grupo (ex: teste)"
                    className="input-field flex-1 mr-3"
                  />
                  <button
                    type="button"
                    onClick={() => removeAnchor(index)}
                    className="text-red-600 hover:text-red-500 p-1"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    Palavras/frases (separadas por vírgula):
                  </label>
                  <textarea
                    defaultValue={field.words.join(', ')}
                    onChange={(e) => updateAnchorWords(index, e.target.value)}
                    placeholder="quero testar, teste grátis, liberar teste"
                    className="input-field w-full"
                    rows={2}
                  />
                </div>
              </div>
            ))}
          </div>
        </CollapsibleSection>

        {/* Patterns de ID */}
        <CollapsibleSection 
          title="Formas de identificar contas/IDs (opcional)" 
          icon={CogIcon}
          description="Patterns regex para detectar IDs de corretoras nas mensagens"
          defaultExpanded={false}
        >
          <div className="flex justify-end mb-4">
            <button
              type="button"
              onClick={addPattern}
              className="btn-secondary"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Adicionar pattern
            </button>
          </div>

          <div className="space-y-4">
            {patternFields.map((field, index) => (
              <div key={field.id} className="border border-gray-200 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">Corretora:</label>
                    <input
                      {...register(`id_patterns.${index}.broker`)}
                      placeholder="quotex, nyrion, etc."
                      className="input-field w-full"
                    />
                  </div>
                  <div className="flex items-end">
                    <div className="flex-1">
                      <label className="block text-xs text-gray-600 mb-1">Pattern (regex):</label>
                      <input
                        {...register(`id_patterns.${index}.pattern`)}
                        placeholder="\b[a-zA-Z0-9]{6,16}\b"
                        className="input-field w-full"
                        style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => removePattern(index)}
                      className="text-red-600 hover:text-red-500 p-2 ml-2"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start">
              <LightBulbIcon className="h-4 w-4 text-yellow-600 mr-2 mt-0.5" />
              <div className="text-xs text-yellow-800">
                <strong>Exemplos de patterns:</strong><br/>
                • Quotex: <code>{'\\b[a-zA-Z0-9]{6,16}\\b'}</code> (alfanumérico 6-16 chars)<br/>
                • Nyrion: <code>{'\\b[0-9]{6,12}\\b'}</code> (numérico 6-12 dígitos)
              </div>
            </div>
          </div>
        </CollapsibleSection>

        {/* Ações */}
        <div className="card">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-600 dark:text-gray-300">
              As configurações se aplicam imediatamente a novos leads
            </div>
            
            <button
              type="submit"
              className={`btn-primary flex items-center ${saved ? 'bg-green-600 hover:bg-green-700' : ''}`}
            >
              <CheckIcon className="h-4 w-4 mr-2" />
              {saved ? 'Salvo!' : 'Salvar Ajustes'}
            </button>
          </div>
        </div>
      </form>

      {/* Métricas */}
      <CollapsibleSection 
        title="Métricas de Performance" 
        description="Estatísticas do sistema de intake"
        defaultExpanded={false}
      >
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card text-center">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">78%</div>
            <div className="text-sm text-gray-600 dark:text-gray-300">Taxa de detecção</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">1.2s</div>
            <div className="text-sm text-gray-600 dark:text-gray-300">Tempo médio</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">23</div>
            <div className="text-sm text-gray-600 dark:text-gray-300">Âncoras ativas</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">95%</div>
            <div className="text-sm text-gray-600 dark:text-gray-300">Sucesso LLM</div>
          </div>
        </div>
      </CollapsibleSection>
    </div>
  );
}
