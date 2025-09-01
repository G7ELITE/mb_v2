import React, { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { 
  PlusIcon, 
  TrashIcon, 
  PlayIcon,
  CheckIcon,
  ArrowLeftIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import type { Procedure, ProcedureStep } from '../types';

import StepModal from '../components/StepModal';

interface ProcedureForm {
  id: string;
  title: string;
  description?: string;
  max_procedure_time: string;
  procedure_cooldown: string;
  allow_nested_procedures: boolean;
  steps: ProcedureStep[];
}

export default function ProcedureEditor() {
  const navigate = useNavigate();
  const [showStepModal, setShowStepModal] = useState(false);
  const [editingStepIndex, setEditingStepIndex] = useState<number | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  const { register, control, handleSubmit, watch, setValue } = useForm<ProcedureForm>({
    defaultValues: {
      id: '',
      title: '',
      description: '',
      max_procedure_time: '30m',
      procedure_cooldown: 'desativado',
      allow_nested_procedures: true,
      steps: []
    }
  });

  const { fields: steps, append, remove, update } = useFieldArray({
    control,
    name: 'steps'
  });

  const title = watch('title');
  
  // Auto-gerar ID baseado no título
  React.useEffect(() => {
    if (title) {
      const slug = title
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9\s]/g, '')
        .replace(/\s+/g, '_')
        .substring(0, 50);
      setValue('id', slug);
    }
  }, [title, setValue]);

  const validateProcedure = (data: ProcedureForm): string[] => {
    const errors: string[] = [];
    
    if (!data.title.trim()) {
      errors.push('Nome do procedimento é obrigatório');
    }
    
    if (data.steps.length === 0) {
      errors.push('Deve ter pelo menos 1 passo');
    }
    
    data.steps.forEach((step, index) => {
      if (!step.condition.trim()) {
        errors.push(`Passo ${index + 1}: Condição é obrigatória`);
      }
      if (!step.if_missing?.automation && !step.if_missing?.procedure && !step.do) {
        errors.push(`Passo ${index + 1}: Precisa de automação de fallback ou ação final`);
      }
    });
    
    return errors;
  };

  const onSubmit = async (data: ProcedureForm) => {
    const validationErrors = validateProcedure(data);
    
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    try {
      const procedure: Procedure = {
        ...data,
        settings: {
          max_procedure_time: data.max_procedure_time,
          procedure_cooldown: data.procedure_cooldown === 'desativado' ? undefined : data.procedure_cooldown,
          allow_nested_procedures: data.allow_nested_procedures
        }
      };

      // TODO: Salvar via API
      console.log('Salvando procedimento:', procedure);
      
      // Simular sucesso
      alert('Procedimento salvo com sucesso!');
      navigate('/procedures');
      
    } catch (error) {
      setErrors(['Erro ao salvar procedimento. Tente novamente.']);
    }
  };

  const handleAddStep = () => {
    setEditingStepIndex(null);
    setShowStepModal(true);
  };

  const handleEditStep = (index: number) => {
    setEditingStepIndex(index);
    setShowStepModal(true);
  };

  const handleSaveStep = (step: ProcedureStep) => {
    if (editingStepIndex !== null) {
      update(editingStepIndex, step);
    } else {
      append(step);
    }
    setShowStepModal(false);
    setEditingStepIndex(null);
  };

  const handleSimulate = () => {
    const data = watch();
    navigate(`/simulator?procedure_draft=${encodeURIComponent(JSON.stringify(data))}`);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={() => navigate('/procedures')}
            className="btn-secondary mr-4"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Voltar
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Novo Procedimento</h1>
            <p className="mt-2 text-gray-600">
              Configure um funil de passos sequenciais para seus leads
            </p>
          </div>
        </div>
      </div>

      {/* Errors */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <ExclamationCircleIcon className="h-5 w-5 text-red-600 mr-2" />
            <h3 className="font-medium text-red-800">Complete as informações marcadas:</h3>
          </div>
          <ul className="text-sm text-red-700 space-y-1">
            {errors.map((error, index) => (
              <li key={index}>• {error}</li>
            ))}
          </ul>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        {/* Informações Básicas */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Informações Básicas</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nome do procedimento *
              </label>
              <input
                {...register('title', { required: true })}
                type="text"
                className="input-field w-full"
                placeholder="Ex.: Liberar acesso ao teste"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ID (gerado automaticamente)
              </label>
              <input
                {...register('id')}
                type="text"
                className="input-field w-full"
                readOnly
              />
              <p className="text-xs text-gray-500 mt-1">
                ID usado como referência interna. Se mudar, atualize referências.
              </p>
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Descrição (opcional)
              </label>
              <textarea
                {...register('description')}
                rows={2}
                className="input-field w-full"
                placeholder="Para que serve este procedimento?"
              />
            </div>
          </div>
        </div>

        {/* Configurações */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Configurações</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tempo máximo deste fluxo
              </label>
              <select {...register('max_procedure_time')} className="input-field w-full">
                <option value="15m">15 minutos</option>
                <option value="30m">30 minutos</option>
                <option value="1h">1 hora</option>
                <option value="4h">4 horas</option>
                <option value="desativado">Desativado</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Se o lead travar, o fluxo expira. Você pode reativar depois.
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Intervalo antes de reabrir este fluxo
              </label>
              <select {...register('procedure_cooldown')} className="input-field w-full">
                <option value="desativado">Desativado</option>
                <option value="30m">30 minutos</option>
                <option value="1h">1 hora</option>
                <option value="12h">12 horas</option>
                <option value="24h">24 horas</option>
              </select>
            </div>
            
            <div className="flex items-center pt-6">
              <input
                {...register('allow_nested_procedures')}
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 text-sm text-gray-700">
                Permitir chamar outro procedimento dentro deste
              </label>
            </div>
          </div>
        </div>

        {/* Passos */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Passos (ordem do funil)
            </h2>
            <button
              type="button"
              onClick={handleAddStep}
              className="btn-primary"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Adicionar passo
            </button>
          </div>
          
          {steps.length === 0 ? (
            <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
              <p className="text-gray-500">Nenhum passo ainda.</p>
              <button
                type="button"
                onClick={handleAddStep}
                className="btn-secondary mt-2"
              >
                Adicionar primeiro passo
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {steps.map((step, index) => (
                <div key={step.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start flex-1">
                      <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 text-sm font-medium rounded-full mr-3 mt-1">
                        {index + 1}
                      </span>
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{step.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">
                          Condição: {step.condition}
                        </p>
                        {step.if_missing && (
                          <p className="text-xs text-orange-600 mt-1">
                            Se não → {step.if_missing.automation || step.if_missing.procedure}
                          </p>
                        )}
                        {step.do && (
                          <p className="text-xs text-green-600 mt-1">
                            Ação final → {step.do.automation || step.do.procedure}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        type="button"
                        onClick={() => handleEditStep(index)}
                        className="text-blue-600 hover:text-blue-500 p-1"
                      >
                        <PlusIcon className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => remove(index)}
                        className="text-red-600 hover:text-red-500 p-1"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Ações do Rodapé */}
        <div className="flex justify-between items-center pt-6 border-t border-gray-200">
          <button
            type="button"
            onClick={handleSimulate}
            className="btn-secondary flex items-center"
            disabled={steps.length === 0}
          >
            <PlayIcon className="h-4 w-4 mr-2" />
            Simular antes de salvar
          </button>
          
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={() => navigate('/procedures')}
              className="btn-secondary"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn-primary flex items-center"
            >
              <CheckIcon className="h-4 w-4 mr-2" />
              Salvar Rascunho
            </button>
          </div>
        </div>
      </form>

      {/* Modal de Passo */}
      {showStepModal && (
        <StepModal
          step={editingStepIndex !== null ? steps[editingStepIndex] : undefined}
          onSave={handleSaveStep}
          onClose={() => {
            setShowStepModal(false);
            setEditingStepIndex(null);
          }}
        />
      )}
    </div>
  );
}
