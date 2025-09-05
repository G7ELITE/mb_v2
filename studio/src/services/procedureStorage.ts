import type { Procedure } from '../types';
import yaml from 'js-yaml';

// const API_BASE_URL = 'http://localhost:8000';
const STORAGE_KEY = 'manyblack_procedures_cache';

// Cache local para performance
let proceduresCache: Procedure[] | null = null;
let cacheTimestamp = 0;
const CACHE_TTL = 30000; // 30 seconds

// Backend API integration service
export const procedureStorage = {
  // Load all procedures from backend
  async getAll(): Promise<Procedure[]> {
    // Check cache first
    const now = Date.now();
    if (proceduresCache && (now - cacheTimestamp) < CACHE_TTL) {
      return proceduresCache;
    }

    try {
      const response = await fetch('/policies/procedures.yml');
      
      if (!response.ok) {
        console.warn('Procedures file not found, returning empty array');
        proceduresCache = [];
        cacheTimestamp = now;
        return [];
      }

      const yamlText = await response.text();
      const procedures = yaml.load(yamlText) as Procedure[] || [];
      
      // Cache the result
      proceduresCache = Array.isArray(procedures) ? procedures : [];
      cacheTimestamp = now;
      
      return proceduresCache;
    } catch (error) {
      console.error('Error loading procedures:', error);
      
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

  // Save all procedures to backend
  async setAll(procedures: Procedure[]): Promise<void> {
    try {
      const yamlContent = yaml.dump(procedures, { 
        // defaultFlowStyle: false, 
        noRefs: true 
      });
      
      const response = await fetch('/api/catalog/save-procedures', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: yamlContent })
      });

      if (!response.ok) {
        throw new Error(`Failed to save procedures: ${response.statusText}`);
      }

      // Update cache
      proceduresCache = procedures;
      cacheTimestamp = Date.now();
      
      // Also save to localStorage as backup
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(procedures));
      } catch {}

    } catch (error) {
      console.error('Error saving procedures:', error);
      throw new Error('Failed to save procedures to backend');
    }
  },

  // Add new procedure
  async add(procedure: Procedure): Promise<void> {
    const procedures = await this.getAll();
    
    // Check if ID already exists
    if (procedures.some(p => p.id === procedure.id)) {
      throw new Error(`Procedure with ID "${procedure.id}" already exists`);
    }
    
    procedures.push(procedure);
    await this.setAll(procedures);
  },

  // Update existing procedure
  async update(id: string, procedure: Procedure): Promise<void> {
    const procedures = await this.getAll();
    const index = procedures.findIndex(p => p.id === id);
    
    if (index === -1) {
      throw new Error(`Procedure with ID "${id}" not found`);
    }
    
    procedures[index] = procedure;
    await this.setAll(procedures);
  },

  // Find procedure by ID
  async getById(id: string): Promise<Procedure | null> {
    const procedures = await this.getAll();
    return procedures.find(p => p.id === id) || null;
  },

  // Delete procedure
  async delete(id: string): Promise<void> {
    const procedures = await this.getAll();
    const filtered = procedures.filter(p => p.id !== id);
    
    if (filtered.length === procedures.length) {
      throw new Error(`Procedure with ID "${id}" not found`);
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
      proceduresCache = [];
      cacheTimestamp = Date.now();
      
    } catch (error) {
      console.error('Error resetting catalog:', error);
      throw new Error('Failed to reset catalog');
    }
  },

  // Get statistics
  async getStats(): Promise<any> {
    const procedures = await this.getAll();
    return {
      total: procedures.length,
      published: procedures.length, // Assuming all are published
      drafts: 0,
      avgSteps: procedures.length > 0 ? 
        procedures.reduce((sum, p) => sum + p.steps.length, 0) / procedures.length : 0
    };
  },

  // Clear cache
  clearCache(): void {
    proceduresCache = null;
    cacheTimestamp = 0;
  }
};
