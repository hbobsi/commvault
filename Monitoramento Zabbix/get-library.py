import os
from dotenv import load_dotenv # type: ignore
import requests
import json
import time
import subprocess
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Carregando configurações
load_dotenv()
COMMVAULT_SERVER = os.getenv("COMMVAULT_SERVER")
ZABBIX_SERVER = os.getenv("ZABBIX_SERVER")
ZABBIX_HOST = os.getenv("ZABBIX_HOST")
ZABBIX_KEY_LIBRARIES = os.getenv("ZABBIX_KEY_LIBRARIES")
API_TOKEN = os.getenv("API_TOKEN")

# Endpoint da API para buscar Libraries
BASE_URL = f'{COMMVAULT_SERVER}/commandcenter/api/Library'

# Cabeçalhos da requisição
payload={}
headers = {
    'Authtoken': API_TOKEN,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def get_libraries():
    """Busca uma lista de Libraries na API do Commvault e formata os dados em uma Low Level Discovery (LLD) para o Zabbix.
    
    Esta função envia uma solicitação GET ao endpoint da API do Commvault, processa a resposta para extrair informações das Libraries e a formata em uma estrutura adequada para o LLD do Zabbix.
    
    Returns:
        list: Uma lista de dicionários contendo o nome das Libraries formatados para uma LLD, onde cada dicionário tem a chave '"{#LIBRARYNAME}"' e o nome da biblioteca correspondente como valor. Se ocorrer um erro durante a solicitação, uma lista vazia é retornada.
    
    Raises:
        requests.exceptions.RequestException: Se houver um problema com a solicitação da API.
    """
    try:
        response = requests.request("GET", BASE_URL, headers=headers, data=payload, verify=False)
        data = json.loads(response.text)
        json_array = [entry['entityInfo'] for entry in data['response']]
        lld_data = [{'"{#LIBRARYNAME}"': json.dumps(ma["name"])} for ma in json_array]
        return lld_data
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar MediaAgents: {e}")
        return []
    
def get_libraries_status():
    """Consulta as métricas das Libraries do Commvault através de requisição na API e as envia para o Zabbix.
    
    Esta função faz uma solicitação GET para a URL base para buscar uma lista de IDs de Library. Para cada ID, ela consulta informações detalhadas sobre a Library, incluindo seu nome e métricas. As métricas são então padronizadas e enviadas ao Zabbix para monitoramento.
    
    Args:
        None
    
    Returns:
        None
    
    Raises:
        None
    """
    response = requests.request("GET", BASE_URL, headers=headers, data=payload, verify=False)
    response_data = json.loads(response.text)
    ids = [item["entityInfo"]["id"] for item in response_data["response"]]
    final_results = []
    for library_id in ids:
        url = f"{BASE_URL}/{library_id}"
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        if response.status_code == 200:
            data = response.json()
            library_info = {
                "libraryName": data["libraryInfo"]["library"]["libraryName"],
                "magLibSummary": data["libraryInfo"]["magLibSummary"]
            }
            final_results.append(library_info)
        else:
            print(f"Erro ao buscar ID {library_id}: {response.status_code}")
    for library in final_results:
        library_name = library["libraryName"]
        summary = library["magLibSummary"]
        # Criar chave para cada métrica e adicionar à lista
        for key, value in summary.items():
            # Normalizar a chave (removendo espaços e caracteres especiais)
            key_normalized = key.replace(" ", "_").lower()
            send_to_zabbix_data(key_normalized, library_name, value)

def send_to_zabbix(libraries):
    """Envia uma lista de Libraries para o Zabbix usando o comando zabbix_sender.
    
    Esta função constrói um comando para enviar dados de LLD para o Zabbix. Ela utiliza o módulo `subprocess` para executar o comando em um ambiente shell. Se o comando falhar, uma mensagem de erro será impressa.
    
    Args:
        libraries (str): Uma string que apresenta todas as Libraries a serem enviadas ao Zabbix.
    
    Raises:
        subprocess.CalledProcessError: Se a execução do comando falhar.
    """
    cmd = f'echo -e \'"{ZABBIX_SERVER}" custom.discovery.ma "{libraries}"\' | C:\Zabbix\zabbix_sender.exe -z {ZABBIX_SERVER} -s {ZABBIX_HOST} -k {ZABBIX_KEY_LIBRARIES} -o "{libraries}"'
    try:
        subprocess.run(cmd, shell=True, capture_output=True, check=True, text=True)
        #print(f"Enviado para o Zabbix: \n{ZABBIX_KEY} = {mediaagents}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao enviar para o Zabbix: {e}")

def send_to_zabbix_data(key_normalized,library_name,value):
    """Envia dados para o Zabbix usando zabbix_sender.
    
    Esta função constrói um comando para enviar um valor especificado para um servidor Zabbix para uma chave e nome de library fornecidos. Ele executa o comando usando o módulo subprocess e manipula quaisquer erros que possam ocorrer durante a execução.
    
    Args:
        key_normalized (str): Padroniza a chave para o item Zabbix.
        library_name (str): O nome da library associada à chave.
        value (str): Valor a ser enviado para o servidor Zabbix.
    
    Raises:
        subprocess.CalledProcessError: Se a execução do comando falhar.
    
    Returns:
        None
    """
    cmd = f'echo -e \'"{ZABBIX_SERVER}" {key_normalized}.library[{library_name}] "{value}"\' | C:\Zabbix\zabbix_sender.exe -z {ZABBIX_SERVER} -s {ZABBIX_HOST} -k {key_normalized}.library[{library_name}] -o "{value}"'
    try:
        subprocess.run(cmd, shell=True, capture_output=True, check=True, text=True)
        print(f"Enviado para o Zabbix: \n'{ZABBIX_SERVER} {key_normalized}.library[{library_name}]:{value}'")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao enviar para o Zabbix: {e}")
if __name__ == "__main__":
    libraries = get_libraries()
    if libraries:
        send_to_zabbix(libraries)
    else:
        print("Nenhuma Library encontrada ou erro na API.")
    time.sleep(10)
    get_libraries_status()