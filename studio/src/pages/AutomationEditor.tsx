import { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  PlusIcon, 
  TrashIcon, 
  PlayIcon,
  ArrowLeftIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import type { Automation } from '../types';
import { automationStorage } from '../services/automationStorage';

interface AutomationForm {
  id: string;
  topic: string;
  eligibility: string;
  priority: number;
  cooldown: string;
  output: {
    type: string;
    text: string;
    buttons: Array<{
      id: string;
      label: string;
      kind: 'url' | 'callback' | 'quick_reply';
      url?: string;
      set_facts?: string;
    }>;
  };
}

export default function AutomationEditor() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = !!id;
  
  const [error, setError] = useState<string>('');
  const [saving, setSaving] = useState(false);

  const { register, handleSubmit, watch, control, reset, formState: { errors } } = useForm<AutomationForm>({
    defaultValues: {
      id: '',
      topic: '',
      eligibility: '',
      priority: 0.5,
      cooldown: '1h',
      output: {
        type: 'message',
        text: '',
        buttons: []
      }
    }
  });

  // Carregar automação para edição
  useEffect(() => {
    if (isEditing && id) {
      const automation = automationStorage.getById(id);
      if (automation) {
        reset({
          id: automation.id,
          topic: automation.topic,
          eligibility: automation.eligibility,
          priority: automation.priority,
          cooldown: automation.cooldown,
          output: {
            type: automation.output.type,
            text: automation.output.text,
            buttons: automation.output.buttons?.map(button => ({
              id: button.id,
              label: button.label,
              kind: button.kind,
              url: button.url || '',
              set_facts: button.set_facts ? JSON.stringify(button.set_facts, null, 2) : '{}'
            })) || []
          }
        });
      } else {
        setError(`Automação com ID "${id}" não encontrada`);
      }
    }
  }, [isEditing, id, reset]);

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'output.buttons'
  });

  const watchedValues = watch();

  const onSubmit = async (data: AutomationForm) => {
    setSaving(true);
    setError('');
    
    try {
      // Processar dados do formulário
      const automation: Automation = {
        id: data.id,
        topic: data.topic,
        eligibility: data.eligibility,
        priority: data.priority,
        cooldown: data.cooldown,
        output: {
          type: data.output.type,
          text: data.output.text,
          buttons: data.output.buttons.map(button => ({
            id: button.id,
            label: button.label,
            kind: button.kind,
            ...(button.kind === 'url' && { url: button.url }),
            ...(button.kind === 'callback' && { 
              set_facts: typeof button.set_facts === 'string' 
                ? JSON.parse(button.set_facts || '{}') 
                : (button.set_facts || {})
            })
          }))
        }
      };

      // Salvar automação
      if (isEditing) {
        automationStorage.update(id!, automation);
      } else {
        automationStorage.add(automation);
      }
      
      // Simular delay mínimo para UX
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Navegar de volta para lista
      navigate('/automations');
    } catch (err: any) {
      setError(err.message || 'Erro ao salvar automação');
    } finally {
      setSaving(false);
    }
  };

  const addButton = () => {
    append({
      id: `btn_${Date.now()}`,
      label: '',
      kind: 'callback',
      set_facts: '{}'
    });
  };

  const getPreview = () => {
    if (!watchedValues.output.text) return null;
    
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="text-sm font-medium text-gray-700 mb-2">Preview da Mensagem:</div>
        <div className="bg-gray-900 rounded-lg p-3">
          <div className="text-gray-900 whitespace-pre-wrap mb-3">
            {watchedValues.output.text}
          </div>
          {watchedValues.output.buttons.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {watchedValues.output.buttons.map((button, index) => (
                button.label && (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    {button.label}
                    {button.kind === 'url' && ' 🔗'}
                  </span>
                )
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/automations')}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg"
          >
            <ArrowLeftIcon className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {isEditing ? 'Editar Automação' : 'Nova Automação'}
            </h1>
            <p className="text-gray-600">
              {isEditing ? 'Modifique a automação existente' : 'Crie uma nova automação para o catálogo'}
            </p>
          </div>
        </div>
        
        <div className="flex space-x-3">
          <button
            type="button"
            onClick={() => navigate('/automations')}
            className="btn-secondary"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit(onSubmit)}
            disabled={saving}
            className="btn-primary flex items-center"
          >
            {saving ? (
              <>
                <div className="animate-spin h-4 w-4 mr-2 border-2 border-white border-t-transparent rounded-full" />
                Salvando...
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4 mr-2" />
                {isEditing ? 'Atualizar' : 'Criar'} Automação
              </>
            )}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Formulário */}
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Configurações Básicas</h2>
            
            <form className="space-y-4">
              {/* ID */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ID da Automação *
                </label>
                <input
                  {...register('id', { required: 'ID é obrigatório' })}
                  className="input-field w-full"
                  placeholder="ex: ask_deposit_for_test"
                />
                {errors.id && (
                  <p className="mt-1 text-sm text-red-600">{errors.id.message}</p>
                )}
              </div>

              {/* Tópico */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tópico *
                </label>
                <input
                  {...register('topic', { required: 'Tópico é obrigatório' })}
                  className="input-field w-full"
                  placeholder="ex: teste, conta, deposito"
                />
                {errors.topic && (
                  <p className="mt-1 text-sm text-red-600">{errors.topic.message}</p>
                )}
              </div>

              {/* Elegibilidade */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Condição de Elegibilidade *
                </label>
                <textarea
                  {...register('eligibility', { required: 'Elegibilidade é obrigatória' })}
                  rows={2}
                  className="input-field w-full"
                  placeholder="ex: não concordou em depositar e não depositou"
                />
                {errors.eligibility && (
                  <p className="mt-1 text-sm text-red-600">{errors.eligibility.message}</p>
                )}
              </div>

              {/* Prioridade */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prioridade (0.0 - 1.0)
                </label>
                <input
                  {...register('priority', { 
                    required: 'Prioridade é obrigatória',
                    min: { value: 0, message: 'Mínimo 0.0' },
                    max: { value: 1, message: 'Máximo 1.0' }
                  })}
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  className="input-field w-full"
                />
                {errors.priority && (
                  <p className="mt-1 text-sm text-red-600">{errors.priority.message}</p>
                )}
              </div>

              {/* Cooldown */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cooldown
                </label>
                <select {...register('cooldown')} className="input-field w-full">
                  <option value="0h">Sem cooldown</option>
                  <option value="1h">1 hora</option>
                  <option value="12h">12 horas</option>
                  <option value="24h">24 horas</option>
                  <option value="48h">48 horas</option>
                </select>
              </div>
            </form>
          </div>

          {/* Mensagem */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Conteúdo da Mensagem</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Texto da Mensagem *
                </label>
                <textarea
                  {...register('output.text', { required: 'Texto é obrigatório' })}
                  rows={4}
                  className="input-field w-full"
                  placeholder="Digite a mensagem que será enviada..."
                />
                {errors.output?.text && (
                  <p className="mt-1 text-sm text-red-600">{errors.output.text.message}</p>
                )}
              </div>

              {/* Botões */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-gray-700">
                    Botões (opcional)
                  </label>
                  <button
                    type="button"
                    onClick={addButton}
                    className="inline-flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                  >
                    <PlusIcon className="h-4 w-4 mr-1" />
                    Adicionar Botão
                  </button>
                </div>

                {fields.map((field, index) => (
                  <div key={field.id} className="border border-gray-200 rounded-lg p-4 mb-3">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium text-gray-700">Botão {index + 1}</span>
                      <button
                        type="button"
                        onClick={() => remove(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Texto do Botão
                        </label>
                        <input
                          {...register(`output.buttons.${index}.label`)}
                          className="input-field w-full text-sm"
                          placeholder="ex: Sim, consigo"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Tipo
                        </label>
                        <select 
                          {...register(`output.buttons.${index}.kind`)}
                          className="input-field w-full text-sm"
                        >
                          <option value="callback">Callback (define fatos)</option>
                          <option value="url">URL (link externo)</option>
                          <option value="quick_reply">Resposta rápida</option>
                        </select>
                      </div>
                    </div>

                    {watch(`output.buttons.${index}.kind`) === 'url' && (
                      <div className="mb-3">
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          URL
                        </label>
                        <input
                          {...register(`output.buttons.${index}.url`)}
                          className="input-field w-full text-sm"
                          placeholder="https://..."
                        />
                      </div>
                    )}

                    {watch(`output.buttons.${index}.kind`) === 'callback' && (
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Fatos a Definir (JSON)
                        </label>
                        <textarea
                          {...register(`output.buttons.${index}.set_facts`)}
                          rows={2}
                          className="input-field w-full text-sm font-mono"
                          placeholder='{"agreements.can_deposit": true}'
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Preview */}
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Preview</h2>
            {getPreview() || (
              <div className="text-center py-8 text-gray-500">
                <ExclamationCircleIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>Digite o texto da mensagem para ver o preview</p>
              </div>
            )}
          </div>

          {/* Dicas */}
          <div className="card bg-blue-50 border-blue-200">
            <h3 className="font-medium text-blue-900 mb-3">💡 Dicas</h3>
            <ul className="text-sm text-blue-800 space-y-2">
              <li>• Use IDs únicos e descritivos</li>
              <li>• Prioridade alta (0.8+) aparece primeiro</li>
              <li>• Botões callback podem definir fatos como agreements.can_deposit</li>
              <li>• Use cooldown para evitar spam</li>
              <li>• Teste sempre no simulador antes de publicar</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-100 border border-red-200 text-red-700 px-4 py-3 rounded-lg shadow-lg">
          <div className="flex items-center">
            <ExclamationCircleIcon className="h-5 w-5 mr-2" />
            {error}
          </div>
        </div>
      )}
    </div>
  );
}
