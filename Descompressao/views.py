from django.shortcuts import render
from django.http import HttpResponse
from .forms import DescompressaoForm
from . import descompressao
from io import BytesIO

# Create your views here.

def descompressao_view(request):
    if request.method == 'POST':
        form = DescompressaoForm(request.POST)
        if form.is_valid():
            matricula = form.cleaned_data['matricula']
            dados = descompressao.pesquisarBD(matricula)
            wb = descompressao.preencherexcel(dados, return_wb=True)  # Modify preencherexcel to return wb if needed

            # Save workbook to memory
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            response = HttpResponse(
                output,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename=descompressao_{matricula}.xlsm'
            return response
    else:
        form = DescompressaoForm()
    return render(request, 'descompressao.html', {'form': form})