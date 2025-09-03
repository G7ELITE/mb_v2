import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  PlusIcon, 
  PencilIcon, 
  PlayIcon,
  TrashIcon,
  ClockIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon

} from '@heroicons/react/24/outline';
import CollapsibleSection from '../components/CollapsibleSection';
import type { Procedure } from '../types';
import { procedureStorage } from '../services/procedureStorage';

export default function Procedures() {
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    published: 0,
    drafts: 0,
    avgSteps: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load procedures on mount
  useEffect(() => {
    loadProcedures();
  }, []);

  const loadProcedures = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const loadedProcedures = await procedureStorage.getAll();
      const loadedStats = await procedureStorage.getStats();
      
      setProcedures(loadedProcedures);
      setStats(loadedStats);
    } catch (error) {
      console.error('Error loading procedures:', error);
      setError('Failed to load procedures');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm(`Tem certeza que deseja excluir o procedimento "${id}"?`)) {
      try {
        await procedureStorage.delete(id);
        await loadProcedures(); // Reload list
      } catch (error) {
        console.error('Error deleting procedure:', error);
        alert('Erro ao excluir procedimento');
      }
    }
  };

  const handleReset = async () => {
    if (confirm('⚠️ Tem certeza que deseja resetar TODOS os procedimentos?\n\nEsta ação irá:\n• Fazer backup dos procedimentos atuais\n• Limpar o catálogo completamente\n\nEsta ação não pode ser desfeita!')) {
      try {
        setLoading(true);
        await procedureStorage.reset();
        await loadProcedures();
        alert('✅ Catálogo resetado com sucesso! Backup criado automaticamente.');
      } catch (error) {
        console.error('Error resetting catalog:', error);
        alert('Erro ao resetar catálogo');
      } finally {
        setLoading(false);
      }
    }
  };

  const getStepStatusIcon = (step: any) => {
    if (step.do) {
      return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
    }
    return <ClockIcon className="h-4 w-4 text-gray-400" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600 dark:text-gray-300">Carregando procedimentos...</span>
      </div>
    );
  }

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
        <div className="flex space-x-3">
          <button
            onClick={handleReset}
            className="btn-secondary flex items-center text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
            disabled={loading}
          >
            <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
            Resetar Catálogo
          </button>
          <Link 
            to="/procedures/new"
            className="btn-primary flex items-center"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Criar Procedimento
          </Link>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-2" />
            <p className="text-red-800">{error}</p>
            <button
              onClick={loadProcedures}
              className="ml-auto text-red-600 hover:text-red-700 underline"
            >
              Tentar novamente
            </button>
          </div>
        </div>
      )}

      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="stats-card">
          <div className="stats-number">{stats.total}</div>
          <div className="stats-label">Total</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">{stats.published}</div>
          <div className="stats-label">Publicados</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">{stats.drafts}</div>
          <div className="stats-label">Rascunhos</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">{stats.avgSteps.toFixed(1)}</div>
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
            actions={[
              {
                label: 'Testar',
                onClick: () => window.location.href = `/simulator?procedure=${procedure.id}`,
                icon: PlayIcon,
                variant: 'primary'
              },
              {
                label: 'Editar',
                onClick: () => window.location.href = `/procedures/${procedure.id}/edit`,
                icon: PencilIcon,
                variant: 'secondary'
              },
              {
                label: 'Excluir',
                onClick: () => handleDelete(procedure.id),
                icon: TrashIcon,
                variant: 'danger'
              }
            ]}
            previewContent={
              <div className="space-y-2">
                <div className="flex items-center gap-4">
                  <span className="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 px-2 py-1 rounded">
                    {procedure.steps.length} passos
                  </span>
                  {procedure.settings?.max_procedure_time && (
                    <span className="text-xs bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 px-2 py-1 rounded">
                      Máx: {procedure.settings.max_procedure_time}
                    </span>
                  )}
                  {procedure.settings?.procedure_cooldown && (
                    <span className="text-xs bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 px-2 py-1 rounded">
                      Cooldown: {procedure.settings.procedure_cooldown}
                    </span>
                  )}
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2" />
                  <span className="text-gray-600 dark:text-gray-300">Status: Ativo • Atualizado há 2 dias</span>
                </div>
              </div>
            }
          >

            {/* Configurações */}
            {procedure.settings && (
              <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="text-xs font-medium text-gray-600 dark:text-gray-300 mb-2">Configurações:</div>
                <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-300">
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
              <h4 className="font-medium text-gray-900 dark:text-gray-100">
                Passos ({procedure.steps.length})
              </h4>
              <div className="space-y-2">
                {procedure.steps.map((step, index) => (
                  <div 
                    key={index}
                    className="flex items-start p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div className="flex items-center mr-3">
                      <span className="flex items-center justify-center w-6 h-6 bg-blue-900 dark:bg-gray-800/60 text-gray-600 dark:text-blue-300 text-xs font-medium rounded-full">
                        {index + 1}
                      </span>
                      <div className="ml-2">
                        {getStepStatusIcon(step)}
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 dark:text-gray-100">
                        {step.name}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                        Condição: {step.condition}
                      </div>
                      {step.if_missing && (
                        <div className="text-xs text-red-700 dark:text-red-700 mt-1">
                          Se não → {step.if_missing.automation || step.if_missing.procedure}
                        </div>
                      )}
                      {step.do && (
                        <div className="text-xs text-green-600 dark:text-green-300 mt-1">
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
      {!loading && !error && procedures.length === 0 && (
        <div className="text-center py-12 card">
          <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
            <DocumentTextIcon className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Catálogo de procedimentos vazio
          </h3>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            O catálogo de procedimentos está vazio. Crie procedimentos para automatizar funis de leads.
          </p>
          <div className="space-y-4">
            <Link to="/procedures/new" className="btn-primary inline-block">
              Criar Primeiro Procedimento
            </Link>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              <p>💡 Dica: Você pode começar criando um procedimento de onboarding</p>
              <p>ou um funil de liberação de teste.</p>
            </div>
          </div>
        </div>
      )}

      {/* Dicas */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-medium text-blue-900 mb-2">💡 Dicas</h3>
        <ul className="text-sm text-white-800 space-y-1">
          <li>• Procedimentos executam passos em ordem até encontrar um não satisfeito</li>
          <li>• Use o simulador para testar diferentes cenários antes de publicar</li>
          <li>• Mantenha condições simples e em português natural</li>
          <li>• Configure timeouts adequados para evitar leads presos</li>
        </ul>
      </div>
    </div>
  );
}
