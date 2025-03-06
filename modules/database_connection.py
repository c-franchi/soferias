"""
Módulo: database_connection.py
------------------------------
Gerencia a conexão com o banco de dados SQLite.
Cria a tabela de usuários se não existir (init_db).
"""

import sqlite3

class DatabaseConnection:
    DB_NAME = "app.db"  # Nome do arquivo do banco de dados

    @staticmethod
    def get_connection():
        """
        Retorna uma conexão ativa com o banco de dados SQLite.
        row_factory = sqlite3.Row para acessar colunas por nome.
        """
        conn = sqlite3.connect(DatabaseConnection.DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """
    Cria a tabela 'usuarios' se ela não existir.
    Pode ser estendido para criar outras tabelas.
    """
    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()
