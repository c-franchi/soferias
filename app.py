"""
Arquivo: app.py
---------------
Este é o arquivo principal da aplicação Flask.
Contém as rotas para:
  - Login (/login)
  - Logout (/logout)
  - Registro (/register)
  - Troca de Senha (/trocar_senha)
  - Perfil (/profile) – com upload de foto e planilha
  - Marcar Férias (/marcar_ferias) – página para agendamento
  - Buscar Funcionário (/buscar_funcionario) – consulta ao banco de funcionários
  - Verificar Agendamento (/verificar_agendamento) – consulta agendamento
  - Agendar Férias (/agendar_ferias) – agendamento com verificação de conflitos
  - Cancelar Agendamento (/cancelar_agendamento) – cancela o agendamento
  - Alterar Agendamento (/alterar_agendamento) – altera o agendamento
  - Solicitar Aprovação (/solicitar_aprovacao) – insere pedido de aprovação
  - Dashboard (/dashboard, /dashboard_data, /aprovar_pedido, /excluir_agendamentos)
  - Relatório (/relatorio, /gerar_pdf) – exibe e exporta relatório
A aplicação utiliza os módulos:
  - modules/database_connection.py (para autenticação: app.db)
  - modules/auth_manager.py
  - modules/employee_db.py (para consultas ao banco setores_funcionarios.db)
  - modules/dashboard_manager.py
"""

import os
import sqlite3
import io
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    make_response,
)
from werkzeug.utils import secure_filename
from xhtml2pdf import pisa
from modules.employee_db import EmployeeDB
from modules.database_connection import init_db
from modules.auth_manager import AuthManager
from modules.dashboard_manager import DashboardManager
from modules.employee_db import EmployeeDB
from datetime import datetime
from jinja2 import Undefined
import re


# Definição da função para converter HTML em PDF (definida inline para evitar problemas de importação)
def html_to_pdf(source_html):
    result = io.BytesIO()
    # Usa StringIO para converter o HTML (string) em um stream para o pisa
    pdf = pisa.CreatePDF(io.StringIO(source_html), dest=result)
    if not pdf.err:
        return result.getvalue()
    return None


# Criação da aplicação Flask e configuração da chave secreta
app = Flask(__name__)
if os.environ.get("FLASK_ENV") == "production":
    key = os.environ.get("FLASK_SECRET_KEY")
    if not key:
        raise RuntimeError("FLASK_SECRET_KEY não definido em produção.")
    app.secret_key = key
else:
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "DEV_ONLY__troque_isto")

# Limite de tamanho de upload (exemplo: 2MB)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB

# Extensões permitidas para upload de fotos e planilhas
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXCEL_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# Inicializa o banco de usuários (app.db)
init_db()

# Configuração da pasta para uploads (ex.: fotos de perfil)
UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "uploads", "profile_pics")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.template_filter("to_br_date")
def to_br_date(date_str, format="%d/%m/%Y"):
    """
    Converte uma string de data do formato ISO (YYYY-MM-DD) para o formato brasileiro (DD/MM/YYYY).
    Se a data estiver vazia ou for inválida, retorna a string original.
    """
    if not date_str or isinstance(date_str, Undefined):
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime(format)
    except Exception as e:
        return date_str


# ------------------------------------------------------------
# ROTA INICIAL
# ------------------------------------------------------------
@app.route("/")
def index():
    """
    Redireciona o usuário para a página de login.
    """
    return redirect(url_for("login"))


# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Requisição inválida."), 400
    usuario = data.get("usuario")
    senha = data.get("senha")
    if not usuario or not senha:
        return jsonify(success=False, message="Usuário e senha são obrigatórios."), 400
    if AuthManager.login_user(usuario, senha):
        session["logged_in"] = True
        session["usuario"] = usuario

        # Define o arquivo de banco de dados exclusivo para este usuário
        safe_user = re.sub(r'[^a-zA-Z0-9_-]+', '_', usuario)
        db_filename = f"gestor_{safe_user}_funcionarios.db"
        session["employee_db"] = db_filename

        # Se o arquivo de banco não existir, cria as tabelas necessárias
        from modules.employee_db import create_user_db
        import os

        if not os.path.exists(db_filename):
            create_user_db(db_filename)

        return jsonify(success=True, message="Login bem-sucedido!")
    else:
        return jsonify(success=False, message="Credenciais inválidas."), 401


# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------
@app.route("/logout")
def logout():
    """
    Limpa a sessão do usuário e redireciona para /login.
    """
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------------------
# REGISTRO DE USUÁRIOS
# ------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    """
    GET: Renderiza o template register.html.
    POST: Recebe (usuario, senha) via JSON e cadastra o usuário via AuthManager.
    """
    if request.method == "GET":
        return render_template("register.html")
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Requisição inválida."), 400
    usuario = data.get("usuario")
    senha = data.get("senha")
    if not usuario or not senha:
        return jsonify(success=False, message="Dados incompletos."), 400
    success, message = AuthManager.register_user(usuario, senha)
    status_code = 200 if success else 409
    return jsonify(success=success, message=message), status_code


# ------------------------------------------------------------
# TROCA DE SENHA
# ------------------------------------------------------------
@app.route("/trocar_senha", methods=["GET", "POST"])
def trocar_senha():
    """
    GET: Renderiza o template trocar_senha.html.
    POST: Recebe nova_senha via JSON e atualiza a senha do usuário logado.
    """
    if request.method == "GET":
        return render_template("trocar_senha.html")
    if "usuario" not in session:
        return jsonify(success=False, message="Usuário não está logado."), 401
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Requisição inválida."), 400
    nova_senha = data.get("nova_senha")
    if not nova_senha:
        return jsonify(success=False, message="Nova senha é obrigatória."), 400
    success, message = AuthManager.change_password(session["usuario"], nova_senha)
    status_code = 200 if success else 500
    return jsonify(success=success, message=message), status_code


# ------------------------------------------------------------
# PERFIL DO USUÁRIO
# ------------------------------------------------------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    """
    GET: Renderiza o template profile.html com informações do usuário.
    POST: Processa o upload de arquivos (foto de perfil e/ou planilha) e atualiza as configurações.
    Em caso de erro, loga a exceção e retorna a mensagem para o cliente.
    """
    if request.method == "GET":
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return render_template(
            "profile.html",
            profile_pic_path=session.get("profile_pic"),
            usuario=session.get("usuario"),
        )

    if "usuario" not in session:
        return jsonify(success=False, message="Usuário não logado."), 401

    try:
        response_data = {}
        # Processa o upload da foto de perfil
        if "profilePicUpload" in request.files:
            file = request.files["profilePicUpload"]
            if file.filename != "" and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                profile_pic_url = url_for(
                    "static", filename=f"uploads/profile_pics/{filename}"
                )
                response_data["profilePicUrl"] = profile_pic_url
                session["profile_pic"] = profile_pic_url
            elif file.filename != "":
                return jsonify(success=False, message="Extensão de imagem não permitida."), 400

        # Processa o upload da planilha e importa os dados
        if "uploadPlanilha" in request.files:
            file = request.files["uploadPlanilha"]
            if file.filename != "" and allowed_file(file.filename, ALLOWED_EXCEL_EXTENSIONS):
                planilha_folder = os.path.join(
                    os.getcwd(), "static", "uploads", "planilhas"
                )
                if not os.path.exists(planilha_folder):
                    os.makedirs(planilha_folder)
                planilha_filename = secure_filename(file.filename)
                planilha_path = os.path.join(planilha_folder, planilha_filename)
                file.save(planilha_path)
                from modules.planilha_processor import process_planilha

                process_message = process_planilha(planilha_path)
                response_data["planilhaStatus"] = process_message
            elif file.filename != "":
                return jsonify(success=False, message="Extensão de planilha não permitida."), 400

        response_data["message"] = "Configurações salvas com sucesso."
        return jsonify(response_data)
    except Exception as e:
        app.logger.error("Erro no processamento do perfil: %s", e)
        return jsonify(success=False, message=str(e)), 500


# ------------------------------------------------------------
# MARCAR FÉRIAS – AGENDAMENTO
# ------------------------------------------------------------
@app.route("/marcar_ferias", methods=["GET"])
def marcar_ferias():
    """
    Renderiza o template marcar_ferias.html para agendamento de férias.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("marcar_ferias.html")


