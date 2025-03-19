
import os
from dotenv import load_dotenv # type: ignore
import time
import requests
import re
import json
import subprocess
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Carregando configurações
load_dotenv()
COMMVAULT_SERVER = os.getenv("COMMVAULT_SERVER")
ZABBIX_SERVER = os.getenv("ZABBIX_SERVER")
ZABBIX_HOST = os.getenv("ZABBIX_HOST")
API_TOKEN = os.getenv("API_TOKEN")

# Cabeçalhos da requisição
payload={}
headers = {
    'Authtoken': API_TOKEN,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def sanitize_string(value):
    if isinstance(value, str):
        return re.sub(r"[^a-zA-Z0-9 _-]", "", value)  # Remove caracteres especiais
    return value[:255]

def get_commcell_license():
    url = f'{COMMVAULT_SERVER}/commandcenter/api/V4/License'
    try:
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        expiryDate = response.json().get("expiryDate")
        key="key.expiryDate"
        try:
            send_to_zabbix(key, expiryDate)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao enviar para o Zabbix: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar informacaoes: {e}")
        return []

def get_commcell_name():
    url = f'{COMMVAULT_SERVER}/commandcenter/api/CommServ'
    try:
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        commCellName = response.json().get("commcell", {}).get("commCellName")
        key="key.commCellName"
        try:
            send_to_zabbix(key, commCellName)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao enviar para o Zabbix: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar informacaoes: {e}")
        return []

def get_commcell_release():
    url = f'{COMMVAULT_SERVER}/commandcenter/api/CommServ'
    try:
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        releaseName = response.json().get("releaseName")
        csVersionInfo = response.json().get("csVersionInfo")
        release = (f"{releaseName} | {csVersionInfo}")
        key="key.release"
        try:
            send_to_zabbix(key, release)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao enviar para o Zabbix: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar informacaoes: {e}")
        return []
    
def get_commcell_health():
    url = f'{COMMVAULT_SERVER}/commandcenter/api/cr/reportsplusengine/datasets/b50b20ed-5fc4-4b4c-f7c4-fc6b84eb35cc/data?cache=true&parameter.commUniId=10000'
    try:
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        valores = {}
        keyGood="key.health-good"
        keyInfo="key.health-info"
        keyWarning="key.health-warning"
        keyCritical="key.health-critical"
        for sublista in response.json().get("records"):
            if sublista[1] == '1_Good':
                valores['Good'] = sublista[2]
            elif sublista[1] == '2_Info':
                valores['Info'] = sublista[2]
            elif sublista[1] == '3_Warning':
                valores['Warning'] = sublista[2]
            elif sublista[1] == '4_Critical':
                valores['Critical'] = sublista[2]
        if 'Good' in valores:
            valor = valores['Good']
            try:
                send_to_zabbix(keyGood, valor)
            except subprocess.CalledProcessError as e:
                print(f"Erro ao enviar para o Zabbix: {e}")
        if 'Info' in valores:
            valor = valores['Info']
            try:
                send_to_zabbix(keyInfo, valor)
            except subprocess.CalledProcessError as e:
                print(f"Erro ao enviar para o Zabbix: {e}")
        if 'Warning' in valores:
            valor = valores['Warning']
            try:
                send_to_zabbix(keyWarning, valor)
            except subprocess.CalledProcessError as e:
                print(f"Erro ao enviar para o Zabbix: {e}")
        if 'Critical' in valores:
            valor = valores['Critical']
            try:
                send_to_zabbix(keyCritical, valor)
            except subprocess.CalledProcessError as e:
                print(f"Erro ao enviar para o Zabbix: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar informacaoes: {e}")
        return []

def send_to_zabbix(key, value):
    """Envia dados de Jobs para o Zabbix usando o aplicativo zabbix_sender.
    
    Esta função constrói um comando para enviar informações de Jobs para um servidor Zabbix usando o aplicativo zabbix_sender. Ele executa o comando em um shell e captura qualquer saída ou erro que possa ocorrer durante a execução.
    
    Args:
        jobs (str): Uma string que representa os dados do Job a serem enviados ao Zabbix.
    
    Raises:
        subprocess.CalledProcessError: Se a execução do comando falhar, uma mensagem de erro será impressa indicando a falha no envio de dados para o Zabbix.
    """
    #cmd = f'echo -e \'"{ZABBIX_SERVER}" custom.discovery.ma "{jobs}" -vv\' | C:\Zabbix\zabbix_sender.exe -z {ZABBIX_SERVER} -s {ZABBIX_HOST} -k {ZABBIX_KEY} -o "{jobs}" -vv'
    cmd = f'C:\Zabbix\zabbix_sender.exe -z {ZABBIX_SERVER} -s {ZABBIX_HOST} -k {key} -o "{value}"'
    try:
        subprocess.run(cmd, shell=True, capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao enviar para o Zabbix: {e}")

if __name__ == "__main__":
    get_commcell_name()
    get_commcell_license()
    get_commcell_release()
    get_commcell_health()
