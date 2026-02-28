"""
SRCC Modules - Plugin-style architecture for Stone Ranch Command Center
Each module is self-contained with its own data handling and routes.
"""

from .life import register_routes as register_life_routes, load_life_data, save_life_data

__all__ = ['register_life_routes', 'load_life_data', 'save_life_data']
