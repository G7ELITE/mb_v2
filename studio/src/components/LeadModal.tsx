import { Fragment, useEffect, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, EyeIcon, ClockIcon, TagIcon, TrashIcon, ClockIcon as ClearIcon } from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import type { LeadDetail } from '../types';

interface LeadModalProps {
  leadId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onSimulate?: (lead: LeadDetail) => void;
}

export default function LeadModal({ leadId, isOpen, onClose, onSimulate }: LeadModalProps) {
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && leadId) {
      loadLeadDetail();
    }
  }, [isOpen, leadId]);

  const loadLeadDetail = async () => {
    if (!leadId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await apiService.getLeadDetail(leadId);
      setLead(data);
    } catch (err) {
      console.error('Erro ao carregar detalhes do lead:', err);
      setError('Erro ao carregar detalhes do lead');
    } finally {
      setLoading(false);
    }
  };

  const handleExportJson = () => {
    if (!lead) return;
    
    const dataStr = JSON.stringify(lead, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `lead-${lead.id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleClearSession = async () => {
    if (!lead || !confirm('Tem certeza que deseja limpar a sessão deste lead? Isso resetará o contexto, procedimento e aguardando.')) return;
    
    setActionLoading('clear_session');
    try {
      await apiService.clearLeadSession(lead.id);
      alert('Sessão limpa com sucesso!');
      // Recarregar dados do lead
      await loadLeadDetail();
    } catch (error) {
      console.error('Erro ao limpar sessão:', error);
      alert('Erro ao limpar sessão. Veja o console para mais detalhes.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteLead = async () => {
    if (!lead || !confirm(`Tem certeza que deseja DELETAR PERMANENTEMENTE o lead "${lead.name}"? Esta ação não pode ser desfeita.`)) return;
    
    setActionLoading('delete_lead');
    try {
      await apiService.deleteLead(lead.id);
      alert('Lead deletado com sucesso!');
      onClose(); // Fechar modal
      // Refresh da lista será feito automaticamente pelo react-query
    } catch (error) {
      console.error('Erro ao deletar lead:', error);
      alert('Erro ao deletar lead. Veja o console para mais detalhes.');
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString('pt-BR');
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      none: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
      pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
      confirmed: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
      com_conta: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
      sem_conta: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
      desconhecido: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    };
    
    return styles[status as keyof typeof styles] || styles.desconhecido;
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25 dark:bg-opacity-50" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 p-6 text-left align-middle shadow-xl transition-all">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <Dialog.Title className="text-xl font-semibold text-gray-900 dark:text-white">
                      {lead?.name || `Lead #${leadId}`}
                    </Dialog.Title>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      ID: {leadId} • {lead?.channel} • {lead?.platform_user_id}
                    </p>
                  </div>
                  <button
                    onClick={onClose}
                    className="rounded-md p-2 text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>

                {loading && (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-2 text-gray-600 dark:text-gray-300">Carregando...</span>
                  </div>
                )}

                {error && (
                  <div className="bg-red-50 dark:bg-red-900/50 border border-red-200 dark:border-red-800 rounded-md p-4 mb-6">
                    <p className="text-red-600 dark:text-red-400">{error}</p>
                  </div>
                )}

                {lead && !loading && (
                  <div className="space-y-6">
                    {/* Informações Básicas */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Informações Básicas</h3>
                        <dl className="space-y-2">
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500 dark:text-gray-400">Nome:</dt>
                            <dd className="text-sm text-gray-900 dark:text-white">{lead.name || 'N/A'}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500 dark:text-gray-400">Canal:</dt>
                            <dd className="text-sm text-gray-900 dark:text-white">{lead.channel}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500 dark:text-gray-400">Idioma:</dt>
                            <dd className="text-sm text-gray-900 dark:text-white">{lead.lang}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500 dark:text-gray-400">Criado em:</dt>
                            <dd className="text-sm text-gray-900 dark:text-white">{formatDate(lead.created_at)}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500 dark:text-gray-400">Última atividade:</dt>
                            <dd className="text-sm text-gray-900 dark:text-white">{formatDate(lead.last_activity_at)}</dd>
                          </div>
                        </dl>
                      </div>

                      <div className="space-y-4">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Procedimento</h3>
                        <dl className="space-y-2">
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500 dark:text-gray-400">Ativo:</dt>
                            <dd className="text-sm text-gray-900 dark:text-white">{lead.procedure.active || 'Nenhum'}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500 dark:text-gray-400">Passo:</dt>
                            <dd className="text-sm text-gray-900 dark:text-white">{lead.procedure.step || 'N/A'}</dd>
                          </div>
                          {lead.procedure.waiting && (
                            <div className="flex justify-between">
                              <dt className="text-sm text-gray-500 dark:text-gray-400">Aguardando:</dt>
                              <dd className="text-sm text-yellow-600 dark:text-yellow-400">
                                {lead.procedure.waiting.tipo || 'Confirmação'}
                              </dd>
                            </div>
                          )}
                        </dl>
                      </div>
                    </div>

                    {/* Snapshot */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">Snapshot</h3>
                      
                      {/* Contas */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Contas</h4>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(lead.snapshot.accounts).map(([broker, status]) => (
                            <span
                              key={broker}
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(status)}`}
                            >
                              {broker}: {status}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Depósito */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Depósito</h4>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(lead.snapshot.deposit.status || 'none')}`}>
                          {lead.snapshot.deposit.status || 'none'}
                        </span>
                      </div>

                      {/* Acordos */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Acordos</h4>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(lead.snapshot.agreements).map(([key, value]) => (
                            <span
                              key={key}
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                value ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                              }`}
                            >
                              {key}: {value ? 'Sim' : 'Não'}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Tags */}
                      {lead.snapshot.tags && lead.snapshot.tags.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Tags</h4>
                          <div className="flex flex-wrap gap-2">
                            {lead.snapshot.tags.map((tag, index) => (
                              <span
                                key={index}
                                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
                              >
                                <TagIcon className="h-3 w-3 mr-1" />
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Eventos Recentes */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">Últimos Eventos</h3>
                      {lead.events_recent.length > 0 ? (
                        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 max-h-64 overflow-y-auto">
                          <div className="space-y-3">
                            {lead.events_recent.map((event) => (
                              <div key={event.id} className="flex items-start space-x-3">
                                <ClockIcon className="h-4 w-4 text-gray-400 mt-0.5" />
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                                    {event.event_type}
                                  </p>
                                  <p className="text-xs text-gray-500 dark:text-gray-400">
                                    {formatDate(event.created_at)}
                                  </p>
                                  {event.payload && Object.keys(event.payload).length > 0 && (
                                    <pre className="text-xs text-gray-600 dark:text-gray-300 mt-1 bg-white dark:bg-gray-800 p-2 rounded">
                                      {JSON.stringify(event.payload, null, 2)}
                                    </pre>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500 dark:text-gray-400">Nenhum evento recente</p>
                      )}
                    </div>

                    {/* Seção de Informações Adicionais */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">Informações Técnicas</h3>
                      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                          <div>
                            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">ID do Lead:</dt>
                            <dd className="text-sm text-gray-900 dark:text-white font-mono">{lead.id}</dd>
                          </div>
                          <div>
                            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Platform User ID:</dt>
                            <dd className="text-sm text-gray-900 dark:text-white font-mono">{lead.platform_user_id}</dd>
                          </div>
                          {lead.procedure.waiting && (
                            <>
                              <div>
                                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Aguardando Tipo:</dt>
                                <dd className="text-sm text-yellow-600 dark:text-yellow-400">{lead.procedure.waiting.tipo}</dd>
                              </div>
                              <div>
                                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Aguardando TTL:</dt>
                                <dd className="text-sm text-yellow-600 dark:text-yellow-400">
                                  {lead.procedure.waiting.ttl ? new Date(lead.procedure.waiting.ttl * 1000).toLocaleString('pt-BR') : 'N/A'}
                                </dd>
                              </div>
                            </>
                          )}
                          <div>
                            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Eventos 24h:</dt>
                            <dd className="text-sm text-gray-900 dark:text-white">{lead.events_24h || 0}</dd>
                          </div>
                          <div>
                            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Canal:</dt>
                            <dd className="text-sm text-gray-900 dark:text-white">{lead.channel}</dd>
                          </div>
                        </dl>
                      </div>
                      
                      {/* Snapshot Completo */}
                      <details className="bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <summary className="p-4 cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg">
                          Ver Snapshot Completo (JSON)
                        </summary>
                        <div className="px-4 pb-4">
                          <pre className="text-xs text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-800 p-3 rounded border overflow-x-auto">
                            {JSON.stringify(lead.snapshot, null, 2)}
                          </pre>
                        </div>
                      </details>
                    </div>

                    {/* Footer Actions */}
                    <div className="flex items-center justify-between pt-6 border-t border-gray-200 dark:border-gray-700">
                      <div className="flex space-x-3">
                        {onSimulate && (
                          <button
                            onClick={() => onSimulate(lead)}
                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                          >
                            <EyeIcon className="h-4 w-4 mr-2" />
                            Simular com este lead
                          </button>
                        )}
                        <button
                          onClick={handleExportJson}
                          className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                          Exportar JSON
                        </button>
                        <button
                          onClick={handleClearSession}
                          disabled={actionLoading === 'clear_session'}
                          className="inline-flex items-center px-4 py-2 border border-yellow-300 dark:border-yellow-600 text-sm font-medium rounded-md text-yellow-700 dark:text-yellow-300 bg-yellow-50 dark:bg-yellow-900 hover:bg-yellow-100 dark:hover:bg-yellow-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50"
                        >
                          <ClearIcon className="h-4 w-4 mr-2" />
                          {actionLoading === 'clear_session' ? 'Limpando...' : 'Limpar Sessão'}
                        </button>
                        <button
                          onClick={handleDeleteLead}
                          disabled={actionLoading === 'delete_lead'}
                          className="inline-flex items-center px-4 py-2 border border-red-300 dark:border-red-600 text-sm font-medium rounded-md text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900 hover:bg-red-100 dark:hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                        >
                          <TrashIcon className="h-4 w-4 mr-2" />
                          {actionLoading === 'delete_lead' ? 'Deletando...' : 'Deletar Lead'}
                        </button>
                      </div>
                      <button
                        onClick={onClose}
                        className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                      >
                        Fechar
                      </button>
                    </div>
                  </div>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
