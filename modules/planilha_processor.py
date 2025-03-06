"""
Módulo: planilha_processor.py
-----------------------------
Este módulo lê um arquivo Excel com os dados dos funcionários e áreas,
e insere/atualiza esses dados no banco de dados setores_funcionarios.db.

É esperado que a planilha contenha as colunas:
  - 'Área'
  - 'Colaborador'
  - 'Chapa'
"""

import pandas as pd
from modules.employee_db import EmployeeDB

def process_planilha(filepath):
    """
    Lê o arquivo Excel localizado em 'filepath' e atualiza as tabelas 'areas' e 'funcionarios'
    no banco de dados setores_funcionarios.db.

    Para cada linha:
      - Verifica se a área existe; se não, insere a área.
      - Insere ou atualiza o funcionário (nome, chapa, area_id).
    
    Retorna uma mensagem informando que a planilha foi processada com sucesso.
    """
    try:
        # Lê o arquivo Excel
        df = pd.read_excel(filepath)
    except Exception as e:
        return f"Erro ao ler a planilha: {e}"

    # Conectar ao banco de dados de funcionários
    conn = EmployeeDB.get_connection()
    cursor = conn.cursor()

    for index, row in df.iterrows():
        # Extrai os valores (ajuste os nomes das colunas conforme sua planilha)
        area = row['Área']
        nome = row['Colaborador']
        chapa = str(row['Chapa']).strip()

        # Verifica se a área já existe
        cursor.execute("SELECT id FROM areas WHERE nome = ?", (area,))
        area_row = cursor.fetchone()
        if area_row:
            area_id = area_row["id"]
        else:
            cursor.execute("INSERT INTO areas (nome) VALUES (?)", (area,))
            area_id = cursor.lastrowid

        # Verifica se o funcionário já existe (pelo número de chapa)
        cursor.execute("SELECT id FROM funcionarios WHERE chapa = ?", (chapa,))
        func_row = cursor.fetchone()
        if func_row:
            # Atualiza os dados do funcionário
            cursor.execute("UPDATE funcionarios SET nome = ?, area_id = ? WHERE chapa = ?",
                           (nome, area_id, chapa))
        else:
            # Insere o novo funcionário
            cursor.execute("INSERT INTO funcionarios (nome, chapa, area_id) VALUES (?, ?, ?)",
                           (nome, chapa, area_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    return "Planilha processada com sucesso."