# ------------------------------------------------------------
# BUSCAR FUNCIONÁRIO (setores_funcionarios.db)
# ------------------------------------------------------------
@app.route("/buscar_funcionario", methods=["GET"])
def buscar_funcionario():
    chapa = request.args.get("chapa")
    if not chapa:
        return jsonify(nome=None)

    from modules.employee_db import get_user_connection

    conn = get_user_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT f.nome, a.nome AS area
        FROM funcionarios f
        LEFT JOIN areas a ON f.area_id = a.id
        WHERE f.chapa = ?
    """,
        (chapa,),
    )
    funcionario = cursor.fetchone()
    cursor.close()
    conn.close()

    if funcionario:
        return jsonify(nome=funcionario["nome"], area=funcionario["area"])
    else:
        return jsonify(nome=None)


# ------------------------------------------------------------
# VERIFICAR AGENDAMENTO (setores_funcionarios.db)
# ------------------------------------------------------------
@app.route("/verificar_agendamento", methods=["GET"])
def verificar_agendamento():
    """
    Verifica se o funcionário (pela chapa) já possui um agendamento.
    Retorna JSON: { agendado: True, dataFerias, dataRetorno } se existir.
    """
    chapa = request.args.get("chapa")
    if not chapa:
        return jsonify(agendado=False)
    conn = EmployeeDB.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM funcionarios WHERE chapa = ?", (chapa,))
    funcionario = cursor.fetchone()
    if funcionario:
        funcionario_id = funcionario["id"]
        cursor.execute(
            "SELECT data_ferias, dias_ferias FROM ferias_agendadas WHERE funcionario_id = ?",
            (funcionario_id,),
        )
        agendamento = cursor.fetchone()
        if agendamento:
            from datetime import datetime, timedelta

            dataFerias = agendamento["data_ferias"]
            diasFerias = int(agendamento["dias_ferias"])
            dataFerias_dt = datetime.strptime(dataFerias, "%Y-%m-%d")
            dataRetorno_dt = dataFerias_dt + timedelta(days=diasFerias)
            cursor.close()
            conn.close()
            return jsonify(
                agendado=True,
                dataFerias=dataFerias,
                dataRetorno=dataRetorno_dt.strftime("%Y-%m-%d"),
            )
    cursor.close()
    conn.close()
    return jsonify(agendado=False)


# ------------------------------------------------------------
# AGENDAR FÉRIAS
# ------------------------------------------------------------
@app.route("/agendar_ferias", methods=["POST"])
def agendar_ferias():
    """
    Rota: /agendar_ferias
    - Recebe JSON com 'chapa', 'dataFerias' e 'diasFerias'.
    - Verifica se o funcionário já possui um agendamento (não pode agendar duas vezes).
    - Verifica se há conflito: nenhum outro funcionário da mesma área pode ter férias que se sobreponham.
    Se houver conflito, retorna { conflito: true } para que o usuário solicite aprovação.
    - Caso contrário, insere o agendamento e retorna success=True.
    """
    data = request.get_json()
    chapa = data.get("chapa")
    dataFerias = data.get("dataFerias")
    try:
        diasFerias = int(data.get("diasFerias"))
    except:
        return jsonify(success=False, message="Dias de férias inválidos."), 400

    if not chapa or not dataFerias or not diasFerias:
        return jsonify(success=False, message="Dados incompletos."), 400

    from datetime import datetime, timedelta

    try:
        start_date = datetime.strptime(dataFerias, "%Y-%m-%d").date()
    except Exception as e:
        return jsonify(success=False, message="Data inválida."), 400
    end_date = start_date + timedelta(days=diasFerias)

    # Usa a conexão do banco de dados específico do usuário (gestor)
    from modules.employee_db import get_user_connection

    conn = get_user_connection()
    cursor = conn.cursor()

    # Busca o funcionário pela chapa
    cursor.execute("SELECT id, area_id FROM funcionarios WHERE chapa = ?", (chapa,))
    funcionario = cursor.fetchone()
    if not funcionario:
        cursor.close()
        conn.close()
        return jsonify(success=False, message="Funcionário não encontrado."), 404
    funcionario_id = funcionario["id"]
    area_id = funcionario["area_id"]

    # Verifica se o funcionário já possui um agendamento
    cursor.execute(
        "SELECT id FROM ferias_agendadas WHERE funcionario_id = ?", (funcionario_id,)
    )
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return (
            jsonify(
                success=False,
                message="Você já possui férias agendadas. Utilize alterar ou cancelar.",
            ),
            409,
        )

    # Verifica conflitos: Se outro funcionário da mesma área tiver agendamento sobreposto
    cursor.execute(
        """
        SELECT f.nome, fa.data_ferias, fa.dias_ferias 
        FROM ferias_agendadas fa
        JOIN funcionarios f ON fa.funcionario_id = f.id
        WHERE f.area_id = ?
        AND (date(fa.data_ferias) <= ? AND date(fa.data_ferias, '+' || fa.dias_ferias || ' days') >= ?)
    """,
        (area_id, end_date.isoformat(), start_date.isoformat()),
    )
    conflict = cursor.fetchone()
    if conflict:
        conflict_name = conflict["nome"]
        conflict_start = conflict["data_ferias"]
        conflict_days = int(conflict["dias_ferias"])
        conflict_end = (
            datetime.strptime(conflict_start, "%Y-%m-%d").date()
            + timedelta(days=conflict_days)
        ).isoformat()
        cursor.close()
        conn.close()
        return (
            jsonify(
                success=False,
                conflito=True,
                nome=conflict_name,
                dataFerias=conflict_start,
                dataRetorno=conflict_end,
                message="Conflito: Outro funcionário do seu setor já está agendado para um período que se sobrepõe. Solicite aprovação.",
            ),
            409,
        )

    # Se não houver conflito, insere o novo agendamento
    cursor.execute(
        "INSERT INTO ferias_agendadas (funcionario_id, data_ferias, dias_ferias) VALUES (?, ?, ?)",
        (funcionario_id, dataFerias, diasFerias),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify(success=True, message="Férias agendadas com sucesso.")


# ------------------------------------------------------------
# CANCELAR AGENDAMENTO
# ------------------------------------------------------------
@app.route("/cancelar_agendamento", methods=["POST"])
def cancelar_agendamentos():
    """
    Recebe JSON com 'chapa' e remove o agendamento do funcionário.
    """
    data = request.get_json()
    chapa = data.get("chapa")
    if not chapa:
        return jsonify(success=False, message="Dados incompletos."), 400
    conn = EmployeeDB.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM funcionarios WHERE chapa = ?", (chapa,))
    funcionario = cursor.fetchone()
    if not funcionario:
        cursor.close()
        conn.close()
        return jsonify(success=False, message="Funcionário não encontrado."), 404
    funcionario_id = funcionario["id"]
    cursor.execute(
        "DELETE FROM ferias_agendadas WHERE funcionario_id = ?", (funcionario_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify(success=True, message="Agendamento cancelado com sucesso.")


# ------------------------------------------------------------
# ALTERAR AGENDAMENTO
# ------------------------------------------------------------
@app.route("/alterar_agendamento", methods=["POST"])
def alterar_agendamento():
    """
    Rota: /alterar_agendamento
    - Recebe JSON com 'chapa', 'dataFerias' e 'diasFerias'.
    - Verifica se o funcionário possui um agendamento existente.
    - Se existir, atualiza o registro com os novos dados e retorna success=True.
    - Caso contrário, retorna erro informando que não há agendamento para alterar.
    """
    data = request.get_json()
    chapa = data.get("chapa")
    dataFerias = data.get("dataFerias")
    diasFerias = data.get("diasFerias")

    if not chapa or not dataFerias or not diasFerias:
        return jsonify(success=False, message="Dados incompletos."), 400

    from modules.employee_db import get_user_connection

    conn = get_user_connection()
    cursor = conn.cursor()

    # Busca o funcionário pela chapa
    cursor.execute("SELECT id FROM funcionarios WHERE chapa = ?", (chapa,))
    funcionario = cursor.fetchone()
    if not funcionario:
        cursor.close()
        conn.close()
        return jsonify(success=False, message="Funcionário não encontrado."), 404
    funcionario_id = funcionario["id"]

    # Verifica se há um agendamento para esse funcionário
    cursor.execute(
        "SELECT id FROM ferias_agendadas WHERE funcionario_id = ?", (funcionario_id,)
    )
    agendamento = cursor.fetchone()
    if not agendamento:
        cursor.close()
        conn.close()
        return (
            jsonify(
                success=False, message="Nenhum agendamento encontrado para alteração."
            ),
            404,
        )

    # Atualiza o agendamento com os novos dados
    cursor.execute(
        "UPDATE ferias_agendadas SET data_ferias = ?, dias_ferias = ? WHERE funcionario_id = ?",
        (dataFerias, diasFerias, funcionario_id),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify(success=True, message="Agendamento alterado com sucesso.")


# ------------------------------------------------------------
# LISTAR AGENDAMENTO
# ------------------------------------------------------------

@app.route('/listar_agendamentos', methods=['GET'])
def listar_agendamentos():
    from modules.employee_db import get_user_connection
    conn = get_user_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.chapa, f.nome, a.nome AS area, fa.data_ferias, fa.dias_ferias,
               date(fa.data_ferias, '+' || fa.dias_ferias || ' days') AS data_retorno
        FROM ferias_agendadas fa
        JOIN funcionarios f ON fa.funcionario_id = f.id
        JOIN areas a ON f.area_id = a.id
        ORDER BY fa.data_ferias
    """)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            "chapa": row["chapa"],
            "nome": row["nome"],
            "area": row["area"],
            "dataFerias": row["data_ferias"],
            "diasFerias": row["dias_ferias"],
            "data_retorno": row["data_retorno"]
        })
    cursor.close()
    conn.close()
    return jsonify(result)


