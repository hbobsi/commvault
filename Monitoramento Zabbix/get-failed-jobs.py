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
ZABBIX_KEY_JOBS = os.getenv("ZABBIX_KEY_MEDIAAGENT")
API_TOKEN = os.getenv("API_TOKEN")

# Endpoint da API para buscar jobs
url = f'{COMMVAULT_SERVER}/commandcenter/api/Job?completedJobLookupTime=14400&jobCategory=Finished&jobFilter=backup,restore&limit=10000'

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

def get_jobs():
    """Consulta informações de Jobs na API do Commvault e filtra os resultados com base no status do Job.
    
    Esta função envia uma solicitação GET para a API do Commvault para buscar informações dos Jobs, processa a resposta e retorna uma lista de Jobs que falharam ou foram concluídos com erros. A lista retornada é formatada em LLD e enviada para o Zabbix.
    
    Returns:
        list: Uma lista de dicionários, cada um contendo detalhes do Job, como ID do Job, status, tipo de job, tipo de backup, nome do client, nome do subclient e motivo da falha. Se nenhum job corresponder aos critérios ou ocorrer um erro durante a solicitação, uma lista vazia será retornada.
    
    Raises:
        requests.exceptions.RequestException: Se houver um erro durante a solicitação da API.
    """
    try:
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        data = response.json()
        lld_jobs = []
        for job in data.get("jobs", []):
            job_summary = job.get("jobSummary", {})
            localized_status = job_summary.get("localizedStatus", "")
            
            if localized_status in ["Failed", "Completed with one or more errors"]:
                lld_jobs.append({
                    "{#JOBID}": str(job_summary.get("jobId")),
                    "{#LOCALIZEDSTATUS}": localized_status,
                    "{#JOBTYPE}": job_summary.get("jobType"),
                    "{#BACKUPLEVELNAME}": job_summary.get("backupLevelName"),
                    "{#CLIENTNAME}": job_summary.get("subclient", {}).get("clientName"),
                    "{#INSTANCENAME}": job_summary.get("subclient", {}).get("instanceName"),
                    "{#PENDINGREASON}": str(sanitize_string(job_summary.get("pendingReason")))
                })
        return lld_jobs
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar jobs: {e}")
        return []

def get_job_status(jobs):
    """Consulta o status dos Jobs e os envia para o Zabbix.
    
    Esta função iterage com uma lista de jobs, extrai o ID do Job e seu status e envia essas informações para um servidor Zabbix usando o aplicativo zabbix_sender. Se ocorrer um erro durante o processo de envio, ele registra uma mensagem de erro e retorna uma lista vazia. No caso de uma exceção de solicitação, ele também registra o erro e retorna uma lista vazia.
    
    Args:
        jobs (list): Uma lista de dicionários, onde cada dicionário contém informações sobre o job, incluindo o ID do job e o status.
    """
    try:
        for job in jobs:
            job_id = job["{#JOBID}"]
            localized_status = job["{#LOCALIZEDSTATUS}"]
            cmd = f'C:\Zabbix\zabbix_sender.exe -z {ZABBIX_SERVER} -s {ZABBIX_HOST} -k status.job[{job_id}] -o "{localized_status}"'
            try:
                subprocess.run(cmd, shell=True, capture_output=True, check=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"Erro ao enviar para o Zabbix: {e}")
                return []
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar Status Jobs: {e}")
        return []

def send_to_zabbix(jobs):
    """Envia dados de Jobs para o Zabbix usando o aplicativo zabbix_sender.
    
    Esta função constrói um comando para enviar informações de Jobs para um servidor Zabbix usando o aplicativo zabbix_sender. Ele executa o comando em um shell e captura qualquer saída ou erro que possa ocorrer durante a execução.
    
    Args:
        jobs (str): Uma string que representa os dados do Job a serem enviados ao Zabbix.
    
    Raises:
        subprocess.CalledProcessError: Se a execução do comando falhar, uma mensagem de erro será impressa indicando a falha no envio de dados para o Zabbix.
    """
    #cmd = f'echo -e \'"{ZABBIX_SERVER}" custom.discovery.ma "{jobs}" -vv\' | C:\Zabbix\zabbix_sender.exe -z {ZABBIX_SERVER} -s {ZABBIX_HOST} -k {ZABBIX_KEY} -o "{jobs}" -vv'
    cmd = f'C:\Zabbix\zabbix_sender.exe -z {ZABBIX_SERVER} -s {ZABBIX_HOST} -k {ZABBIX_KEY_JOBS} -o "{jobs}"'
    try:
        subprocess.run(cmd, shell=True, capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao enviar para o Zabbix: {e}")

if __name__ == "__main__":
    jobs = get_jobs()
    if jobs:
        send_to_zabbix(jobs)
        time.sleep(10)
        get_job_status(jobs)
    else:
        print("Nenhum job encontrado ou erro na API.")
