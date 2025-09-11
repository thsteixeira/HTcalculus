"""
Fixed vencimento service with better error handling and isolation
"""

import os
import sys
from datetime import datetime, date
from typing import Optional, Dict, List, Any

# Since we're now in the utils directory, we can import fichas_api directly
try:
    from fichas_api import FichasAPI_Manager
except ImportError as e:
    print(f"Import error: {e}")
    raise


class VencimentoServiceFixed:
    """Fixed service class for handling vencimento data operations"""
    
    def __init__(self):
        try:
            self.api_manager = FichasAPI_Manager()
        except Exception as e:
            print(f"Error initializing API manager: {e}")
            raise
    
    def calculate_vencimento_data(self, matricula: str, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """
        Calculate vencimento data for the specified period and return structured data.
        """
        try:
            print(f"Starting vencimento calculation for {matricula}")
            
            # Step 1: Validate professor exists
            print("Step 1: Validating professor...")
            result = self.api_manager.busca_matricula(matricula)
            if not result or 'servidor' not in result:
                return {
                    'success': False,
                    'message': f'Professor com matrícula {matricula} não encontrado',
                    'data': None
                }
            
            professor = result['servidor']
            professor_name = professor.get('SERVIDOR_NOME', 'Desconhecido')
            print(f"Professor found: {professor_name}")
            
            # Step 2: Extract vencimento data from API
            print("Step 2: Extracting vencimento data...")
            vencimento_data = self._extract_vencimento_data_safe(professor, data_inicio, data_fim)
            print(f"Found {len(vencimento_data)} vencimento records")
            
            if not vencimento_data:
                return {
                    'success': False,
                    'message': f'Nenhum dado de vencimento encontrado para o período solicitado',
                    'data': None
                }
            
            # Step 3: Process and structure the data
            print("Step 3: Processing data...")
            processed_data = self._process_vencimento_data(vencimento_data, professor_name, matricula, data_inicio, data_fim)
            
            # Step 4: Calculate summary
            total_vencimentos = sum(record['valor'] for record in vencimento_data)
            valor_medio = total_vencimentos / len(vencimento_data) if len(vencimento_data) > 0 else 0
            
            return {
                'success': True,
                'message': f'Dados calculados com sucesso! {len(vencimento_data)} registros de vencimento processados.',
                'data': processed_data,
                'raw_data': vencimento_data,  # Add raw data for complete view
                'professor_full_data': professor,  # Add complete professor data
                'metadata': {
                    'professor_name': professor_name,
                    'matricula': matricula,
                    'periodo_inicio': f"{data_inicio.month:02d}/{data_inicio.year}",
                    'periodo_fim': f"{data_fim.month:02d}/{data_fim.year}",
                    'total_registros': len(vencimento_data),
                    'total_vencimentos': total_vencimentos,
                    'valor_medio': valor_medio,
                    'filename': f'vencimentos_{matricula.replace("-", "_")}_{data_inicio.strftime("%Y%m")}_{data_fim.strftime("%Y%m")}.xlsx'
                }
            }
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error in calculate_vencimento_data: {e}")
            print(f"Full traceback: {error_traceback}")
            return {
                'success': False,
                'message': f'Erro ao calcular dados: {str(e)}',
                'data': None
            }
    
    def _extract_vencimento_data_safe(self, professor: Dict, data_inicio: date, data_fim: date) -> List[Dict]:
        """
        Safe extraction of vencimento data from professor's fichasFinanceiras
        """
        vencimento_data = []
        
        try:
            fichas = professor.get('fichasFinanceiras', [])
            print(f"Processing {len(fichas)} fichas financeiras")
            
            for ficha in fichas:
                ano = ficha.get('FICHA_FINANCEIRA_ANO_REFERENCIA')
                if not ano:
                    continue
                    
                itens = ficha.get('fichasFinanceirasItens', [])
                for item in itens:
                    nome_verba = item.get('FICHA_FINANCEIRA_ITEM_NOME_VERBA', '').upper()
                    cod_verba = item.get('FICHA_FINANCEIRA_ITEM_COD_VERBA')
                    
                    # Look for vencimento/salary entries (code 101 or vencimento-related names)
                    if (cod_verba == 101 or 
                        'VENCIMENTO' in nome_verba or 
                        'SALARIO' in nome_verba or
                        'SUBSÍDIO' in nome_verba):
                        
                        # Extract monthly values
                        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
                        
                        for i, month in enumerate(months, 1):
                            try:
                                valor = item.get(f'FICHA_FINANCEIRA_ITEM_{month}', 0)
                                if valor and float(valor) > 0:
                                    # Check if this month/year is within the requested period
                                    record_date = date(ano, i, 1)
                                    periodo_inicio = date(data_inicio.year, data_inicio.month, 1)
                                    periodo_fim = date(data_fim.year, data_fim.month, 1)
                                    
                                    if periodo_inicio <= record_date <= periodo_fim:
                                        vencimento_data.append({
                                            'year': ano,
                                            'month': i,
                                            'valor': float(valor),
                                            'nome_verba': nome_verba,
                                            'cod_verba': cod_verba,
                                            'date': record_date
                                        })
                            except (ValueError, TypeError) as e:
                                print(f"Error processing month {month} for year {ano}: {e}")
                                continue
        
        except Exception as e:
            print(f"Error in _extract_vencimento_data_safe: {e}")
            
        return vencimento_data
    
    def _process_vencimento_data(self, vencimento_data: List[Dict], professor_name: str, matricula: str, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """
        Process vencimento data into a structured format for display
        """
        try:
            # Structure for storing processed results
            processed = {
                'professor_name': professor_name,
                'matricula': matricula,
                'relatorio_titulo': f"Relatório de Vencimentos - {professor_name} - Matrícula {matricula}",
                'periodo_inicio': f"{data_inicio.month:02d}/{data_inicio.year}",
                'periodo_fim': f"{data_fim.month:02d}/{data_fim.year}",
                'periodos': []
            }
            
            # Group data by month/year
            monthly_data = {}
            for record in vencimento_data:
                key = (record['year'], record['month'])
                if key not in monthly_data:
                    monthly_data[key] = {
                        'year': record['year'],
                        'month': record['month'],
                        'valores': [],
                        'total': 0.0
                    }
                monthly_data[key]['valores'].append(record)
                monthly_data[key]['total'] += record['valor']
            
            # Sort by date and create periods
            sorted_periods = sorted(monthly_data.keys())
            for year, month in sorted_periods:
                period_data = monthly_data[(year, month)]
                period_date = date(year, month, 1)
                
                periodo = {
                    'mes': period_date,
                    'mes_formatado': period_date.strftime('%b/%Y'),
                    'ano': year,
                    'mes_numero': month,
                    'total_vencimentos': period_data['total'],
                    'registros': period_data['valores'],
                    'quantidade_registros': len(period_data['valores'])
                }
                
                processed['periodos'].append(periodo)
            
            return processed
            
        except Exception as e:
            print(f"Error in _process_vencimento_data: {e}")
            return {
                'professor_name': professor_name,
                'matricula': matricula,
                'periodos': []
            }
    
    def get_vencimento_summary(self, matricula: str, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """
        Get a preview/summary of vencimento data without generating Excel
        """
        try:
            print(f"Getting vencimento summary for {matricula}")
            
            # Get professor data
            result = self.api_manager.busca_matricula(matricula)
            if not result or 'servidor' not in result:
                return {
                    'success': False,
                    'message': 'Professor não encontrado'
                }
            
            professor = result['servidor']
            vencimento_data = self._extract_vencimento_data_safe(professor, data_inicio, data_fim)
            
            if not vencimento_data:
                return {
                    'success': False,
                    'message': 'Nenhum dado de vencimento encontrado para o período'
                }
            
            # Calculate summary
            total_valor = sum(record['valor'] for record in vencimento_data)
            total_registros = len(vencimento_data)
            
            # Group by year/month for details
            monthly_summary = {}
            for record in vencimento_data:
                key = f"{record['month']:02d}/{record['year']}"
                if key not in monthly_summary:
                    monthly_summary[key] = 0
                monthly_summary[key] += record['valor']
            
            return {
                'success': True,
                'professor_name': professor.get('SERVIDOR_NOME'),
                'total_registros': total_registros,
                'total_valor': total_valor,
                'valor_medio': total_valor / total_registros if total_registros > 0 else 0,
                'periodo_inicio': f"{data_inicio.month:02d}/{data_inicio.year}",
                'periodo_fim': f"{data_fim.month:02d}/{data_fim.year}",
                'monthly_summary': monthly_summary
            }
            
        except Exception as e:
            import traceback
            print(f"Error in get_vencimento_summary: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'message': f'Erro ao obter resumo: {str(e)}'
            }