# ------------------------------------------------------------
# SOLICITAR APROVAÇÃO
# ------------------------------------------------------------
@app.route("/solicitar_aprovacao", methods=["POST"])
def solicitar_aprovacao():
    if not session.get("logged_in"):
        return jsonify(success=False, message="Não autorizado"), 401
    data = request.get_json()
    chapa = data.get("chapa")
    dataFerias = data.get("dataFerias")
    diasFerias = data.get("diasFerias")
    try:
        conn = EmployeeDB.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO pedidos_aprovacao (chapa, dataFerias, diasFerias, status, data_pedido)
            VALUES (?, ?, ?, 'PENDENTE', datetime('now'))
        """,
            (chapa, dataFerias, diasFerias),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify(
            success=True, message="Pedido de aprovação enviado ao supervisor."
        )
    except Exception as e:
        print("Erro ao solicitar aprovação:", e)
        return jsonify(success=False, message=str(e)), 500


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------
@app.route("/dashboard", methods=["GET"])
def dashboard():
    """
    Renderiza o dashboard com os dados obtidos pelo DashboardManager.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    data = DashboardManager.get_dashboard_data()
    return render_template(
        "dashboard.html",
        total_agendamentos=data["total_agendamentos"],
        pedidos_aprovacao=data["pedidos_aprovacao"],
        profile_pic_path=session.get("profile_pic"),
    )


