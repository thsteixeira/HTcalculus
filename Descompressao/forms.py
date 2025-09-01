from django import forms

class DescompressaoForm(forms.Form):
    matricula = forms.IntegerField(label='Insira a matrícula', min_value=1, max_value=99999999, required=True)
    #inicio = forms.DateField(label='Data de início', required=True)
    #fim = forms.DateField(label='Data de fim', required=True)