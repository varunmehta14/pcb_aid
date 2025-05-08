"""
Shared dependencies for FastAPI routes.
"""
from typing import Dict, Any

# Global PCB data store (in memory database)
pcb_data_store: Dict[str, Any] = {}

def get_pcb_data_store():
    """Dependency that provides access to the pcb_data_store.
    
    This allows routes in other modules to access the centralized PCB data store.
    """
    return pcb_data_store 