# ------------------------------------------------------------
# DADOS DO DASHBOARD (JSON)
# ------------------------------------------------------------
@app.route("/dashboard_data", methods=["GET"])
def dashboard_data():
    """
    Retorna os dados do dashboard em formato JSON.
    Inclui labels (meses), datasets (dados agrupados por área), total_agendamentos e pedidos_aprovacao.
    """
    if not session.get("logged_in"):
        return jsonify(success=False, message="Não autorizado"), 401
    data = DashboardManager.get_dashboard_data()
    return jsonify(
        labels=data["labels"],
        datasets=data["datasets"],
        total_agendamentos=data["total_agendamentos"],
        pedidos_aprovacao=data["pedidos_aprovacao"],
    )


# ------------------------------------------------------------
# APROVAR/REJEITAR PEDIDOS
# ------------------------------------------------------------
@app.route("/aprovar_pedido", methods=["POST"])
def aprovar_pedido():
    if not session.get("logged_in"):
        return jsonify(success=False, message="Não autorizado"), 401
    data = request.get_json()
    pedido_id = data.get("pedido_id")
    acao = data.get("acao")
    if acao == "aprovar":
        result = DashboardManager.aprovar_pedido(pedido_id)
    else:
        result = DashboardManager.rejeitar_pedido(pedido_id)
    if result:
        return jsonify(success=True)
    else:
        return jsonify(success=False), 500


# ------------------------------------------------------------
# EXCLUIR TODOS OS AGENDAMENTOS
# ------------------------------------------------------------
@app.route("/excluir_agendamentos", methods=["POST"])
def excluir_agendamentos():
    if not session.get("logged_in"):
        return jsonify(success=False, message="Não autorizado"), 401
    result = DashboardManager.excluir_agendamentos()
    if result:
        return jsonify(success=True)
    else:
        return jsonify(success=False), 500


