from django import forms
from datetime import date, datetime
import re

class VencimentoForm(forms.Form):
    """Form for vencimento data calculation"""
    
    matricula = forms.CharField(
        label='Matrícula do Professor', 
        max_length=15, 
        required=True,
        help_text='Digite a matrícula do professor (ex: 00292553-03)',
        widget=forms.TextInput(attrs={
            'placeholder': '00292553-03',
            'pattern': r'\d{8}-\d{2}',
            'title': 'Formato: 00000000-00',
            'class': 'form-control'
        })
    )
    
    data_inicio = forms.DateField(
        label='Data de Início do Período', 
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        }),
        help_text='Data de início do período para busca de vencimentos'
    )
    
    data_fim = forms.DateField(
        label='Data de Fim do Período', 
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        help_text='Data final do período para busca de vencimentos'
    )
    
    def clean_matricula(self):
        """Validate and normalize matricula format"""
        matricula = self.cleaned_data.get('matricula', '').strip()
        
        if not matricula:
            raise forms.ValidationError('Matrícula é obrigatória.')
        
        # Remove any spaces or special characters except dash
        matricula = re.sub(r'[^\d-]', '', matricula)
        
        # Check if it's in the correct format (8 digits - 2 digits)
        if re.match(r'^\d{8}-\d{2}$', matricula):
            return matricula
        
        # Try to format if it's just numbers
        numbers_only = re.sub(r'[^\d]', '', matricula)
        
        if len(numbers_only) == 10:
            # Format as 00000000-00
            formatted = f"{numbers_only[:8]}-{numbers_only[8:]}"
            return formatted
        elif len(numbers_only) == 8:
            # Assume it needs -00 at the end
            formatted = f"{numbers_only}-00"
            return formatted
        elif len(numbers_only) < 8:
            # Pad with leading zeros
            padded = numbers_only.zfill(8)
            formatted = f"{padded}-00"
            return formatted
        else:
            raise forms.ValidationError(
                'Formato de matrícula inválido. Use o formato: 00000000-00'
            )
    
    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if data_inicio and data_fim:
            if data_inicio > data_fim:
                raise forms.ValidationError('A data de início deve ser anterior à data de fim.')
            
            if data_fim > date.today():
                raise forms.ValidationError('A data de fim não pode ser no futuro.')
                
            # Check if period is not too large (more than 10 years)
            if (data_fim - data_inicio).days > 365 * 10:
                raise forms.ValidationError('O período não pode ser maior que 10 anos.')
        
        return cleaned_data