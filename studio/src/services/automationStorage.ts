import type { Automation } from '../types';

const STORAGE_KEY = 'manyblack_automations';

// Automações padrão do sistema
const defaultAutomations: Automation[] = [
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

export const automationStorage = {
  // Carregar todas as automações
  getAll(): Automation[] {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) {
        // Primeira vez - inicializar com padrões
        this.setAll(defaultAutomations);
        return defaultAutomations;
      }
      return JSON.parse(stored);
    } catch (error) {
      console.error('Erro ao carregar automações:', error);
      return defaultAutomations;
    }
  },

  // Salvar todas as automações
  setAll(automations: Automation[]): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(automations));
    } catch (error) {
      console.error('Erro ao salvar automações:', error);
      throw new Error('Erro ao salvar automações no localStorage');
    }
  },

  // Adicionar nova automação
  add(automation: Automation): void {
    const automations = this.getAll();
    
    // Verificar se ID já existe
    if (automations.some(a => a.id === automation.id)) {
      throw new Error(`Automação com ID "${automation.id}" já existe`);
    }
    
    automations.push(automation);
    this.setAll(automations);
  },

  // Atualizar automação existente
  update(id: string, automation: Automation): void {
    const automations = this.getAll();
    const index = automations.findIndex(a => a.id === id);
    
    if (index === -1) {
      throw new Error(`Automação com ID "${id}" não encontrada`);
    }
    
    automations[index] = automation;
    this.setAll(automations);
  },

  // Buscar automação por ID
  getById(id: string): Automation | null {
    const automations = this.getAll();
    return automations.find(a => a.id === id) || null;
  },

  // Deletar automação
  delete(id: string): void {
    const automations = this.getAll();
    const filtered = automations.filter(a => a.id !== id);
    
    if (filtered.length === automations.length) {
      throw new Error(`Automação com ID "${id}" não encontrada`);
    }
    
    this.setAll(filtered);
  },

  // Resetar para padrões
  reset(): void {
    this.setAll(defaultAutomations);
  },

  // Estatísticas
  getStats() {
    const automations = this.getAll();
    return {
      total: automations.length,
      highPriority: automations.filter(a => a.priority >= 0.8).length,
      avgCooldown: this.calculateAvgCooldown(automations),
      topics: [...new Set(automations.map(a => a.topic))].length
    };
  },

  private calculateAvgCooldown(automations: Automation[]): string {
    const cooldowns = automations.map(a => {
      const match = a.cooldown.match(/(\d+)h/);
      return match ? parseInt(match[1]) : 0;
    });
    
    const avg = cooldowns.reduce((sum, val) => sum + val, 0) / cooldowns.length;
    return `${Math.round(avg)}h`;
  }
};
