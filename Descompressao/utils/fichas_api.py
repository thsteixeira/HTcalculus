import requests
from requests.auth import HTTPBasicAuth
from fichas_api_config import api_config
import urllib3
import sys
from datetime import datetime, date
from typing import Optional, Dict, List, Any

# Disable SSL warnings for sandbox
urllib3.disable_warnings()

class FichasAPI_Manager:
    def __init__(self):
        self.token = None
    
    def get_auth_token(self, display_token=False):
        """Authenticates to Fichas API and stores token"""
        try:
            url = f"https://{api_config['host']}/login"
            payload = {
                "email": api_config['email'],
                "password": api_config['password']
            }
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            self.token = response.json()['token']
            
            if display_token:
                print("\n🔑 Authentication Token:")
                print("-"*50)
                print(self.token)
                print("-"*50)
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            return False
        
    def busca_cpf(self, cpf):
        """
        Busca servidores pelo CPF informado.
        Retorna os dados dos servidores encontrados.
        """
        # Autentica antes de buscar
        if not self.get_auth_token():
            print("❌ Não foi possível autenticar na API.")
            return None
        try:
            url = f"https://{api_config['host']}/servidor/busca/cpf"
            payload = {
                "cpf": cpf
            }
            headers = {
                "Content-Type": "application/json",
                "X-Auth-Token": f"{self.token}"
            }
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Erro na busca por CPF: {str(e)}")
            return None

    def busca_matricula(self, matricula) -> Optional[Dict[str, Any]]:
        """
        Busca servidor pela matrícula informada.
        Aceita tanto int quanto string para flexibilidade.
        Retorna os dados do servidor encontrado.
        """
        if not self.get_auth_token():
            print("❌ Não foi possível autenticar na API.")
            return None
        try:
            url = f"https://{api_config['host']}/servidor/busca/matricula"
            payload = {
                "matricula": matricula
            }
            headers = {
                "Content-Type": "application/json",
                "X-Auth-Token": f"{self.token}"
            }
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Erro na busca por matrícula: {str(e)}")
            return None

    def busca_pagamentos_periodo(self, matricula, data_inicio: date, data_fim: date) -> Optional[List[Dict[str, Any]]]:
        """
        Busca pagamentos de um servidor em um período específico.
        Extrai os dados das fichas financeiras do servidor.
        
        Args:
            matricula: Matrícula do servidor (int ou string)
            data_inicio: Data de início do período (YYYY-MM-DD)
            data_fim: Data de fim do período (YYYY-MM-DD)
            
        Returns:
            Lista de pagamentos ou None em caso de erro
        """
        # First get the server data which includes financial records
        servidor_data = self.busca_matricula(matricula)
        if not servidor_data or 'servidor' not in servidor_data:
            print("❌ Servidor não encontrado.")
            return None
        
        try:
            fichas_financeiras = servidor_data['servidor'].get('fichasFinanceiras', [])
            pagamentos = []
            
            # Filter financial records by year range
            year_inicio = data_inicio.year
            year_fim = data_fim.year
            
            for ficha in fichas_financeiras:
                ano_ref = ficha.get('FICHA_FINANCEIRA_ANO_REFERENCIA')
                if ano_ref and year_inicio <= ano_ref <= year_fim:
                    # Extract payment items from this financial record
                    itens = ficha.get('fichasFinanceirasItens', [])
                    for item in itens:
                        # Convert financial item to payment format
                        pagamento = {
                            'ano': ano_ref,
                            'codrubrica': item.get('FICHA_FINANCEIRA_ITEM_COD_VERBA'),
                            'nome_verba': item.get('FICHA_FINANCEIRA_ITEM_NOME_VERBA'),
                            'valor_total': item.get('FICHA_FINANCEIRA_ITEM_TOTAL', 0),
                            'valores_mensais': {
                                'jan': item.get('FICHA_FINANCEIRA_ITEM_JAN', 0),
                                'fev': item.get('FICHA_FINANCEIRA_ITEM_FEV', 0),
                                'mar': item.get('FICHA_FINANCEIRA_ITEM_MAR', 0),
                                'abr': item.get('FICHA_FINANCEIRA_ITEM_ABR', 0),
                                'mai': item.get('FICHA_FINANCEIRA_ITEM_MAI', 0),
                                'jun': item.get('FICHA_FINANCEIRA_ITEM_JUN', 0),
                                'jul': item.get('FICHA_FINANCEIRA_ITEM_JUL', 0),
                                'ago': item.get('FICHA_FINANCEIRA_ITEM_AGO', 0),
                                'set': item.get('FICHA_FINANCEIRA_ITEM_SET', 0),
                                'out': item.get('FICHA_FINANCEIRA_ITEM_OUT', 0),
                                'nov': item.get('FICHA_FINANCEIRA_ITEM_NOV', 0),
                                'dez': item.get('FICHA_FINANCEIRA_ITEM_DEZ', 0),
                                'dec_terceiro': item.get('FICHA_FINANCEIRA_ITEM_DEC_TERCEIRO', 0)
                            }
                        }
                        pagamentos.append(pagamento)
            
            return pagamentos
            
        except Exception as e:
            print(f"❌ Erro ao processar pagamentos: {str(e)}")
            return None

    def processar_pagamentos_para_calculo(self, pagamentos: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Processa os pagamentos retornados pela API e organiza por categoria
        para uso nos cálculos de descompressão.
        
        Args:
            pagamentos: Lista de pagamentos retornados pela API
            
        Returns:
            Dicionário organizado por categorias de verbas
        """
        # Mapeamento de códigos de rubrica para categorias
        rubricas_map = {
            101: 'vencimentos',
            150: 'gam',
            126: 'titulacao',
            175: 'titulacao',
            141: 'gcet',
            156: 'gcet',
            235: 'gcet',
            136: 'adic_tem_serv',
            212: 'ferias'
        }
        
        # Inicializar categorias
        resultado = {
            'nome': '',
            'matricula': 0,
            'vencimentos': [],
            'gam': [],
            'titulacao': [],
            'gcet': [],
            'adic_tem_serv': [],
            'ferias': []
        }
        
        # Processar cada pagamento
        for pagamento in pagamentos:
            # Extrair informações básicas do primeiro pagamento
            if not resultado['nome'] and 'nome' in pagamento:
                resultado['nome'] = pagamento['nome']
            if not resultado['matricula'] and 'matricula' in pagamento:
                resultado['matricula'] = pagamento['matricula']
            
            # Categorizar por código de rubrica
            cod_rubrica = pagamento.get('codrubrica', 0)
            if cod_rubrica in rubricas_map:
                categoria = rubricas_map[cod_rubrica]
                # Formatear dados para compatibilidade com função existente
                verba_formatada = (
                    pagamento.get('referencia', ''),
                    cod_rubrica,
                    float(pagamento.get('valor', 0))
                )
                resultado[categoria].append(verba_formatada)
        
        return resultado

    def get_dados_calculo_descompressao(self, matricula, data_inicio: date, data_fim: date) -> Optional[Dict[str, Any]]:
        """
        Método principal para obter todos os dados necessários para o cálculo de descompressão.
        
        Args:
            matricula: Matrícula do servidor (int ou string)
            data_inicio: Data de início do período
            data_fim: Data de fim do período
            
        Returns:
            Dados organizados para o cálculo ou None em caso de erro
        """
        try:
            # Buscar dados do servidor
            servidor = self.busca_matricula(matricula)
            if not servidor:
                print(f"❌ Servidor com matrícula {matricula} não encontrado.")
                return None
            
            # Buscar pagamentos do período
            pagamentos = self.busca_pagamentos_periodo(matricula, data_inicio, data_fim)
            if not pagamentos:
                print(f"❌ Nenhum pagamento encontrado para o período.")
                return None
            
            # Processar pagamentos para formato compatível
            dados_processados = self.processar_pagamentos_para_calculo(pagamentos)
            
            # Adicionar informações do servidor
            dados_processados['nome'] = servidor.get('nome', '')
            dados_processados['matricula'] = matricula
            
            print(f"✅ Dados obtidos com sucesso:")
            print(f"   - Servidor: {dados_processados['nome']}")
            print(f"   - Matrícula: {matricula}")
            print(f"   - Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
            print(f"   - Total de pagamentos: {len(pagamentos)}")
            print(f"   - Vencimentos: {len(dados_processados['vencimentos'])}")
            print(f"   - GAM: {len(dados_processados['gam'])}")
            print(f"   - Titulação: {len(dados_processados['titulacao'])}")
            print(f"   - GCET: {len(dados_processados['gcet'])}")
            print(f"   - Adic. Tempo Serviço: {len(dados_processados['adic_tem_serv'])}")
            print(f"   - Férias: {len(dados_processados['ferias'])}")
            
            return dados_processados
            
        except Exception as e:
            print(f"❌ Erro ao obter dados para cálculo: {str(e)}")
            return None

def main():
    """Main program execution"""
    print("\n" + "="*50)
    print("Tentativa da conexão com a API de fichas financeiras")
    print("Henrique Teixeira Advogados Associados")
    print("="*50 + "\n")

    fichas_api = FichasAPI_Manager()

    while True:
        print("\n🔧 Main Menu")
        print("1. Authenticate & Show Token")
        print("2. Pesquise por CPF")
        print("3. Pesquise por Matrícula")
        print("4. Buscar Pagamentos por Período")
        print("5. Teste Completo de Cálculo de Descompressão")
        print("6. Exit")
        
        choice = input("Select option (1-6): ").strip()
        
        if choice == "1":
            if fichas_api.get_auth_token(display_token=True):
                print("✅ Authentication successful!")

        elif choice == "2":
            cpf = input("Insira o CPF a ser pesquisado: ").strip()
            result = fichas_api.busca_cpf(cpf)
            if result:
                print("🔍 Search Results:")
                print("-"*50)
                print(result)
                print("-"*50)
            else:
                print("❌ No results found.")

        elif choice == "3":
            try:
                matricula = int(input("Insira a matrícula a ser pesquisada: ").strip())
                result = fichas_api.busca_matricula(matricula)
                if result:
                    print("🔍 Search Results:")
                    print("-"*50)
                    print(result)
                    print("-"*50)
                else:
                    print("❌ No results found.")
            except ValueError:
                print("❌ Matrícula deve ser um número válido.")

        elif choice == "4":
            try:
                matricula = int(input("Insira a matrícula: ").strip())
                data_inicio_str = input("Data de início (YYYY-MM-DD): ").strip()
                data_fim_str = input("Data de fim (YYYY-MM-DD): ").strip()
                
                # Parse dates
                data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
                data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
                
                result = fichas_api.busca_pagamentos_periodo(matricula, data_inicio, data_fim)
                if result:
                    print("🔍 Pagamentos encontrados:")
                    print("-"*50)
                    print(f"Total de registros: {len(result)}")
                    for i, pagamento in enumerate(result[:5]):  # Show first 5
                        print(f"{i+1}. {pagamento}")
                    if len(result) > 5:
                        print(f"... e mais {len(result) - 5} registros")
                    print("-"*50)
                else:
                    print("❌ No results found.")
            except ValueError as e:
                print(f"❌ Erro nos dados inseridos: {e}")

        elif choice == "5":
            try:
                matricula = int(input("Insira a matrícula: ").strip())
                data_inicio_str = input("Data de início (YYYY-MM-DD): ").strip()
                data_fim_str = input("Data de fim (YYYY-MM-DD): ").strip()
                
                # Parse dates
                data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
                data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
                
                print("\n📊 Executando teste completo...")
                result = fichas_api.get_dados_calculo_descompressao(matricula, data_inicio, data_fim)
                
                if result:
                    print("\n✅ Dados prontos para cálculo de descompressão!")
                    print("="*60)
                else:
                    print("\n❌ Falha ao obter dados para cálculo.")
                    
            except ValueError as e:
                print(f"❌ Erro nos dados inseridos: {e}")

        elif choice == "6":
            print("Goodbye! 👋")
            sys.exit()
            
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
