"""
Módulo: auth_manager.py
-----------------------
Gerencia a autenticação de usuários:
- login (valida credenciais)
- register (cadastro)
- change_password (troca de senha)
Utiliza o werkzeug.security para lidar com hash de senhas.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from modules.database_connection import DatabaseConnection

class AuthManager:
    @staticmethod
    def login_user(usuario, senha):
        """
        Verifica se 'usuario' existe e se a 'senha' corresponde ao hash armazenado.
        Retorna True se login for bem-sucedido, False caso contrário.
        """
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT usuario, senha FROM usuarios WHERE usuario = ?", (usuario,))
            row = cursor.fetchone()
            if row and check_password_hash(row["senha"], senha):
                return True
            return False
        except Exception as e:
            print(f"Erro em login_user: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def register_user(usuario, senha):
        """
        Registra um novo usuário, criptografando a senha.
        Verifica se o usuário já existe. Retorna (True, msg) ou (False, msg).
        """
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Verifica se já existe
            cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario,))
            if cursor.fetchone():
                return False, "Usuário já existe."
            # Criptografa a senha e insere
            senha_hash = generate_password_hash(senha)
            cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", (usuario, senha_hash))
            conn.commit()
            return True, "Usuário registrado com sucesso!"
        except Exception as e:
            print(f"Erro em register_user: {e}")
            return False, "Erro ao registrar usuário."
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def change_password(usuario, nova_senha):
        """
        Altera a senha do 'usuario' para 'nova_senha' (criptografada).
        Retorna (True, msg) ou (False, msg).
        """
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            senha_hash = generate_password_hash(nova_senha)
            cursor.execute("UPDATE usuarios SET senha = ? WHERE usuario = ?", (senha_hash, usuario))
            if cursor.rowcount == 0:
                return False, "Usuário não encontrado."
            conn.commit()
            return True, "Senha atualizada com sucesso!"
        except Exception as e:
            print(f"Erro em change_password: {e}")
            return False, "Erro ao atualizar senha."
        finally:
            cursor.close()
            conn.close()
