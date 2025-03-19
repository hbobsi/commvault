
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
API_TOKEN = os.getenv("API_TOKEN")

# Endpoint da API para buscar jobs
url = f'{COMMVAULT_SERVER}/commandcenter/api/Job?completedJobLookupTime=3600'

# Cabeçalhos da requisição
payload={}
headers = {
    'Authtoken': API_TOKEN,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def get_jobs():
    """Busca lista de Jobs na API do Commvault.
    Esta função envia uma solicitação GET para a URL especificada em #Configurações
    para listar os jobs dos últimos 3600 segundos. Ela lida com quaisquer exceções 
    na solicitação e retorna uma lista vazia em caso de erro.
    Returns:
        list: Uma lista de Jobs. Se ocorrer um erro, uma lista vazia será retornada.
    Raises:
        requests.exceptions.RequestException: Se houver um erro durante a solicitação.
    """
    try:
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        jobs = response.json().get("jobs", [])
        return jobs
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar jobs: {e}")
        return []

def parse_jobs(jobs):
    """Analisa a lista de Jobs e conta o número de ocorrências baseado no status do Jobs.
    Args:
        jobs (list of dict): Uma lista de dicionários de jobs, onde cada dicionário contém
                             uma chave 'jobSummary' com um campo 'status' indicando o status 
                             da tarefa.
    Returns:
        dict: Um dicionário contendo as contagens de jobs baseado em seu status com as seguintes chaves:
            - "commvault.failed_jobs": Número de jobs que falharam.
            - "commvault.running_jobs": Número de jobs que estão em execução.
            - "commvault.completed_jobs": Número de jobs que completaram com sucesso.
            - "commvault.queued_jobs": Número de jobs que estão em fila.
            - "commvault.waiting_jobs": Número de jobs que estão aguardando por recurso.
            - "commvault.pending_jobs": Número de jobs que estão pendentes.
    """
    failed_jobs = 0
    running_jobs = 0
    completed_jobs = 0
    queued_jobs = 0
    waiting_jobs = 0
    pending_jobs = 0

    for job in jobs:
        status = job['jobSummary'].get('status')
        if status == 'Completed': 
            completed_jobs += 1
        elif status == 'Failed':
            failed_jobs += 1
        elif status == 'Queued':
            queued_jobs += 1    
        elif status == 'Waiting':
            waiting_jobs += 1
        elif status == 'Running':
            running_jobs += 1
        elif status == 'Pending':
            pending_jobs += 1

    return {
        "commvault.failed_jobs": failed_jobs,
        "commvault.running_jobs": running_jobs,
        "commvault.completed_jobs": completed_jobs,
        "commvault.queued_jobs": queued_jobs,
        "commvault.waiting_jobs": waiting_jobs,
        "commvault.pending_jobs": pending_jobs
    }

def send_to_zabbix(metrics):
    """Enviar métricas coletadas para o Zabbix.
    Esta função pega um dicionário de métricas e envia cada par de chave-valor 
    para o servidor Zabbix usando o executável zabbix_sender. Ele constrói um 
    comando para cada métrica e o executa no shell. Se o comando falhar, uma 
    mensagem de erro é impressa.
    Args:
        metrics (dict): Um dicionário onde as chaves são nomes de métricas e os 
                        valores são os valores de métricas correspondentes a serem 
                        enviados para o Zabbix.
    Raises:
        subprocess.CalledProcessError: Se o comando zabbix_sender falhar na execução.
    """
    for key, value in metrics.items():
        cmd = f'C:\Zabbix\zabbix_sender.exe -z {ZABBIX_SERVER} -s {ZABBIX_HOST} -k {key} -o {value}'
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"Enviado para o Zabbix: {key} = {value}")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao enviar para o Zabbix: {e}")

if __name__ == "__main__":
    jobs = get_jobs()
    if jobs:
        metrics = parse_jobs(jobs)
        send_to_zabbix(metrics)
    else:
        print("Nenhum job encontrado ou erro na API.")
