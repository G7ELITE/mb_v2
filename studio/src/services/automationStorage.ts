import type { Automation } from '../types';
import yaml from 'js-yaml';

const API_BASE_URL = 'http://localhost:8000';
const STORAGE_KEY = 'manyblack_automations_cache';

// Cache local para performance
let automationsCache: Automation[] | null = null;
let cacheTimestamp = 0;
const CACHE_TTL = 30000; // 30 seconds

// Backend API integration service
export const automationStorage = {
  // Load all automations from backend
  async getAll(): Promise<Automation[]> {
    // Check cache first
    const now = Date.now();
    if (automationsCache && (now - cacheTimestamp) < CACHE_TTL) {
      return automationsCache;
    }

    try {
      const response = await fetch('/policies/catalog.yml');
      
      if (!response.ok) {
        console.warn('Catalog file not found, returning empty array');
        automationsCache = [];
        cacheTimestamp = now;
        return [];
      }

      const yamlText = await response.text();
      const automations = yaml.load(yamlText) as Automation[] || [];
      
      // Cache the result
      automationsCache = Array.isArray(automations) ? automations : [];
      cacheTimestamp = now;
      
      return automationsCache;
    } catch (error) {
      console.error('Error loading automations:', error);
      
      // Try to load from localStorage cache as fallback
      try {
        const cached = localStorage.getItem(STORAGE_KEY);
        if (cached) {
          return JSON.parse(cached);
        }
      } catch {}
      
      return [];
    }
  },

  // Save all automations to backend
  async setAll(automations: Automation[]): Promise<void> {
    try {
      const yamlContent = yaml.dump(automations, { 
        defaultFlowStyle: false, 
        noRefs: true 
      });
      
      const response = await fetch('/api/catalog/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: yamlContent })
      });

      if (!response.ok) {
        throw new Error(`Failed to save automations: ${response.statusText}`);
      }

      // Update cache
      automationsCache = automations;
      cacheTimestamp = Date.now();
      
      // Also save to localStorage as backup
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(automations));
      } catch {}

    } catch (error) {
      console.error('Error saving automations:', error);
      throw new Error('Failed to save automations to backend');
    }
  },

  // Add new automation
  async add(automation: Automation): Promise<void> {
    const automations = await this.getAll();
    
    // Check if ID already exists
    if (automations.some(a => a.id === automation.id)) {
      throw new Error(`Automation with ID "${automation.id}" already exists`);
    }
    
    automations.push(automation);
    await this.setAll(automations);
  },

  // Update existing automation
  async update(id: string, automation: Automation): Promise<void> {
    const automations = await this.getAll();
    const index = automations.findIndex(a => a.id === id);
    
    if (index === -1) {
      throw new Error(`Automation with ID "${id}" not found`);
    }
    
    automations[index] = automation;
    await this.setAll(automations);
  },

  // Find automation by ID
  async getById(id: string): Promise<Automation | null> {
    const automations = await this.getAll();
    return automations.find(a => a.id === id) || null;
  },

  // Delete automation
  async delete(id: string): Promise<void> {
    const automations = await this.getAll();
    const filtered = automations.filter(a => a.id !== id);
    
    if (filtered.length === automations.length) {
      throw new Error(`Automation with ID "${id}" not found`);
    }
    
    await this.setAll(filtered);
  },

  // Reset catalog via API
  async reset(): Promise<void> {
    try {
      const response = await fetch('/api/catalog/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          create_backup_first: true,
          keep_confirm_targets: true
        })
      });

      if (!response.ok) {
        throw new Error(`Reset failed: ${response.statusText}`);
      }

      // Clear cache
      automationsCache = [];
      cacheTimestamp = Date.now();
      
    } catch (error) {
      console.error('Error resetting catalog:', error);
      throw new Error('Failed to reset catalog');
    }
  },

  // Get statistics
  async getStats(): Promise<any> {
    const automations = await this.getAll();
    return {
      total: automations.length,
      highPriority: automations.filter(a => a.priority >= 0.8).length,
      avgCooldown: this.calculateAvgCooldown(automations),
      topics: [...new Set(automations.map(a => a.topic))].length
    };
  },

  // Get catalog statistics from API
  async getCatalogStats(): Promise<any> {
    try {
      const response = await fetch('/api/catalog/stats');
      if (!response.ok) {
        throw new Error(`Failed to get stats: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error getting catalog stats:', error);
      return await this.getStats(); // Fallback to local stats
    }
  },

  calculateAvgCooldown(automations: Automation[]): string {
    if (automations.length === 0) return '0h';
    
    const cooldowns = automations.map(a => {
      const match = a.cooldown.match(/(\d+)h/);
      return match ? parseInt(match[1]) : 0;
    });
    
    const avg = cooldowns.reduce((sum, val) => sum + val, 0) / cooldowns.length;
    return `${Math.round(avg)}h`;
  },

  // Clear cache
  clearCache(): void {
    automationsCache = null;
    cacheTimestamp = 0;
  }
};
