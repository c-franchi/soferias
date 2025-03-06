"""
Módulo: dashboard_manager.py
----------------------------
Centraliza a lógica do Dashboard, consultando o banco setores_funcionarios.db
para:
  - Obter os agendamentos de férias agrupados por mês e por área,
    retornando também detalhes dos funcionários (nome e dias de férias) para tooltips.
  - Buscar os pedidos de aprovação pendentes.
  - Aprovar um pedido: insere o registro em ferias_agendadas e atualiza o status do pedido.
  - Rejeitar um pedido: atualiza o status para "REJEITADO".
  - Excluir todos os agendamentos.
"""

from modules.employee_db import EmployeeDB
from datetime import datetime, timedelta

class DashboardManager:
    @staticmethod
    def get_dashboard_data():
        conn = EmployeeDB.get_connection()
        cursor = conn.cursor()

        # Consulta: agrupa os agendamentos por mês e por área, incluindo área_id
        cursor.execute("""
            SELECT strftime('%Y-%m', fa.data_ferias) AS mes, a.nome AS area, a.id as area_id, COUNT(*) AS count
            FROM ferias_agendadas fa
            JOIN funcionarios f ON fa.funcionario_id = f.id
            JOIN areas a ON f.area_id = a.id
            GROUP BY mes, a.nome
        """)
        rows = cursor.fetchall()

        # Extrai os meses únicos (ordenados) e informações das áreas
        meses = sorted({row["mes"] for row in rows})
        area_info = {}
        for row in rows:
            area_name = row["area"]
            if area_name not in area_info:
                area_info[area_name] = row["area_id"]
        areas = sorted(list(area_info.keys()))

        # Definir cores para cada área (ciclo de cores se necessário)
        colors = [
            "rgba(75, 192, 192, 0.5)",
            "rgba(255, 206, 86, 0.5)",
            "rgba(153, 102, 255, 0.5)",
            "rgba(54, 030, 235, 0.5)",
            "rgba(255, 159, 64, 0.5)"
        ]

        # Monta os datasets para o gráfico: para cada área, para cada mês,
        # obtenha a contagem e detalhes (lista de "nome (dias dias)")
        datasets = []
        for i, area in enumerate(areas):
            data_for_area = []
            customData = []  # Armazenará detalhes para cada mês
            area_id = area_info[area]
            for mes in meses:
                # Valor agregado: contagem para esse mês e área
                count_val = next((row["count"] for row in rows if row["mes"] == mes and row["area"] == area), 0)
                data_for_area.append(count_val)
                # Obter detalhes para cada agendamento (nome e dias)
                cursor.execute("""
                    SELECT f.nome, fa.dias_ferias
                    FROM ferias_agendadas fa
                    JOIN funcionarios f ON fa.funcionario_id = f.id
                    WHERE strftime('%Y-%m', fa.data_ferias) = ? AND f.area_id = ?
                """, (mes, area_id))
                details = cursor.fetchall()
                if details:
                    detail_list = [f"{d['nome']} ({d['dias_ferias']} dias)" for d in details]
                    customData.append("\n".join(detail_list))
                else:
                    customData.append("")
            datasets.append({
                "label": area,
                "data": data_for_area,
                "backgroundColor": colors[i % len(colors)],
                "borderColor": colors[i % len(colors)],
                "borderWidth": 1,
                "customData": customData
            })

        # Total de agendamentos
        cursor.execute("SELECT COUNT(*) AS total FROM ferias_agendadas")
        total_agendamentos = cursor.fetchone()["total"]

        # Consulta para pedidos de aprovação pendentes (assumindo que a tabela pedidos_aprovacao existe)
        try:
            cursor.execute("""
                SELECT pa.id, f.nome, pa.dataFerias, pa.diasFerias, pa.status, pa.data_pedido
                FROM pedidos_aprovacao pa
                JOIN funcionarios f ON pa.chapa = f.chapa
                WHERE pa.status = 'PENDENTE'
            """)
            pedidos_rows = cursor.fetchall()
            pedidos_aprovacao = []
            for row in pedidos_rows:
                pedidos_aprovacao.append((
                    row["id"],
                    row["nome"],
                    row["dataFerias"],
                    row["diasFerias"],
                    row["status"],
                    row["data_pedido"]
                ))
        except Exception as e:
            print("Erro ao buscar pedidos de aprovação:", e)
            pedidos_aprovacao = []

        cursor.close()
        conn.close()

        return {
            "labels": meses,
            "datasets": datasets,
            "total_agendamentos": total_agendamentos,
            "pedidos_aprovacao": pedidos_aprovacao
        }

    @staticmethod
    def aprovar_pedido(pedido_id):
        """
        Aprova um pedido de férias:
          1) Busca o registro na tabela pedidos_aprovacao (obtem chapa, dataFerias e diasFerias).
          2) Busca o funcionário pela chapa e insere o registro em ferias_agendadas.
          3) Atualiza o status do pedido para 'APROVADO'.
        """
        try:
            conn = EmployeeDB.get_connection()
            cursor = conn.cursor()

            # 1) Obter dados do pedido
            cursor.execute("""
                SELECT chapa, dataFerias, diasFerias
                FROM pedidos_aprovacao
                WHERE id = ?
            """, (pedido_id,))
            pedido = cursor.fetchone()
            if not pedido:
                cursor.close()
                conn.close()
                return False

            chapa = pedido["chapa"]
            dataFerias = pedido["dataFerias"]
            diasFerias = pedido["diasFerias"]

            # 2) Buscar o funcionário pelo número de chapa
            cursor.execute("SELECT id FROM funcionarios WHERE chapa = ?", (chapa,))
            func = cursor.fetchone()
            if not func:
                cursor.close()
                conn.close()
                return False

            funcionario_id = func["id"]

            # Inserir registro em ferias_agendadas
            cursor.execute("""
                INSERT INTO ferias_agendadas (funcionario_id, data_ferias, dias_ferias)
                VALUES (?, ?, ?)
            """, (funcionario_id, dataFerias, diasFerias))

            # 3) Atualizar o status do pedido para 'APROVADO'
            cursor.execute("UPDATE pedidos_aprovacao SET status = 'APROVADO' WHERE id = ?", (pedido_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print("Erro ao aprovar pedido:", e)
            return False

    @staticmethod
    def rejeitar_pedido(pedido_id):
        """
        Rejeita um pedido, atualizando o status para 'REJEITADO'.
        """
        try:
            conn = EmployeeDB.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE pedidos_aprovacao SET status = 'REJEITADO' WHERE id = ?", (pedido_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print("Erro ao rejeitar pedido:", e)
            return False

    @staticmethod
    def excluir_agendamentos():
        try:
            conn = EmployeeDB.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ferias_agendadas")
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print("Erro ao excluir agendamentos:", e)
            return False
