import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import {
  MagnifyingGlassIcon,
  CalendarDaysIcon,
  PencilIcon,
  TrashIcon,
  CheckIcon,
  XMarkIcon,
  DocumentArrowDownIcon,
  Square3Stack3DIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { useToast } from '../hooks/useToast';

interface EquipeConsulta {
  id: number;
  pergunta_funcionario: string;
  resposta_gerada: string;
  parametros_rag: any;
  fontes_kb: any;
  funcionario_id: string | null;
  sessao_id: string | null;
  criado_em: string;
}

interface FiltersForm {
  search: string;
  date_from: string;
  date_to: string;
}

interface EditingConsulta {
  id: number;
  pergunta: string;
  resposta: string;
}

export default function EquipeConsultas() {
  const toast = useToast();

  // Estados principais
  const [consultas, setConsultas] = useState<EquipeConsulta[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  // Estados de seleção e edição
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [editingConsulta, setEditingConsulta] = useState<EditingConsulta | null>(null);
  const [editingLoading, setEditingLoading] = useState(false);

  // Estados de ação em lote
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Form para filtros
  const { register, handleSubmit, watch, reset } = useForm<FiltersForm>({
    defaultValues: {
      search: '',
      date_from: '',
      date_to: ''
    }
  });

  const watchFilters = watch();

  // Carregar consultas inicial
  useEffect(() => {
    loadConsultas();
  }, []);

  // Carregar consultas quando filtros mudam
  useEffect(() => {
    const delayedLoad = setTimeout(() => {
      if (watchFilters.search || watchFilters.date_from || watchFilters.date_to) {
        loadConsultas(watchFilters);
      }
    }, 500); // Debounce de 500ms

    return () => clearTimeout(delayedLoad);
  }, [watchFilters.search, watchFilters.date_from, watchFilters.date_to]);

  const loadConsultas = async (filters: FiltersForm = { search: '', date_from: '', date_to: '' }) => {
    try {
      setLoading(true);
      setError('');

      const params: any = {
        limit: 100
      };

      if (filters.search && filters.search.trim()) {
        params.search = filters.search.trim();
      }

      if (filters.date_from) {
        params.date_from = filters.date_from;
      }

      if (filters.date_to) {
        params.date_to = filters.date_to;
      }

      const data = await apiService.getEquipeConsultas(params);
      setConsultas(data);

    } catch (error: any) {
      console.error('Erro ao carregar consultas:', error);
      const errorMessage = error?.response?.data?.detail || 'Erro interno';
      setError(errorMessage);
      toast.error(`Erro ao carregar consultas: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const onFiltersSubmit = (data: FiltersForm) => {
    loadConsultas(data);
  };

  const clearFilters = () => {
    reset();
    loadConsultas();
  };

  const toggleSelection = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) 
        ? prev.filter(selectedId => selectedId !== id)
        : [...prev, id]
    );
  };

  const selectAll = () => {
    if (selectedIds.length === consultas.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(consultas.map(c => c.id));
    }
  };

  const startEditing = (consulta: EquipeConsulta) => {
    setEditingConsulta({
      id: consulta.id,
      pergunta: consulta.pergunta_funcionario,
      resposta: consulta.resposta_gerada
    });
  };

  const cancelEditing = () => {
    setEditingConsulta(null);
  };

  const saveEditing = async () => {
    if (!editingConsulta) return;

    try {
      setEditingLoading(true);

      await apiService.updateEquipeConsulta(
        editingConsulta.id,
        editingConsulta.pergunta,
        editingConsulta.resposta
      );

      // Atualizar na lista local
      setConsultas(prev => prev.map(c => 
        c.id === editingConsulta.id 
          ? {
              ...c,
              pergunta_funcionario: editingConsulta.pergunta,
              resposta_gerada: editingConsulta.resposta
            }
          : c
      ));

      setEditingConsulta(null);
      toast.success('Consulta atualizada com sucesso!');

    } catch (error: any) {
      console.error('Erro ao salvar edição:', error);
      toast.error('Erro ao salvar alterações');
    } finally {
      setEditingLoading(false);
    }
  };

  const deleteSelected = async () => {
    if (selectedIds.length === 0) return;

    try {
      setBulkActionLoading(true);

      await apiService.deleteEquipeConsultasBulk(selectedIds);

      // Remover da lista local
      setConsultas(prev => prev.filter(c => !selectedIds.includes(c.id)));
      setSelectedIds([]);
      setShowDeleteConfirm(false);

      toast.success(`${selectedIds.length} consulta(s) removida(s) com sucesso!`);

    } catch (error: any) {
      console.error('Erro ao deletar consultas:', error);
      toast.error('Erro ao remover consultas');
    } finally {
      setBulkActionLoading(false);
    }
  };

  const exportSelected = async () => {
    if (selectedIds.length === 0) {
      toast.error('Selecione pelo menos uma consulta para exportar');
      return;
    }

    try {
      setBulkActionLoading(true);

      const result = await apiService.exportEquipeFinetuning(selectedIds);

      // Criar e baixar arquivo
      const blob = new Blob([result.content], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`${result.total_samples} consultas exportadas para fine-tuning!`);

    } catch (error: any) {
      console.error('Erro ao exportar consultas:', error);
      toast.error('Erro ao exportar consultas');
    } finally {
      setBulkActionLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('pt-BR');
    } catch {
      return dateString;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <Square3Stack3DIcon className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Equipe - Consultas</h1>
              <p className="text-gray-600 dark:text-gray-300">Gerencie perguntas e respostas da equipe de atendimento</p>
            </div>
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Filtros</h2>
          
          <form onSubmit={handleSubmit(onFiltersSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Busca por texto */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Buscar em perguntas e respostas
                </label>
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    {...register('search')}
                    type="text"
                    placeholder="Digite para buscar..."
                    className="w-full pl-10 p-3 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                  />
                </div>
              </div>

              {/* Data inicial */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Data inicial
                </label>
                <div className="relative">
                  <CalendarDaysIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    {...register('date_from')}
                    type="date"
                    className="w-full pl-10 p-3 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>

              {/* Data final */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Data final
                </label>
                <div className="relative">
                  <CalendarDaysIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    {...register('date_to')}
                    type="date"
                    className="w-full pl-10 p-3 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center pt-4">
              <button
                type="button"
                onClick={clearFilters}
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
              >
                Limpar filtros
              </button>
              
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-2 rounded-md font-medium"
              >
                {loading ? 'Filtrando...' : 'Aplicar Filtros'}
              </button>
            </div>
          </form>
        </div>

        {/* Ações em lote */}
        {selectedIds.length > 0 && (
          <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <CheckCircleIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                <span className="text-blue-800 dark:text-blue-200 font-medium">
                  {selectedIds.length} consulta(s) selecionada(s)
                </span>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={exportSelected}
                  disabled={bulkActionLoading}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-md font-medium flex items-center space-x-2"
                >
                  <DocumentArrowDownIcon className="w-4 h-4" />
                  <span>Exportar Fine-tuning</span>
                </button>

                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  disabled={bulkActionLoading}
                  className="bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white px-4 py-2 rounded-md font-medium flex items-center space-x-2"
                >
                  <TrashIcon className="w-4 h-4" />
                  <span>Deletar Selecionadas</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tabela de consultas */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Consultas ({consultas.length})
              </h2>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={selectedIds.length === consultas.length && consultas.length > 0}
                  onChange={selectAll}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label className="text-sm text-gray-600 dark:text-gray-300">
                  Selecionar todas
                </label>
              </div>
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/30 border-b border-red-200 dark:border-red-700">
              <div className="flex items-center space-x-2">
                <ExclamationTriangleIcon className="w-5 h-5 text-red-600 dark:text-red-400" />
                <span className="text-red-800 dark:text-red-200">{error}</span>
              </div>
            </div>
          )}

          {loading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-300">Carregando consultas...</p>
            </div>
          ) : consultas.length === 0 ? (
            <div className="p-12 text-center text-gray-500 dark:text-gray-400">
              <Square3Stack3DIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Nenhuma consulta encontrada</p>
              <p className="text-sm">Use os filtros para buscar consultas específicas</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider w-12">
                      <input
                        type="checkbox"
                        checked={selectedIds.length === consultas.length}
                        onChange={selectAll}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Pergunta
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Resposta
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Data
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider w-32">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {consultas.map((consulta) => (
                    <tr key={consulta.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(consulta.id)}
                          onChange={() => toggleSelection(consulta.id)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                      </td>
                      <td className="px-6 py-4">
                        {editingConsulta?.id === consulta.id ? (
                          <textarea
                            value={editingConsulta.pergunta}
                            onChange={(e) => setEditingConsulta(prev => prev ? {...prev, pergunta: e.target.value} : null)}
                            className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-y"
                            rows={3}
                          />
                        ) : (
                          <div className="text-sm text-gray-900 dark:text-white max-w-md">
                            <p className="line-clamp-3">{consulta.pergunta_funcionario}</p>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {editingConsulta?.id === consulta.id ? (
                          <textarea
                            value={editingConsulta.resposta}
                            onChange={(e) => setEditingConsulta(prev => prev ? {...prev, resposta: e.target.value} : null)}
                            className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-y"
                            rows={4}
                          />
                        ) : (
                          <div className="text-sm text-gray-900 dark:text-white max-w-md">
                            <p className="line-clamp-4">{consulta.resposta_gerada}</p>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {formatDate(consulta.criado_em)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        {editingConsulta?.id === consulta.id ? (
                          <div className="flex items-center justify-center space-x-2">
                            <button
                              onClick={saveEditing}
                              disabled={editingLoading}
                              className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300"
                              title="Salvar alterações"
                            >
                              <CheckIcon className="w-5 h-5" />
                            </button>
                            <button
                              onClick={cancelEditing}
                              disabled={editingLoading}
                              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                              title="Cancelar edição"
                            >
                              <XMarkIcon className="w-5 h-5" />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-center space-x-2">
                            <button
                              onClick={() => startEditing(consulta)}
                              className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                              title="Editar consulta"
                            >
                              <PencilIcon className="w-5 h-5" />
                            </button>
                            <button
                              onClick={() => {
                                setSelectedIds([consulta.id]);
                                setShowDeleteConfirm(true);
                              }}
                              className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                              title="Deletar consulta"
                            >
                              <TrashIcon className="w-5 h-5" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal de confirmação de exclusão */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md mx-4">
              <div className="flex items-center space-x-3 mb-4">
                <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Confirmar Exclusão
                </h3>
              </div>
              
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                Tem certeza que deseja excluir {selectedIds.length} consulta(s)? 
                Esta ação não pode ser desfeita.
              </p>
              
              <div className="flex space-x-4">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={bulkActionLoading}
                  className="flex-1 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 py-2 px-4 rounded-md hover:bg-gray-300 dark:hover:bg-gray-500"
                >
                  Cancelar
                </button>
                <button
                  onClick={deleteSelected}
                  disabled={bulkActionLoading}
                  className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white py-2 px-4 rounded-md"
                >
                  {bulkActionLoading ? 'Excluindo...' : 'Excluir'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
