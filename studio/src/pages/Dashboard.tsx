import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  PlusIcon, 
  CogIcon, 
  PlayIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import type { HealthCheck } from '../types';

export default function Dashboard() {
  const [healthStatus, setHealthStatus] = useState<HealthCheck | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let timer: number | undefined;
    const checkHealth = async () => {
      try {
        console.log('Fazendo requisição para /health...');
        const health = await apiService.healthCheck();
        console.log('Resposta do health:', health);
        setHealthStatus(health);
      } catch (error) {
        console.error('Erro ao verificar saúde do sistema:', error);
        setHealthStatus(null);
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
    timer = window.setInterval(checkHealth, 5000);
    return () => { if (timer) window.clearInterval(timer); };
  }, []);

  const stats = [
    {
      title: 'Procedimentos',
      info: '2 criados / 1 publicado / 1 rascunho',
      value: '2',
      subtitle: 'Total',
      icon: CheckCircleIcon,
      color: 'text-green-600'
    },
    {
      title: 'Automações',
      info: '8 ativas / cooldown médio 12h',
      value: '8',
      subtitle: 'Ativas',
      icon: ClockIcon,
      color: 'text-blue-600'
    },
    {
      title: 'Saúde do Sistema',
      info: loading ? 'Verificando...' : (healthStatus?.status === 'healthy' ? 'Sistema operacional' : 'Problemas detectados'),
      value: loading ? '...' : (healthStatus?.status === 'healthy' ? '✓' : '!'),
      subtitle: healthStatus?.env || 'Backend',
      icon: healthStatus?.status === 'healthy' ? CheckCircleIcon : ExclamationTriangleIcon,
      color: healthStatus?.status === 'healthy' ? 'text-green-600' : 'text-red-600'
    }
  ];

  const quickActions = [
    {
      title: 'Ver Leads',
      description: 'Gerenciar e visualizar leads',
      href: '/leads',
      icon: CogIcon,
      color: 'bg-blue-500 hover:bg-blue-600'
    },
    {
      title: 'Criar Procedimento',
      description: 'Novo funil de passos para leads',
      href: '/procedures/new',
      icon: PlusIcon,
      color: 'bg-green-500 hover:bg-green-600'
    },
    {
      title: 'Simulador',
      description: 'Testar conversas antes de publicar',
      href: '/simulator',
      icon: PlayIcon,
      color: 'bg-purple-500 hover:bg-purple-600'
    }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Painel</h1>
        <p className="mt-2 text-gray-600">
          Visão geral do ManyBlack Studio - Configure funis, automações e teste conversas
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat) => (
          <div key={stat.title} className="stats-card">
            <div className="flex items-center mb-3">
              <div className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700">
                <stat.icon className="h-6 w-6 text-gray-600 dark:text-gray-300" />
              </div>
              <h3 className="ml-3 text-lg font-semibold text-gray-900 dark:text-white">{stat.title}</h3>
            </div>
            <div className="stats-number">{stat.value}</div>
            <div className="stats-label">{stat.subtitle}</div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">{stat.info}</p>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Ações Rápidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action) => (
            <Link
              key={action.title}
              to={action.href}
              className="card hover:shadow-md transition-shadow cursor-pointer group"
            >
              <div className="flex items-center">
                <div className={`p-3 rounded-lg text-white transition-colors ${action.color}`}>
                  <action.icon className="h-6 w-6" />
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                    {action.title}
                  </h3>
                  <p className="text-sm text-gray-500">{action.description}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Atividade Recente</h2>
        <div className="card">
          <div className="space-y-4">
            <div className="flex items-center text-sm">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
              <span className="text-gray-600">10:30</span>
              <span className="ml-3 text-gray-900">Procedimento "liberar_teste" executado com sucesso</span>
            </div>
            <div className="flex items-center text-sm">
              <div className="w-2 h-2 bg-blue-400 rounded-full mr-3"></div>
              <span className="text-gray-600">09:15</span>
              <span className="ml-3 text-gray-900">Automação "ask_deposit_for_test" atualizada</span>
            </div>
            <div className="flex items-center text-sm">
              <div className="w-2 h-2 bg-yellow-400 rounded-full mr-3"></div>
              <span className="text-gray-600">08:45</span>
              <span className="ml-3 text-gray-900">Simulação executada: "quero testar o robô"</span>
            </div>
            <div className="text-center pt-4">
              <Link to="/activity" className="text-blue-600 hover:text-blue-500 text-sm font-medium">
                Ver todas as atividades →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
