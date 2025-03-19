import os
from dotenv import load_dotenv # type: ignore
import requests
import json
import subprocess
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Carregando configurações
load_dotenv()
COMMVAULT_SERVER = os.getenv("COMMVAULT_SERVER")
ZABBIX_SERVER = os.getenv("ZABBIX_SERVER")
ZABBIX_HOST = os.getenv("ZABBIX_HOST")
ZABBIX_KEY_MEDIAAGENT = os.getenv("ZABBIX_KEY_MEDIAAGENT")
API_TOKEN = os.getenv("API_TOKEN")

# Endpoint da API para buscar jobs
url = f'{COMMVAULT_SERVER}/commandcenter/api/V4/mediaAgent'

# Cabeçalhos da requisição
payload={}
headers = {
    'Authtoken': API_TOKEN,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def get_ma():
    """Busca informações dos MediaAgents na API do Commvault.
    
    Esta função envia uma solicitação GET para a API do Commvault para consultar informações dos MediaAgents, processa a resposta e a formata para Low Level Dicovery (LLD) para o Zabbix. Em caso de falha na solicitação, ela manipula a exceção e retorna uma lista vazia.
    
    Returns:
        list: Uma lista de dicionários contendo nomes de exibição dos MediaAgents formatados em LLD, ou uma lista vazia se ocorrer um erro.
    
    Raises:
        requests.exceptions.RequestException: Se houver um erro durante a solicitação da API.
    """
    try:
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        data = json.loads(response.text)
        ma_list = [
            {"displayName":ma["displayName"]}
            for ma in data.get("mediaAgents",[])
        ]
        lld_data = [{'"{#HOSTNAME}"': json.dumps(ma["displayName"])} for ma in ma_list]
        return lld_data
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar MediaAgents: {e}")
        return []

def get_ma_status():
    """Busca o status dos MediaAgents na API do Commvault e formata os dados em uma Low Level Discovery (LLD) para o Zabbix.
    
    Esta função envia uma solicitação GET ao endpoint da API do Commvault para consultar o status dos MediaAgents. Ela processa a resposta para extrair o status de cada MediaAgent, formata-as para LLD e envia os dados para o Zabbix.
    
    Returns:
        list: Uma lista de dicionários contendo o status de cada MediaAgent se a operação for bem-sucedida, ou uma lista vazia em caso de exceção.
    
    Raises:
        requests.exceptions.RequestException: Se houver um erro durante a solicitação da API.
    """
    try:
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        data = json.loads(response.text)
        ma_list = [
            {"displayName":ma["displayName"],"status":ma["status"]}
            for ma in data.get("mediaAgents",[])
        ]
        lld_data = [{"{#HOSTNAME}": json.dumps(ma["displayName"]),"{#STATUS}": json.dumps(ma["status"])} for ma in ma_list]
        for item in lld_data:
            mediaAgent = item.get("{#HOSTNAME}")
            status = item.get("{#STATUS}")
            send_to_zabbix_data(mediaAgent, status)
        return []
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar Status MediaAgents: {e}")
        return []

def send_to_zabbix(mediaagents):
    """Enviar dados do MediaAgent para o servidor Zabbix.
    
    Esta função constrói um comando para enviar informações do MediaAgent para um servidor Zabbix usando o aplicativo `zabbix_sender`. Ele executa o comando em um shell e manipula quaisquer erros que possam ocorrer durante a execução.
    
    Args:
        mediaagents (str): Os dados do MediaAgent a serem enviados ao servidor Zabbix.
    
    Raises:
        subprocess.CalledProcessError: Se a execução do comando falhar.
    """
    cmd = f'echo -e \'"{ZABBIX_SERVER}" custom.discovery.ma "{mediaagents}"\' | C:\Zabbix\zabbix_sender.exe -z {ZABBIX_SERVER} -s {ZABBIX_HOST} -k {ZABBIX_KEY_MEDIAAGENT} -o "{mediaagents}"'
    try:
        subprocess.run(cmd, shell=True, capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao enviar para o Zabbix: {e}")

def send_to_zabbix_data(mediaAgent,status):
    """Envia dados de status dos MediaAgents para o Zabbix usando zabbix_sender.
    
    Esta função constrói um comando para enviar o status de cada MediaAgent para um servidor Zabbix usando o executável zabbix_sender. Ele executa o comando em um shell e manipula quaisquer erros que possam ocorrer durante a execução.
    
    Args:
        mediaAgent (str): Nome do MediaAgent para o qual o status está sendo enviado.
        status (str): Status do MediaAgent a ser enviado ao servidor Zabbix.
    
    Raises:
        subprocess.CalledProcessError: Se a execução do comando falhar.
    
    Returns:
        None
    """
    cmd = f'echo -e \'"{ZABBIX_SERVER}" status.ma[{mediaAgent}] "{status}"\' | C:\Zabbix\zabbix_sender.exe -z {ZABBIX_SERVER} -s {ZABBIX_HOST} -k status.ma[{mediaAgent}] -o "{status}"'
    try:
        subprocess.run(cmd, shell=True, capture_output=True, check=True, text=True)
        print(f"Enviado para o Zabbix: \n'{ZABBIX_SERVER} status.ma[{mediaAgent}] {status}'")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao enviar para o Zabbix: {e}")

if __name__ == "__main__":
    mediaagents = get_ma()
    if mediaagents:
        send_to_zabbix(mediaagents)
        get_ma_status()
    else:
        print("Nenhum MediaAgent encontrado ou erro na API.")
