import os
import importlib
import inspect
from games.base_game import BaseGame

def get_available_games():
    games = []
    games_dir = os.path.dirname(__file__)
    
    # Scan through all files in games directory
    for filename in os.listdir(games_dir):
        if filename.endswith('_game.py') and filename != 'base_game.py':
            module_name = filename[:-3]  # Remove .py
            try:
                # Import the module dynamically
                module = importlib.import_module(f'games.{module_name}')
                
                # Find game class in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and issubclass(obj, BaseGame) 
                        and obj != BaseGame):
                        games.append(obj)
            except Exception as e:
                print(f"Error loading game {module_name}: {str(e)}")
                
    return games 