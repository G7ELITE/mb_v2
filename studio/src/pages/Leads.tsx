import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  EyeIcon,
  FunnelIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import LeadModal from '../components/LeadModal';
import type { LeadsFilters, LeadDetail } from '../types';

const PAGE_SIZES = [25, 50, 100];
const SORT_OPTIONS = [
  { value: 'created_at', label: 'Data de criação' },
  { value: 'last_activity_at', label: 'Última atividade' },
  { value: 'name', label: 'Nome' },
  { value: 'events_24h', label: 'Eventos 24h' },
];

const CHANNEL_OPTIONS = [
  { value: 'telegram', label: 'Telegram' },
  { value: 'whatsapp', label: 'WhatsApp' },
];

const LANG_OPTIONS = [
  { value: 'pt-BR', label: 'Português (BR)' },
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Español' },
];

const DEPOSIT_STATUS_OPTIONS = [
  { value: 'none', label: 'Nenhum' },
  { value: 'pending', label: 'Pendente' },
  { value: 'confirmed', label: 'Confirmado' },
];

const ACCOUNT_STATUS_OPTIONS = [
  { value: 'com_conta', label: 'Tem conta' },
  { value: 'sem_conta', label: 'Sem conta' },
  { value: 'desconhecido', label: 'Desconhecido' },
];

