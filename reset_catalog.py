#!/usr/bin/env python3
"""
🔄 ManyBlack V2 - Catalog Reset CLI
Safe reset of automation catalogs and procedures with backup
"""
import os
import sys
import json
import asyncio
from pathlib import Path

# Adicionar app ao path
sys.path.insert(0, str(Path(__file__).parent))

from app.api.catalog_reset import get_reset_service
from app.infra.logging import log_structured

def print_banner():
    """Print banner for catalog reset."""
    print("🔄 ManyBlack V2 - Catalog Reset")
    print("=" * 50)
    print("⚠️  ATENÇÃO: Esta operação irá limpar todos os procedimentos e automações!")
    print("📦 Um backup será criado automaticamente antes do reset.")
    print("")

async def main():
    """Main reset function."""
    print_banner()
    
    # Get service
    service = get_reset_service()
    
    try:
        # Show current stats
        print("📊 Status atual do catálogo:")
        stats = await service.get_catalog_stats()
        print(f"   • Automações: {stats.get('automations_count', 0)}")
        print(f"   • Procedimentos: {stats.get('procedures_count', 0)}")
        print(f"   • Targets de confirmação: {stats.get('confirm_targets_count', 0)}")
        print("")
        
        # Check if already empty
        if stats.get('catalog_empty', True) and stats.get('procedures_empty', True):
            print("✅ Catálogo já está vazio. Nenhuma ação necessária.")
            return
        
        # Confirmation prompt
        response = input("🤔 Deseja continuar com o reset? (sim/não): ").lower().strip()
        if response not in ['sim', 's', 'yes', 'y']:
            print("❌ Reset cancelado pelo usuário.")
            return
        
        print("")
        print("🔄 Iniciando reset do catálogo...")
        
        # Create backup
        print("📦 Criando backup...")
        backup_path = await service.create_backup(include_database=False)
        print(f"✅ Backup criado em: {backup_path}")
        
        # Reset catalogs
        print("🧹 Resetando catálogos...")
        reset_results = await service.reset_catalogs(keep_confirm_targets=True)
        
        print("")
        print("✅ Reset concluído com sucesso!")
        print(f"   • Arquivos resetados: {', '.join(reset_results['files_reset'])}")
        print(f"   • Backup disponível em: {backup_path}")
        
        # Clear caches
        print("🗄️  Limpando caches...")
        await service._clear_caches()
        print("✅ Caches limpos")
        
        print("")
        print("🎉 Catálogo resetado! Agora você pode:")
        print("   • Acessar a UI para criar novas automações")
        print("   • Usar os endpoints da API para gerenciar o catálogo")
        print("   • Restaurar o backup se necessário")
        
        # Log structured event
        log_structured("info", "catalog_reset_cli_complete", {
            "backup_path": backup_path,
            "reset_results": reset_results
        })
        
    except Exception as e:
        log_structured("error", "catalog_reset_cli_failed", {
            "error": str(e)
        })
        print(f"❌ Erro durante o reset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
