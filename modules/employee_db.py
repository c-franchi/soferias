# modules/employee_db.py
import sqlite3
from flask import session

def get_user_connection():
    """
    Retorna uma conexão com o banco de dados específico do usuário,
    cujo caminho está armazenado em session['employee_db'].
    """
    db_path = session.get('employee_db')
    if not db_path:
        raise RuntimeError("Banco de dados do usuário não definido na sessão.")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def create_user_db(db_path):
    """
    Cria (ou atualiza) as tabelas necessárias no banco de dados indicado por db_path.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS areas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        chapa TEXT NOT NULL,
        area_id INTEGER,
        FOREIGN KEY (area_id) REFERENCES areas(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ferias_agendadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funcionario_id INTEGER,
        data_ferias DATE,
        dias_ferias INTEGER,
        FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pedidos_aprovacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapa TEXT NOT NULL,
        dataFerias DATE NOT NULL,
        diasFerias INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDENTE',
        data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()
    print(f"Banco de dados '{db_path}' criado ou atualizado.")

class EmployeeDB:
    """
    Classe para encapsular a obtenção de conexão com o banco de dados específico do usuário.
    Ela utiliza a função get_user_connection definida acima.
    """
    @staticmethod
    def get_connection():
        return get_user_connection()
