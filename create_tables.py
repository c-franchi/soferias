import sqlite3

db_path = "setores_funcionarios.db"  # MESMO nome do EmployeeDB

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tabela areas
cursor.execute('''
CREATE TABLE IF NOT EXISTS areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL
)
''')

# Tabela funcionarios
cursor.execute('''
CREATE TABLE IF NOT EXISTS funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    chapa TEXT NOT NULL,
    area_id INTEGER,
    FOREIGN KEY (area_id) REFERENCES areas(id)
)
''')

# Tabela ferias_agendadas
cursor.execute('''
CREATE TABLE IF NOT EXISTS ferias_agendadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    funcionario_id INTEGER,
    data_ferias DATE,
    dias_ferias INTEGER,
    FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
)
''')

# Tabela pedidos_aprovacao
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
print("Tabelas criadas ou atualizadas com sucesso!")
