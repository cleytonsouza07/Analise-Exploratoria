import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv
import os
from tqdm import tqdm  # Para barra de progresso

load_dotenv()

def carregar_dados_em_blocos(query, project_id, credentials_file, chunk_size=100000):
    try:
        credentials = service_account.Credentials.from_service_account_file(credentials_file)
        client = bigquery.Client(credentials=credentials, project=project_id)

        dados_completos = pd.DataFrame()
        offset = 0
        
        total_rows = client.query(f"SELECT COUNT(*) as total FROM ({query})").to_dataframe().iloc[0]['total']
        total_chunks = total_rows // chunk_size + (1 if total_rows % chunk_size != 0 else 0)

        with tqdm(total=total_chunks, desc="Carregando dados", unit="bloco") as pbar:
            while True:
                paginated_query = f"{query} LIMIT {chunk_size} OFFSET {offset}"
                dados_chunk = client.query(paginated_query).to_dataframe()

                if dados_chunk.empty:
                    break

                dados_completos = pd.concat([dados_completos, dados_chunk], ignore_index=True)
                offset += chunk_size  # Avança o offset para pegar o próximo bloco de dados
                
                pbar.update(1)

        print(f"\nDados carregados com sucesso: {len(dados_completos)} linhas e {len(dados_completos.columns)} colunas.")
        return dados_completos
    except Exception as e:
        print(f"Erro ao carregar os dados: {e}")
        return None

def explorar_dados(dados):
    print("\nResumo dos Dados:")
    print(dados.describe())
    print("\nTipos de Dados:")
    print(dados.dtypes)
    print("\nValores Ausentes:")
    print(dados.isnull().sum())

def tratar_valores_ausentes(dados):
    for coluna in dados.columns:
        if dados[coluna].isnull().sum() > 0:
            if np.issubdtype(dados[coluna].dtype, np.number):
                dados[coluna].fillna(dados[coluna].mean(), inplace=True)
            else:
                if not dados[coluna].mode().empty:
                    dados[coluna].fillna(dados[coluna].mode()[0], inplace=True)
    return dados

def calcular_estatisticas_descritivas(dados):
    estatisticas = dados.describe()
    print(estatisticas)

def visualizar_dados(dados):
    # Gráfico de taxa de sexo com Matplotlib
    sexo_counts = dados['sexo'].value_counts().reset_index()
    sexo_counts.columns = ['sexo', 'count']
    
    plt.figure(figsize=(8, 6))
    sns.barplot(x='sexo', y='count', data=sexo_counts, palette='Set2')
    plt.title('Distribuição de Inscrições por Sexo')
    plt.xlabel('Sexo')
    plt.ylabel('Total de Inscrições')
    plt.show()

    # Gráfico de distribuição por faixa etária
    faixa_etaria_counts = dados['faixa_etaria'].value_counts().reset_index()
    faixa_etaria_counts.columns = ['faixa_etaria', 'count']
    
    plt.figure(figsize=(8, 6))
    sns.barplot(x='faixa_etaria', y='count', data=faixa_etaria_counts, palette='Set3')
    plt.title('Distribuição de Inscrições por Faixa Etária')
    plt.xlabel('Faixa Etária')
    plt.ylabel('Total de Inscrições')
    plt.show()

    # Gráfico de distribuição por tipo de escola
    tipo_escola_counts = dados['sigla_uf_residencia'].value_counts().reset_index()
    tipo_escola_counts.columns = ['sigla_uf_residencia', 'count']
    
    plt.figure(figsize=(8, 6))
    sns.barplot(x='sigla_uf_residencia', y='count', data=tipo_escola_counts, palette='Set1')
    plt.title('Distribuição de Inscrições por Tipo de Escola (UF)')
    plt.xlabel('Tipo de Escola')
    plt.ylabel('Total de Inscrições')
    plt.show()

    # Gráfico de total de inscrições por ano
    dados_agrupados = dados.groupby('ano').size().reset_index(name='total_inscricoes')
    
    plt.figure(figsize=(8, 6))
    sns.lineplot(x='ano', y='total_inscricoes', data=dados_agrupados, marker='o')
    plt.title('Total de Inscrições por Ano')
    plt.xlabel('Ano')
    plt.ylabel('Total de Inscrições')
    plt.show()

def apresentar_resultados():
    print("Análise concluída. Consulte os gráficos e estatísticas descritivas apresentadas.")

def main():

    QUERY = """
    SELECT ano, id_inscricao, faixa_etaria, sexo, id_municipio_residencia, sigla_uf_residencia
    FROM `basedosdados.br_inep_enem.microdados`
    WHERE ano BETWEEN 2018 AND 2022
    """

    PROJECT_ID = os.getenv('id_projeto_cloud_console')
    CREDENTIALS_FILE = os.getenv('arquivo_credenciais_cloud_console')

    dados = carregar_dados_em_blocos(QUERY, PROJECT_ID, CREDENTIALS_FILE)
    if dados is not None:
        explorar_dados(dados)
        dados = tratar_valores_ausentes(dados)
        calcular_estatisticas_descritivas(dados)
        visualizar_dados(dados)
        apresentar_resultados()

if __name__ == "__main__":
    main()
