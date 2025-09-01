import requests
from requests.auth import HTTPBasicAuth
from fichas_api_config import api_config
import urllib3
import sys

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
        print("4. Exit")
        
        choice = input("Select option (1-4): ").strip()
        
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

        elif choice == "4":
            print("Goodbye! 👋")
            sys.exit()
            
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
