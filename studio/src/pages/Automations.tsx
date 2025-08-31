import { useState } from 'react';
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

// Mock data para demonstração
const mockAutomations: Automation[] = [
  {
    id: 'ask_deposit_for_test',
    topic: 'teste',
    eligibility: 'não concordou em depositar e não depositou',
    priority: 0.85,
    cooldown: '24h',
    output: {
      type: 'message',
      text: 'Para liberar o teste, você consegue fazer um pequeno depósito? 💰',
      buttons: [
        {
          id: 'btn_yes_deposit',
          label: 'Sim, consigo',
          kind: 'callback',
          set_facts: { 'agreements.can_deposit': true },
          track: { event: 'click_yes_deposit', utm_passthrough: true }
        },
        {
          id: 'btn_help_deposit',
          label: 'Como deposito?',
          kind: 'url',
          url: '${deposit_help_link}',
          track: { event: 'open_deposit_help' }
        }
      ]
    }
  },
  {
    id: 'signup_link',
    topic: 'conta',
    eligibility: 'não tem conta em alguma corretora suportada',
    priority: 0.90,
    cooldown: '12h',
    output: {
      type: 'message',
      text: 'Primeiro você precisa criar uma conta na corretora! 📊\n\nRecomendo a Quotex - é mais fácil para iniciantes:',
      buttons: [
        {
          id: 'btn_quotex_signup',
          label: 'Criar conta Quotex',
          kind: 'url',
          url: 'https://quotex.io/pt/?lid=123456',
          track: { event: 'signup_quotex_click' }
        }
      ]
    }
  },
  {
    id: 'trial_unlock',
    topic: 'liberacao',
    eligibility: 'todas as etapas anteriores cumpridas',
    priority: 1.0,
    cooldown: '0h',
    output: {
      type: 'message',
      text: '🎉 Parabéns! Seu acesso foi liberado!\n\nAgora você pode usar o robô de sinais. Lembrando:\n• Opera em M5\n• Usa estratégia Gale\n• Acompanhe sempre o mercado\n\nBoa sorte e bons trades! 📈'
    }
  }
];

export default function Automations() {
  const [automations] = useState<Automation[]>(mockAutomations);

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

      {/* Cards de Estatísticas - MOVIDO PARA O TOPO */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="stats-card">
          <div className="stats-number">3</div>
          <div className="stats-label">Total de automações</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">2</div>
          <div className="stats-label">Alta prioridade</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">12h</div>
          <div className="stats-label">Cooldown médio</div>
        </div>
        <div className="stats-card">
          <div className="stats-number">87%</div>
          <div className="stats-label">Taxa de conversão</div>
        </div>
      </div>

      {/* Filtros Rápidos */}
      <div className="flex flex-wrap gap-2">
        <button className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
          Todas (3)
        </button>
        <button className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600">
          Alta prioridade (2)
        </button>
        <button className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600">
          Teste (1)
        </button>
        <button className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600">
          Conta (1)
        </button>
      </div>

      {/* Lista de Automações */}
      <div className="space-y-4">
        {automations.map((automation) => (
          <CollapsibleSection
            key={automation.id}
            title={automation.id}
            description={`Tópico: ${automation.topic} • Prioridade: ${getPriorityLabel(automation.priority)} (${automation.priority}) • ${automation.eligibility}`}
            icon={CogIcon}
            defaultExpanded={false}
          >
            <div className="flex justify-end mb-6 space-x-2">
              <Link
                to={`/simulator?automation=${automation.id}`}
                className="btn-secondary flex items-center"
              >
                <PlayIcon className="h-4 w-4 mr-1" />
                Testar
              </Link>
              <Link
                to={`/automations/${automation.id}/edit`}
                className="btn-secondary flex items-center"
              >
                <PencilIcon className="h-4 w-4 mr-1" />
                Editar
              </Link>
              <button className="text-red-600 hover:text-red-500 p-2">
                <TrashIcon className="h-4 w-4" />
              </button>
            </div>
                
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
        <ul className="text-sm text-green-800 space-y-1">
          <li>• Use prioridades para controlar qual mensagem aparece primeiro</li>
          <li>• Configure cooldowns para evitar spam</li>
          <li>• Teste sempre no simulador antes de publicar</li>
          <li>• Botões com set_facts atualizam o estado do lead automaticamente</li>
        </ul>
      </div>
    </div>
  );
}
