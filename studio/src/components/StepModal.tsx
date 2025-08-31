import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { XMarkIcon } from '@heroicons/react/24/outline';
import type { ProcedureStep } from '../types';
import { COMMON_CONDITIONS, AUTOMATION_IDS } from '../types';
import AutocompleteInput from './AutocompleteInput';

interface StepModalProps {
  step?: ProcedureStep;
  onSave: (step: ProcedureStep) => void;
  onClose: () => void;
}

interface StepForm {
  name: string;
  condition: string;
  fallback_action: 'automation' | 'procedure';
  fallback_automation: string;
  fallback_procedure: string;
  final_action: 'next' | 'automation' | 'procedure';
  final_automation: string;
  final_procedure: string;
}

export default function StepModal({ step, onSave, onClose }: StepModalProps) {
  const [errors, setErrors] = useState<string[]>([]);

  const { register, handleSubmit, watch, setValue } = useForm<StepForm>({
    defaultValues: {
      name: step?.name || '',
      condition: step?.condition || '',
      fallback_action: step?.if_missing?.automation ? 'automation' : 'procedure',
      fallback_automation: step?.if_missing?.automation || '',
      fallback_procedure: step?.if_missing?.procedure || '',
      final_action: step?.do?.automation ? 'automation' : 
                    step?.do?.procedure ? 'procedure' : 'next',
      final_automation: step?.do?.automation || '',
      final_procedure: step?.do?.procedure || ''
    }
  });

  const fallbackAction = watch('fallback_action');
  const finalAction = watch('final_action');

  const validateStep = (data: StepForm): string[] => {
    const errors: string[] = [];
    
    if (!data.name.trim()) {
      errors.push('Nome do passo é obrigatório');
    }
    
    if (!data.condition.trim()) {
      errors.push('Descreva a condição com uma frase simples. Ex.: "depósito confirmado"');
    }
    
    if (data.fallback_action === 'automation' && !data.fallback_automation) {
      errors.push('Escolha qual mensagem enviar quando esta etapa não estiver satisfeita');
    }
    
    if (data.fallback_action === 'procedure' && !data.fallback_procedure) {
      errors.push('Escolha qual procedimento executar quando esta etapa não estiver satisfeita');
    }
    
    if (data.final_action === 'automation' && !data.final_automation) {
      errors.push('Escolha a mensagem de sucesso para este passo');
    }
    
    if (data.final_action === 'procedure' && !data.final_procedure) {
      errors.push('Escolha qual procedimento executar quando esta etapa estiver satisfeita');
    }
    
    return errors;
  };

  const onSubmit = (data: StepForm) => {
    const validationErrors = validateStep(data);
    
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    const newStep: ProcedureStep = {
      name: data.name,
      condition: data.condition
    };

    // Configurar ação de fallback (if_missing)
    if (data.fallback_action === 'automation' && data.fallback_automation) {
      newStep.if_missing = { automation: data.fallback_automation };
    } else if (data.fallback_action === 'procedure' && data.fallback_procedure) {
      newStep.if_missing = { procedure: data.fallback_procedure };
    }

    // Configurar ação final (do)
    if (data.final_action === 'automation' && data.final_automation) {
      newStep.do = { automation: data.final_automation };
    } else if (data.final_action === 'procedure' && data.final_procedure) {
      newStep.do = { procedure: data.final_procedure };
    }

    onSave(newStep);
  };

  // Mock de procedimentos existentes para autocomplete
  const existingProcedures = [
    'liberar_teste',
    'onboarding_completo',
    'ajuda_deposito',
    'reativacao_lead'
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {step ? 'Editar Passo' : 'Configurar Passo'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Errors */}
        {errors.length > 0 && (
          <div className="m-6 mb-0 bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="font-medium text-red-800 mb-2">Corrija os seguintes problemas:</h3>
            <ul className="text-sm text-red-700 space-y-1">
              {errors.map((error, index) => (
                <li key={index}>• {error}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* Nome do Passo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nome do passo *
            </label>
            <input
              {...register('name', { required: true })}
              type="text"
              className="input-field w-full"
              placeholder="Ex.: Concorda em depositar"
            />
          </div>

          {/* Condição */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Condição para seguir *
            </label>
            <AutocompleteInput
              value={watch('condition')}
              onChange={(value) => setValue('condition', value)}
              placeholder="Ex.: o lead concordou em depositar"
              suggestions={COMMON_CONDITIONS.map(c => ({ value: c, label: c }))}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Frase simples. O sistema interpreta e verifica automaticamente.
            </p>
          </div>

          {/* Se a condição NÃO estiver satisfeita */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-4">Se a condição NÃO estiver satisfeita</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  O que fazer
                </label>
                <select 
                  {...register('fallback_action')}
                  className="input-field w-full"
                >
                  <option value="automation">Enviar automação</option>
                  <option value="procedure">Executar outro procedimento</option>
                </select>
              </div>

              {fallbackAction === 'automation' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Automação *
                  </label>
                  <AutocompleteInput
                    value={watch('fallback_automation')}
                    onChange={(value) => setValue('fallback_automation', value)}
                    placeholder="Escolha uma automação"
                    suggestions={AUTOMATION_IDS.map(id => ({ 
                      value: id, 
                      label: id,
                      description: `Automação: ${id}`
                    }))}
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Escolha a mensagem pronta para este caso.
                  </p>
                </div>
              )}

              {fallbackAction === 'procedure' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Procedimento *
                  </label>
                  <AutocompleteInput
                    value={watch('fallback_procedure')}
                    onChange={(value) => setValue('fallback_procedure', value)}
                    placeholder="Escolha um procedimento"
                    suggestions={existingProcedures.map(id => ({ 
                      value: id, 
                      label: id,
                      description: `Procedimento: ${id}`
                    }))}
                    className="w-full"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Se a condição estiver satisfeita */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-4">Se a condição estiver satisfeita</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ação
                </label>
                <select 
                  {...register('final_action')}
                  className="input-field w-full"
                >
                  <option value="next">Seguir para o próximo passo</option>
                  <option value="automation">Enviar automação</option>
                  <option value="procedure">Executar outro procedimento</option>
                </select>
              </div>

              {finalAction === 'automation' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Automação
                  </label>
                  <AutocompleteInput
                    value={watch('final_automation')}
                    onChange={(value) => setValue('final_automation', value)}
                    placeholder="Escolha uma automação"
                    suggestions={AUTOMATION_IDS.map(id => ({ 
                      value: id, 
                      label: id,
                      description: `Automação: ${id}`
                    }))}
                    className="w-full"
                  />
                </div>
              )}

              {finalAction === 'procedure' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Procedimento
                  </label>
                  <AutocompleteInput
                    value={watch('final_procedure')}
                    onChange={(value) => setValue('final_procedure', value)}
                    placeholder="Escolha um procedimento"
                    suggestions={existingProcedures.map(id => ({ 
                      value: id, 
                      label: id,
                      description: `Procedimento: ${id}`
                    }))}
                    className="w-full"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn-primary"
            >
              {step ? 'Atualizar Passo' : 'Adicionar Passo'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
