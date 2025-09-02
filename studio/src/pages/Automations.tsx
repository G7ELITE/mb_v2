import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  PlusIcon, 
  PencilIcon, 
  PlayIcon,
  TrashIcon,
  ClockIcon,
  BoltIcon,
  CogIcon
} from '@heroicons/react/24/outline';
import CollapsibleSection from '../components/CollapsibleSection';
import type { Automation } from '../types';
import { automationStorage } from '../services/automationStorage';

export default function Automations() {
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    highPriority: 0,
    avgCooldown: '0h',
    topics: 0
  });

  // Carregar automações
  useEffect(() => {
    loadAutomations();
  }, []);

  const loadAutomations = () => {
    try {
      const loadedAutomations = automationStorage.getAll();
      const loadedStats = automationStorage.getStats();
      setAutomations(loadedAutomations);
      setStats(loadedStats);
    } catch (error) {
      console.error('Erro ao carregar automações:', error);
    }
  };

  const handleDelete = (id: string) => {
    if (confirm(`Tem certeza que deseja excluir a automação "${id}"?`)) {
      try {
        automationStorage.delete(id);
        loadAutomations(); // Recarregar lista
      } catch (error) {
        console.error('Erro ao excluir automação:', error);
        alert('Erro ao excluir automação');
      }
    }
  };

  const getPriorityLabel = (priority: number) => {
    if (priority >= 0.9) return 'Alta';
    if (priority >= 0.7) return 'Média';
    return 'Baixa';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Automações</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-300">
            Gerencie mensagens automáticas do catálogo
          </p>
        </div>
        <Link 
          to="/automations/new"
          className="btn-primary flex items-center"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Criar Automação
        </Link>
      </div>

      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="stats-card">
          <div className="stats-number">{stats.total}</div>
          <div className="stats-label">Total de automações</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">{stats.highPriority}</div>
          <div className="stats-label">Alta prioridade</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">{stats.avgCooldown}</div>
          <div className="stats-label">Cooldown médio</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">{stats.topics}</div>
          <div className="stats-label">Tópicos únicos</div>
        </div>
      </div>

      {/* Filtros Rápidos */}
      <div className="flex flex-wrap gap-2">
        <button className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
          Todas ({automations.length})
        </button>
        <button className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600">
          Alta prioridade ({stats.highPriority})
        </button>
        {[...new Set(automations.map(a => a.topic))].map(topic => (
          <button 
            key={topic}
            className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
          >
            {topic} ({automations.filter(a => a.topic === topic).length})
          </button>
        ))}
      </div>

      {/* Lista de Automações */}
      <div className="space-y-4">
        {automations.map((automation) => (
          <CollapsibleSection
            key={automation.id}
            title={automation.id}
            description={`Tópico: ${automation.topic} • ${automation.eligibility}`}
            icon={CogIcon}
            defaultExpanded={false}
            actions={[
              {
                label: 'Testar',
                onClick: () => window.location.href = `/simulator?automation=${automation.id}`,
                icon: PlayIcon,
                variant: 'primary'
              },
              {
                label: 'Editar',
                onClick: () => window.location.href = `/automations/${automation.id}/edit`,
                icon: PencilIcon,
                variant: 'secondary'
              },
              {
                label: 'Excluir',
                onClick: () => handleDelete(automation.id),
                icon: TrashIcon,
                variant: 'danger'
              }
            ]}
            previewContent={
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 px-2 py-1 rounded">
                    {getPriorityLabel(automation.priority)}
                  </span>
                  <span className="text-xs bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 px-2 py-1 rounded">
                    {automation.cooldown}
                  </span>
                  <span className="text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 px-2 py-1 rounded">
                    Ativa
                  </span>
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
                  <span className="font-medium">Preview:</span> {automation.output.text.slice(0, 100)}...
                </div>
                {automation.expects_reply && (
                  <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                    🎯 Espera confirmação: {automation.expects_reply.target}
                  </div>
                )}
                {automation.output.buttons && automation.output.buttons.length > 0 && (
                  <div className="flex gap-1">
                    {automation.output.buttons.slice(0, 2).map((button, index) => (
                      <span
                        key={index}
                        className="text-xs bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 px-2 py-1 rounded"
                      >
                        {button.label}
                      </span>
                    ))}
                    {automation.output.buttons.length > 2 && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        +{automation.output.buttons.length - 2} mais
                      </span>
                    )}
                  </div>
                )}
              </div>
            }
          >
                
            {/* Preview da mensagem */}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 mb-4">
              <div className="text-sm text-gray-700 dark:text-gray-200 whitespace-pre-wrap">
                {automation.output.text}
              </div>
              {automation.output.buttons && automation.output.buttons.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {automation.output.buttons.map((button, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                    >
                      {button.label}
                      {button.kind === 'url' && ' 🔗'}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Configurações */}
            <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-300 mb-4">
              <div className="flex items-center">
                <BoltIcon className="h-4 w-4 mr-1" />
                <span className="text-gray-700 dark:text-gray-200">
                  Prioridade: {getPriorityLabel(automation.priority)} ({automation.priority})
                </span>
              </div>
              <div className="flex items-center">
                <ClockIcon className="h-4 w-4 mr-1" />
                Cooldown: {automation.cooldown}
              </div>
            </div>

            {/* Status */}
            <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center text-green-600 dark:text-green-400">
                  <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                  Ativa
                </div>
                <div className="text-gray-500 dark:text-gray-400">
                  Última execução: há 30 min
                </div>
              </div>
            </div>
          </CollapsibleSection>
        ))}
      </div>

      {/* Empty State */}
      {automations.length === 0 && (
        <div className="text-center py-12 card">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <BoltIcon className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Nenhuma automação criada
          </h3>
          <p className="text-gray-600 mb-6">
            Crie automações para responder automaticamente aos leads
          </p>
          <Link to="/automations/new" className="btn-primary">
            Criar Primeira Automação
          </Link>
        </div>
      )}



      {/* Dicas */}
      <div className="card bg-green-50 border-green-200">
        <h3 className="font-medium text-green-900 mb-2">💡 Dicas para automações</h3>
        <ul className="text-sm text-white-400 space-y-1">
          <li>• Use prioridades para controlar qual mensagem aparece primeiro</li>
          <li>• Configure cooldowns para evitar spam</li>
          <li>• Teste sempre no simulador antes de publicar</li>
          <li>• Botões com set_facts atualizam o estado do lead automaticamente</li>
        </ul>
      </div>
    </div>
  );
}
