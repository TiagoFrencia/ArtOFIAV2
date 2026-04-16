"""
Quick Start - Guía de Inicio Rápido
===================================

Para ejecutar el sistema completamente integrado, usa este ejemplo.
"""

import asyncio
import logging
from src.orchestrator.main_integration import IntegratedArtOfIA


async def quick_start_example():
    """
    Ejemplo de inicio rápido del sistema completamente integrado.
    """
    
    # 1. Crear sistema
    system = IntegratedArtOfIA(".mcp.json")
    
    # 2. Inicializar
    print("\n[*] Initializing ArtOfIABox Integrated System...")
    if not await system.initialize():
        print("[-] Initialization failed")
        return
    
    print("[+] System initialized successfully\n")
    
    # 3. Ver estado
    system.print_status()
    
    # 4. Ejecutar operación
    print("\n[*] Running full red team operation...\n")
    
    target = {
        "name": "Vulnerable API",
        "url": "http://api.target.com",
        "type": "rest_api",
        "endpoints": ["/users", "/products", "/admin"],
    }
    
    result = await system.run_full_red_team_operation(target)
    
    # 5. Ver resultado
    print(f"\n[+] Operation Result: {result.get('result')}")
    
    if result.get('stages', {}).get('exploitation', {}).get('success'):
        print("[+] Exploitation was successful!")
        print(f"    Output: {result['stages']['exploitation'].get('output', 'N/A')[:100]}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s"
    )
    
    asyncio.run(quick_start_example())
