from django.shortcuts import render
from django.http import JsonResponse
from django.contrib import messages
from .forms import VencimentoForm
from .services import FichasAPIService
from .vencimento_service_fixed import VencimentoServiceFixed
import json

# Create your views here.

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
                
                # Return the results to be displayed in the template
                return render(request, 'vencimento.html', {
                    'form': form,
                    'resultados': resultados,
                    'metadata': metadata,
                    'matricula': matricula,
                    'data_inicio': data_inicio,
                    'data_fim': data_fim
                })
            else:
                messages.error(request, result['message'])
    else:
        form = VencimentoForm()
    
    return render(request, 'vencimento.html', {'form': form})

def validate_professor_ajax(request):
    """AJAX endpoint to validate professor existence"""
    
    if request.method == 'GET':
        matricula = request.GET.get('matricula')
        
        if not matricula:
            return JsonResponse({'valid': False, 'message': 'Matrícula não informada'})
        
        try:
            matricula = int(matricula)
            api_service = FichasAPIService()
            result = api_service.validate_professor_exists(matricula)
            
            return JsonResponse({
                'valid': result['exists'],
                'message': result['message'],
                'professor': result.get('professor', {})
            })
            
        except ValueError:
            return JsonResponse({'valid': False, 'message': 'Matrícula deve ser um número'})
        except Exception as e:
            return JsonResponse({'valid': False, 'message': f'Erro: {str(e)}'})
    
    return JsonResponse({'valid': False, 'message': 'Método não permitido'})



def vencimento_preview_ajax(request):
    """AJAX endpoint to get vencimento data preview"""
    
    if request.method == 'GET':
        matricula = request.GET.get('matricula')
        data_inicio = request.GET.get('data_inicio')
        data_fim = request.GET.get('data_fim')
        
        if not all([matricula, data_inicio, data_fim]):
            return JsonResponse({'success': False, 'message': 'Parâmetros incompletos'})
        
        try:
            from datetime import datetime
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            
            vencimento_service = VencimentoServiceFixed()
            result = vencimento_service.get_vencimento_summary(matricula, data_inicio, data_fim)
            
            return JsonResponse(result)
            
        except ValueError as e:
            return JsonResponse({'success': False, 'message': f'Erro nos parâmetros: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})