import { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  PlusIcon, 
  PencilIcon, 
  PlayIcon,
  TrashIcon,
  ClockIcon,
  CheckCircleIcon,
  DocumentTextIcon,

} from '@heroicons/react/24/outline';
import CollapsibleSection from '../components/CollapsibleSection';
import type { Procedure } from '../types';

// Mock data para demonstração
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
    ],
    settings: {
      max_procedure_time: '30m',
      procedure_cooldown: '1h'
    }
  },
  {
    id: 'onboarding_completo',
    title: 'Onboarding completo',
    description: 'Procedimento de onboarding completo para novos leads',
    steps: [
      {
        name: 'Explicar robô',
        condition: 'robô foi explicado para o lead',
        if_missing: { automation: 'explain_robot' }
      },
      {
        name: 'Definir corretora',
        condition: 'lead tem corretora definida',
        if_missing: { automation: 'ask_broker_preference' }
      }
    ]
  }
];

export default function Procedures() {
  const [procedures] = useState<Procedure[]>(mockProcedures);

  const getStepStatusIcon = (step: any) => {
    if (step.do) {
      return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
    }
    return <ClockIcon className="h-4 w-4 text-yellow-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Procedimentos</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-300">
            Gerencie funis de procedimentos com passos sequenciais
          </p>
        </div>
        <Link 
          to="/procedures/new"
          className="btn-primary flex items-center"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Criar Procedimento
        </Link>
      </div>

      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="stats-card">
          <div className="stats-number">2</div>
          <div className="stats-label">Total</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">1</div>
          <div className="stats-label">Publicado</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">1</div>
          <div className="stats-label">Rascunho</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">4.2</div>
          <div className="stats-label">Passos médios</div>
        </div>
      </div>

      {/* Lista de Procedimentos */}
      <div className="space-y-4">
        {procedures.map((procedure) => (
          <CollapsibleSection
            key={procedure.id}
            title={procedure.title}
            description={`ID: ${procedure.id} • ${procedure.description}`}
            icon={DocumentTextIcon}
            defaultExpanded={false}
          >
            <div className="flex justify-end mb-6 space-x-2">
              <Link
                to={`/simulator?procedure=${procedure.id}`}
                className="btn-secondary flex items-center"
              >
                <PlayIcon className="h-4 w-4 mr-1" />
                Testar
              </Link>
              <Link
                to={`/procedures/${procedure.id}/edit`}
                className="btn-secondary flex items-center"
              >
                <PencilIcon className="h-4 w-4 mr-1" />
                Editar
              </Link>
              <button className="text-red-600 hover:text-red-500 p-2">
                <TrashIcon className="h-4 w-4" />
              </button>
            </div>

            {/* Configurações */}
            {procedure.settings && (
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <div className="text-xs font-medium text-gray-600 mb-2">Configurações:</div>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  {procedure.settings.max_procedure_time && (
                    <span>Tempo máximo: {procedure.settings.max_procedure_time}</span>
                  )}
                  {procedure.settings.procedure_cooldown && (
                    <span>Cooldown: {procedure.settings.procedure_cooldown}</span>
                  )}
                </div>
              </div>
            )}

            {/* Passos */}
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">
                Passos ({procedure.steps.length})
              </h4>
              <div className="space-y-2">
                {procedure.steps.map((step, index) => (
                  <div 
                    key={index}
                    className="flex items-start p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center mr-3">
                      <span className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-xs font-medium rounded-full">
                        {index + 1}
                      </span>
                      <div className="ml-2">
                        {getStepStatusIcon(step)}
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
                        {step.name}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        Condição: {step.condition}
                      </div>
                      {step.if_missing && (
                        <div className="text-xs text-orange-600 mt-1">
                          Se não satisfeito → {step.if_missing.automation || step.if_missing.procedure}
                        </div>
                      )}
                      {step.do && (
                        <div className="text-xs text-green-600 mt-1">
                          Ação final → {step.do.automation || step.do.procedure}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Status Summary */}
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center text-gray-600 dark:text-gray-300">
                  <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                  Status: Ativo
                </div>
                <div className="text-gray-500 dark:text-gray-400">
                  Última atualização: há 2 dias
                </div>
              </div>
            </div>
          </CollapsibleSection>
        ))}
      </div>

      {/* Empty State */}
      {procedures.length === 0 && (
        <div className="text-center py-12 card">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <PlusIcon className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Nenhum procedimento criado
          </h3>
          <p className="text-gray-600 mb-6">
            Crie seu primeiro procedimento para automatizar funis de leads
          </p>
          <Link to="/procedures/new" className="btn-primary">
            Criar Primeiro Procedimento
          </Link>
        </div>
      )}

      {/* Dicas */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-medium text-blue-900 mb-2">💡 Dicas</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Procedimentos executam passos em ordem até encontrar um não satisfeito</li>
          <li>• Use o simulador para testar diferentes cenários antes de publicar</li>
          <li>• Mantenha condições simples e em português natural</li>
          <li>• Configure timeouts adequados para evitar leads presos</li>
        </ul>
      </div>
    </div>
  );
}
