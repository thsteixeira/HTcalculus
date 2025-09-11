from django.shortcuts import render
from django.contrib import messages
from .forms import VencimentoForm
import json
from datetime import datetime

# Add utils directory to path for import
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, 'utils')
if utils_dir not in sys.path:
    sys.path.insert(0, utils_dir)

from services import VencimentoServiceFixed

# Create your views here.

def save_raw_data_to_json(raw_data, professor_data, metadata, matricula, data_inicio, data_fim):
    """
    Save raw data to a readable JSON file with proper formatting
    """
    try:
        # Create a comprehensive data structure
        json_data = {
            "consultation_info": {
                "matricula": matricula,
                "data_inicio": data_inicio.strftime("%Y-%m-%d") if data_inicio else None,
                "data_fim": data_fim.strftime("%Y-%m-%d") if data_fim else None,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_records": len(raw_data) if raw_data else 0,
                "description": "Dados completos de vencimentos extraídos da API"
            },
            "summary_metadata": {
                "professor_name": metadata.get('professor_name', ''),
                "total_vencimentos": float(metadata.get('total_vencimentos', 0)),
                "valor_medio": float(metadata.get('valor_medio', 0)),
                "periodo_inicio": metadata.get('periodo_inicio', ''),
                "periodo_fim": metadata.get('periodo_fim', ''),
                "total_periodos": metadata.get('total_periodos', 0),
                "total_registros": metadata.get('total_registros', 0)
            },
            "professor_complete_data": {
                "description": "Dados completos do professor retornados pela API",
                "data": professor_data
            },
            "vencimento_records": {
                "description": "Registros individuais de vencimento organizados por data",
                "records": []
            },
            "monthly_summary": {
                "description": "Resumo mensal dos vencimentos",
                "data": {}
            }
        }
        
        # Format raw data for better readability and organize by month/year
        monthly_totals = {}
        if raw_data:
            for i, record in enumerate(raw_data, 1):
                # Handle date serialization
                record_date = record.get('date')
                if hasattr(record_date, 'strftime'):
                    date_str = record_date.strftime("%Y-%m-%d")
                else:
                    date_str = str(record_date) if record_date else None
                
                formatted_record = {
                    "record_id": i,
                    "year": record.get('year'),
                    "month": record.get('month'),
                    "month_name": datetime(2000, record.get('month', 1), 1).strftime("%B") if record.get('month') else None,
                    "date": date_str,
                    "vencimento_details": {
                        "nome_verba": record.get('nome_verba'),
                        "cod_verba": record.get('cod_verba'),
                        "valor": float(record.get('valor', 0))
                    },
                    "original_record": record  # Include all original fields for completeness
                }
                json_data["vencimento_records"]["records"].append(formatted_record)
                
                # Calculate monthly totals
                month_key = f"{record.get('year', 0)}-{record.get('month', 0):02d}"
                if month_key not in monthly_totals:
                    monthly_totals[month_key] = {
                        "year": record.get('year'),
                        "month": record.get('month'),
                        "month_name": datetime(2000, record.get('month', 1), 1).strftime("%B") if record.get('month') else None,
                        "total_valor": 0,
                        "record_count": 0
                    }
                monthly_totals[month_key]["total_valor"] += float(record.get('valor', 0))
                monthly_totals[month_key]["record_count"] += 1
        
        # Add monthly summary to JSON
        json_data["monthly_summary"]["data"] = dict(sorted(monthly_totals.items()))
        
        # Create filename with timestamp and matricula
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vencimento_data_{matricula}_{timestamp}.json"
        
        # Save to the Descompressao directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, filename)
        
        # Write JSON with proper indentation for readability
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, indent=4, ensure_ascii=False, sort_keys=True, default=str)
        
        return {
            'success': True,
            'filename': filename,
            'file_path': file_path,
            'message': f'Dados salvos em: {filename}',
            'record_count': len(raw_data) if raw_data else 0
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro ao salvar JSON: {str(e)}'
        }

def vencimento_view(request):
    """View for generating vencimento data"""
    
    if request.method == 'POST':
        form = VencimentoForm(request.POST)
        if form.is_valid():
            matricula = form.cleaned_data['matricula']
            data_inicio = form.cleaned_data['data_inicio']
            data_fim = form.cleaned_data['data_fim']
            
            # Initialize vencimento service
            vencimento_service = VencimentoServiceFixed()
            
            # Get vencimento data instead of generating Excel
            result = vencimento_service.calculate_vencimento_data(matricula, data_inicio, data_fim)
            
            if result['success']:
                resultados = result['data']
                metadata = result['metadata']
                raw_data = result.get('raw_data', [])  # Get raw data
                professor_data = result.get('professor_full_data', {})  # Get complete professor data
                
                # Save raw data to JSON file for external analysis
                json_result = save_raw_data_to_json(
                    raw_data, professor_data, metadata, 
                    matricula, data_inicio, data_fim
                )
                
                # Add JSON save status to messages
                if json_result['success']:
                    messages.success(request, f"✅ {json_result['message']}")
                else:
                    messages.warning(request, f"⚠️ {json_result['message']}")
                
                # Return the results to be displayed in the template
                return render(request, 'vencimento.html', {
                    'form': form,
                    'resultados': resultados,
                    'metadata': metadata,
                    'raw_data': raw_data,  # Pass raw data to template
                    'professor_data': professor_data,  # Pass complete professor data
                    'matricula': matricula,
                    'data_inicio': data_inicio,
                    'data_fim': data_fim,
                    'json_file_info': json_result  # Pass JSON file info
                })
            else:
                messages.error(request, result['message'])
    else:
        form = VencimentoForm()
    
    return render(request, 'vencimento.html', {'form': form})