export default function Leads() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // Estados dos filtros
  const [filters, setFilters] = useState<LeadsFilters>(() => {
    const params = Object.fromEntries(searchParams.entries());
    return {
      q: params.q || '',
      channel: params.channel || '',
      lang: params.lang || '',
      deposit_status: params.deposit_status || '',
      accounts_quotex: params.accounts_quotex || '',
      accounts_nyrion: params.accounts_nyrion || '',
      agreements_can_deposit: params.agreements_can_deposit === 'true' ? true : params.agreements_can_deposit === 'false' ? false : undefined,
      agreements_wants_test: params.agreements_wants_test === 'true' ? true : params.agreements_wants_test === 'false' ? false : undefined,
      inactive_gt_hours: params.inactive_gt_hours ? parseInt(params.inactive_gt_hours) : undefined,
      min_events_24h: params.min_events_24h ? parseInt(params.min_events_24h) : undefined,
      page: parseInt(params.page || '1'),
      page_size: parseInt(params.page_size || '50'),
      sort_by: params.sort_by || 'created_at',
      sort_dir: (params.sort_dir as 'asc' | 'desc') || 'desc',
      mock: params.mock === 'true',
    };
  });

  // Estados da UI
  const [filtersExpanded, setFiltersExpanded] = useState(false);
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Query para buscar leads
  const { data: leadsData, isLoading, error, refetch } = useQuery({
    queryKey: ['leads', filters],
    queryFn: () => apiService.getLeads(filters),
    staleTime: 30000, // 30 segundos
  });

  // Aplicar filtros na URL com debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      const params = new URLSearchParams();
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.set(key, value.toString());
        }
      });
      
      setSearchParams(params);
    }, 300);

    return () => clearTimeout(timer);
  }, [filters, setSearchParams]);

  const updateFilters = (newFilters: Partial<LeadsFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 })); // Reset página ao filtrar
  };

  // const handleSort = (field: string) => {
  //   const newDir = filters.sort_by === field && filters.sort_dir === 'desc' ? 'asc' : 'desc';
  //   setFilters(prev => ({ ...prev, sort_by: field, sort_dir: newDir }));
  // };

  const handleViewLead = (leadId: number) => {
    setSelectedLeadId(leadId);
    setIsModalOpen(true);
  };

  const handleSimulateWithLead = (lead: LeadDetail) => {
    // Navegar para o simulador com dados do lead
    const simulatorData = {
      lead: {
        id: lead.id,
        nome: lead.name,
        lang: lead.lang,
      },
      snapshot: lead.snapshot,
      messages_window: [
        { id: '1', text: 'Mensagem simulada do lead' }
      ],
    };

    navigate('/simulator', { 
      state: { prefilledData: simulatorData } 
    });
    setIsModalOpen(false);
  };

  const resetFilters = () => {
    setFilters({
      page: 1,
      page_size: 50,
      sort_by: 'created_at',
      sort_dir: 'desc',
      mock: false,
    });
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('pt-BR');
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

  const totalPages = leadsData?.total_pages || 0;
  const currentPage = filters.page || 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <UsersIcon className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Leads</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {leadsData?.total || 0} leads encontrados
            </p>
          </div>
        </div>

        <button
          onClick={() => setFiltersExpanded(!filtersExpanded)}
          className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
        >
          <FunnelIcon className="h-4 w-4 mr-2" />
          Filtros
        </button>
      </div>

      {/* Filtros */}
      {filtersExpanded && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-4">
          {/* Linha 1: Busca e datas */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Buscar
              </label>
              <input
                type="text"
                value={filters.q || ''}
                onChange={(e) => updateFilters({ q: e.target.value })}
                placeholder="Nome ou platform_user_id"
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Canal
              </label>
              <select
                value={filters.channel || ''}
                onChange={(e) => updateFilters({ channel: e.target.value || undefined })}
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              >
                <option value="">Todos</option>
                {CHANNEL_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Idioma
              </label>
              <select
                value={filters.lang || ''}
                onChange={(e) => updateFilters({ lang: e.target.value || undefined })}
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              >
                <option value="">Todos</option>
                {LANG_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Linha 2: Status e contas */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Status Depósito
              </label>
              <select
                value={filters.deposit_status || ''}
                onChange={(e) => updateFilters({ deposit_status: e.target.value || undefined })}
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              >
                <option value="">Todos</option>
                {DEPOSIT_STATUS_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Conta Quotex
              </label>
              <select
                value={filters.accounts_quotex || ''}
                onChange={(e) => updateFilters({ accounts_quotex: e.target.value || undefined })}
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              >
                <option value="">Todos</option>
                {ACCOUNT_STATUS_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Conta Nyrion
              </label>
              <select
                value={filters.accounts_nyrion || ''}
                onChange={(e) => updateFilters({ accounts_nyrion: e.target.value || undefined })}
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              >
                <option value="">Todos</option>
                {ACCOUNT_STATUS_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Linha 3: Acordos e números */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Pode Depositar
              </label>
              <select
                value={filters.agreements_can_deposit === undefined ? '' : filters.agreements_can_deposit.toString()}
                onChange={(e) => {
                  const value = e.target.value === '' ? undefined : e.target.value === 'true';
                  updateFilters({ agreements_can_deposit: value });
                }}
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              >
                <option value="">Todos</option>
                <option value="true">Sim</option>
                <option value="false">Não</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Quer Testar
              </label>
              <select
                value={filters.agreements_wants_test === undefined ? '' : filters.agreements_wants_test.toString()}
                onChange={(e) => {
                  const value = e.target.value === '' ? undefined : e.target.value === 'true';
                  updateFilters({ agreements_wants_test: value });
                }}
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              >
                <option value="">Todos</option>
                <option value="true">Sim</option>
                <option value="false">Não</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Inativo há (horas)
              </label>
              <input
                type="number"
                value={filters.inactive_gt_hours || ''}
                onChange={(e) => updateFilters({ inactive_gt_hours: e.target.value ? parseInt(e.target.value) : undefined })}
                placeholder="Ex: 24"
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Min. eventos 24h
              </label>
              <input
                type="number"
                value={filters.min_events_24h || ''}
                onChange={(e) => updateFilters({ min_events_24h: e.target.value ? parseInt(e.target.value) : undefined })}
                placeholder="Ex: 5"
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              />
            </div>
          </div>

          {/* Ações */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.mock || false}
                  onChange={(e) => updateFilters({ mock: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Dados mock</span>
              </label>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={resetFilters}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                Reset
              </button>
              <button
                onClick={() => refetch()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
              >
                Aplicar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tabela */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600 dark:text-gray-300">Carregando leads...</span>
          </div>
        )}

        {error && (
          <div className="p-6">
            <div className="bg-red-50 dark:bg-red-900/50 border border-red-200 dark:border-red-800 rounded-md p-4">
              <p className="text-red-600 dark:text-red-400">Erro ao carregar leads</p>
            </div>
          </div>
        )}

        {leadsData && !isLoading && (
          <>
            {/* Header da tabela */}
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {leadsData.total} leads • Página {currentPage} de {totalPages}
                  </span>
                </div>

                <div className="flex items-center space-x-4">
                  <select
                    value={filters.page_size}
                    onChange={(e) => setFilters(prev => ({ ...prev, page_size: parseInt(e.target.value), page: 1 }))}
                    className="rounded-md border-gray-300 dark:border-gray-600 text-sm dark:bg-gray-700 dark:text-white"
                  >
                    {PAGE_SIZES.map(size => (
                      <option key={size} value={size}>{size} por página</option>
                    ))}
                  </select>

                  <select
                    value={filters.sort_by}
                    onChange={(e) => setFilters(prev => ({ ...prev, sort_by: e.target.value }))}
                    className="rounded-md border-gray-300 dark:border-gray-600 text-sm dark:bg-gray-700 dark:text-white"
                  >
                    {SORT_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>

                  <button
                    onClick={() => setFilters(prev => ({ ...prev, sort_dir: prev.sort_dir === 'asc' ? 'desc' : 'asc' }))}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    {filters.sort_dir === 'asc' ? <ArrowUpIcon className="h-4 w-4" /> : <ArrowDownIcon className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Conteúdo da tabela */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Lead
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Canal
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Criado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Contas
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Depósito
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Acordos
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Eventos 24h
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {leadsData.items.map((lead) => (
                    <tr key={lead.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {lead.name || `Lead #${lead.id}`}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {lead.platform_user_id}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                          {lead.channel}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {formatDate(lead.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(lead.accounts).map(([broker, status]) => (
                            <span
                              key={broker}
                              className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${getStatusBadge(status)}`}
                            >
                              {broker.charAt(0).toUpperCase()}: {status.charAt(0).toUpperCase()}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(lead.deposit.status || 'none')}`}>
                          {lead.deposit.status || 'none'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(lead.agreements).map(([key, value]) => (
                            <span
                              key={key}
                              className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                                value ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                              }`}
                            >
                              {key.split('_').pop()}: {value ? '✓' : '✗'}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          lead.events_24h > 5 ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                          lead.events_24h > 0 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
                          'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                        }`}>
                          {lead.events_24h}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleViewLead(lead.id)}
                          className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                          aria-label={`Ver lead ${lead.id}`}
                        >
                          <EyeIcon className="h-4 w-4 mr-1" />
                          Ver
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Paginação */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    Mostrando {((currentPage - 1) * (filters.page_size || 50)) + 1} a {Math.min(currentPage * (filters.page_size || 50), leadsData.total)} de {leadsData.total} resultados
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setFilters(prev => ({ ...prev, page: Math.max(1, currentPage - 1) }))}
                      disabled={currentPage <= 1}
                      className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronLeftIcon className="h-5 w-5" />
                    </button>
                    
                    <span className="px-3 py-1 text-sm text-gray-700 dark:text-gray-300">
                      {currentPage} / {totalPages}
                    </span>
                    
                    <button
                      onClick={() => setFilters(prev => ({ ...prev, page: Math.min(totalPages, currentPage + 1) }))}
                      disabled={currentPage >= totalPages}
                      className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronRightIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Modal de detalhes do lead */}
      <LeadModal
        leadId={selectedLeadId}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedLeadId(null);
        }}
        onSimulate={handleSimulateWithLead}
      />
    </div>
  );
}
