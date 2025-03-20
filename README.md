# Commvault Monitoring Scripts

Este repositório contém scripts Python para monitorar ambientes Commvault e integrar com o Zabbix.

## Descrição

Os scripts coletam várias métricas e informações de um CommCell Commvault e as enviam para um servidor Zabbix para monitoramento e alertas.

## Scripts

* `get-commcell-info.py`: Coleta informações gerais do CommCell (nome, licença, versão, saúde) e envia para o Zabbix.
* `get-failed-jobs.py`: Coleta informações sobre jobs com falha no Commvault e envia para o Zabbix para monitoramento e alertas.
* `get-jobs.py`: Coleta informações sobre o status dos Jobs (concluídos, falha, etc) e envia para o Zabbix.
* `get-library.py`: Coleta informações sobre as Libraries (descobre e monitora métricas) e envia para o Zabbix.
* `get-ma.py`: Coleta informações sobre os MediaAgents (descobre e monitora status) e envia para o Zabbix.

## Pré-requisitos

* Python 3.6+
* Bibliotecas Python:
    * `requests`
    * `python-dotenv`
    * `urllib3`
* Acesso à API do Commvault
* Servidor Zabbix com o Zabbix Sender instalado
* Variáveis de ambiente configuradas:
    * `COMMVAULT_SERVER`: URL do servidor Commvault (ex: `https://seu-servidor-commvault`)
    * `ZABBIX_SERVER`: Endereço do servidor Zabbix
    * `ZABBIX_HOST`: Nome do host Zabbix para identificar o CommCell
    * `API_TOKEN`: Token de autenticação para a API do Commvault
    * `ZABBIX_KEY_JOBS`: Chave do Zabbix para os Jobs
    * `ZABBIX_KEY_MEDIAAGENT`: Chave do Zabbix para MediaAgents
    * `ZABBIX_KEY_LIBRARIES`: Chave do Zabbix para Libraries

## Instalação

1.  Clone este repositório:
    ```bash
    git clone https://github.com/hbobsi/commvault.git
    ```
2.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
3.  Copie o arquivo `.env.example` para `.env` e configure as variáveis de ambiente.
4.  Configure o Zabbix para receber os dados (crie itens, hosts, etc).
5.  Agende a execução dos scripts (ex: com `cron` no Linux ou Agendador de Tarefas no Windows).

## Uso

Para executar um script individualmente:

```bash
python get-commcell-info.py