# ------------------------------------------------------------
# RELATÓRIO
# ------------------------------------------------------------
@app.route("/relatorio")
def relatorio():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = EmployeeDB.get_connection()
    cursor = conn.cursor()

    # Funcionários em período de férias (data_ferias <= hoje <= data_ferias + dias_ferias)
    cursor.execute(
        """
        SELECT f.chapa, f.nome, fa.data_ferias, fa.dias_ferias,
               date(fa.data_ferias, '+' || fa.dias_ferias || ' days') AS data_retorno
        FROM ferias_agendadas fa
        JOIN funcionarios f ON fa.funcionario_id = f.id
        WHERE date(fa.data_ferias) <= date('now')
          AND date(fa.data_ferias, '+' || fa.dias_ferias || ' days') >= date('now')
    """
    )
    em_ferias_rows = cursor.fetchall()
    # Transforma em lista de tuplas (ou use como preferir)
    em_ferias = []
    for row in em_ferias_rows:
        em_ferias.append(
            (
                row["chapa"],
                row["nome"],
                row["data_ferias"],
                row["dias_ferias"],
                row["data_retorno"],
            )
        )

    # Funcionários com férias agendadas, mas ainda não iniciadas
    cursor.execute(
        """
        SELECT f.chapa, f.nome, fa.data_ferias, fa.dias_ferias,
        date(fa.data_ferias, '+' || fa.dias_ferias || ' days') AS data_retorno
        FROM ferias_agendadas fa
        JOIN funcionarios f ON fa.funcionario_id = f.id
        WHERE date(fa.data_ferias) > date('now')
    """
    )
    agendados_rows = cursor.fetchall()
    agendados = []
    for row in agendados_rows:
        agendados.append(
            (
                row["chapa"],
                row["nome"],
                row["data_ferias"],
                row["dias_ferias"],
                row["data_retorno"],
            )
        )

    cursor.close()
    conn.close()

    return render_template("relatorio.html", em_ferias=em_ferias, agendados=agendados)


# ------------------------------------------------------------
# GERAR PDF
# ------------------------------------------------------------
@app.route("/gerar_pdf")
def gerar_pdf():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = EmployeeDB.get_connection()
    cursor = conn.cursor()

    # Consulta de funcionários em período de férias
    cursor.execute(
        """
        SELECT f.chapa, f.nome, fa.data_ferias, fa.dias_ferias,
        date(fa.data_ferias, '+' || fa.dias_ferias || ' days') as data_retorno
        FROM ferias_agendadas fa
        JOIN funcionarios f ON fa.funcionario_id = f.id
        WHERE date(fa.data_ferias) <= date('now')
        AND date(fa.data_ferias, '+' || fa.dias_ferias || ' days') >= date('now')
    """
    )
    em_ferias_rows = cursor.fetchall()
    em_ferias = []
    for row in em_ferias_rows:
        em_ferias.append(
            (
                row["chapa"],
                row["nome"],
                row["data_ferias"],
                row["dias_ferias"],
                row["data_retorno"],
            )
        )

    # Consulta de funcionários com férias agendadas (futuras)
    cursor.execute(
        """
        SELECT f.chapa, f.nome, fa.data_ferias, fa.dias_ferias,
        date(fa.data_ferias, '+' || fa.dias_ferias || ' days') as data_retorno
        FROM ferias_agendadas fa
        JOIN funcionarios f ON fa.funcionario_id = f.id
        WHERE date(fa.data_ferias) > date('now')
    """
    )
    agendados_rows = cursor.fetchall()
    agendados = []
    for row in agendados_rows:
        agendados.append(
            (
                row["chapa"],
                row["nome"],
                row["data_ferias"],
                row["dias_ferias"],
                row["data_retorno"],
            )
        )

    cursor.close()
    conn.close()

    html = render_template(
        "relatorio_pdf.html", em_ferias=em_ferias, agendados=agendados
    )
    pdf = html_to_pdf(html)
    if pdf:
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            "inline; filename=relatorio_ferias.pdf"
        )
        return response
    else:
        return "Erro ao gerar PDF", 500


# ------------------------------------------------------------
# EXECUÇÃO DO SERVIDOR FLASK
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run()  # Não use debug=True em produção
