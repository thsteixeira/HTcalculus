"""
Service class for integrating the Fichas API with Django
"""

import os
import sys
from datetime import date, datetime
from typing import Optional, Dict, List, Any

# Add the utils directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, 'utils')
sys.path.append(utils_dir)

from fichas_api import FichasAPI_Manager


class FichasAPIService:
    """Service class for handling Fichas API operations in Django"""
    
    def __init__(self):
        self.api_manager = FichasAPI_Manager()
    
    def validate_professor_exists(self, matricula: str) -> Dict[str, Any]:
        """
        Validate if professor exists in the system.
        
        Args:
            matricula: Professor's matricula in format 00000000-00
            
        Returns:
            Dictionary with validation result
        """
        try:
            result = self.api_manager.busca_matricula(matricula)
            
            if result:
                return {
                    'exists': True,
                    'professor': result,
                    'message': 'Professor encontrado'
                }
            else:
                return {
                    'exists': False,
                    'professor': None,
                    'message': 'Professor não encontrado'
                }
                
        except Exception as e:
            return {
                'exists': False,
                'professor': None,
                'message': f'Erro ao validar professor: {str(e)}'
            }
