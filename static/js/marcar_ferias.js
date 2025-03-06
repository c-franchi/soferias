/*
  marcar_ferias.js
  ------------------
  - Gerencia a busca do funcionário via chapa e o agendamento de férias.
  - Valida datas, calcula a data de retorno e envia os dados via POST para /agendar_ferias.
  - Exibe popups animados (SweetAlert2) para confirmação, sucesso, erro e solicitações de aprovação.
  - Ao buscar o funcionário, também consulta os agendamentos existentes e os exibe,
    destacando os usuários do mesmo setor.
*/

// Função para converter data de "YYYY-MM-DD" para "DD/MM/YYYY"
function formatDateBR(dateStr) {
    const parts = dateStr.split("-");
    if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return dateStr;
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("marcar_ferias.js carregado");

    const chapaInput = document.getElementById('chapa');
    const nomeDisplay = document.getElementById('nomeFuncionario');
    const areaDisplay = document.getElementById('areaFuncionario');
    const dataFeriasInput = document.getElementById('dataFerias');
    const diasFeriasInput = document.getElementById('diasFerias');
    const mensagemConflitoP = document.getElementById('mensagemConflito');
    const cancelarButton = document.getElementById('cancelarButton');
    const alterarButton = document.getElementById('alterarButton');
    const solicitarAprovacaoButton = document.getElementById('solicitarAprovacao');
    const escolherOutraDataButton = document.getElementById('escolherOutraData');
    const conflitoModal = new bootstrap.Modal(document.getElementById('conflitoModal'));
    const agendamentosList = document.getElementById('agendamentosList'); // div onde serão listados os agendamentos

    let funcionarioData = null;
    let conflitoData = null;
    let isSubmitting = false;

    // Ao enviar o formulário para buscar o funcionário via chapa
    document.getElementById('marcarFeriasForm').addEventListener('submit', (e) => {
        e.preventDefault();
        console.log("Evento de busca de chapa acionado.");
        const chapa = chapaInput.value.trim();
        if (chapa) {
            fetch(`/buscar_funcionario?chapa=${chapa}`)
                .then(response => response.json())
                .then(data => {
                    console.log("Dados retornados da busca:", data);
                    if (data.nome) {
                        nomeDisplay.textContent = `Nome: ${data.nome}`;
                        areaDisplay.textContent = `Área: ${data.area}`;
                        funcionarioData = data;
                        verificarAgendamento(chapa);
                        document.getElementById('funcionarioInfo').style.display = 'block';
                        // Após obter os dados do funcionário, lista os agendamentos
                        listarAgendamentos(data.area);
                    } else {
                        Swal.fire({
                            title: "Atenção",
                            text: "Funcionário não encontrado.",
                            icon: "warning",
                            timer: 2000,
                            showConfirmButton: false
                        });
                        funcionarioData = null;
                    }
                })
                .catch(error => {
                    console.error("Erro na busca de funcionário:", error);
                    Swal.fire({
                        title: "Erro",
                        text: error.message,
                        icon: "error",
                        timer: 2000,
                        showConfirmButton: false
                    });
                });
        } else {
            Swal.fire({
                title: "Atenção",
                text: "Por favor, informe sua chapa.",
                icon: "warning",
                timer: 2000,
                showConfirmButton: false
            });
        }
    });

    // Função para verificar se o funcionário já possui agendamento
    function verificarAgendamento(chapa) {
        console.log("Verificando agendamento para a chapa:", chapa);
        fetch(`/verificar_agendamento?chapa=${chapa}`)
            .then(response => response.json())
            .then(data => {
                console.log("Resultado da verificação:", data);
                if (data.agendado) {
                    nomeDisplay.textContent += ` - Férias agendadas para: ${formatDateBR(data.dataFerias)} - Retorno: ${formatDateBR(data.dataRetorno)}`;
                    cancelarButton.style.display = 'inline-block';
                    alterarButton.style.display = 'inline-block';
                } else {
                    cancelarButton.style.display = 'none';
                    alterarButton.style.display = 'none';
                }
            })
            .catch(error => {
                console.error("Erro na verificação de agendamento:", error);
                Swal.fire({
                    title: "Erro",
                    text: error.message,
                    icon: "error",
                    timer: 2000,
                    showConfirmButton: false
                });
            });
    }

    // Função para listar os agendamentos existentes
    function listarAgendamentos(meuSetor) {
        fetch('/listar_agendamentos')
            .then(response => response.json())
            .then(data => {
                console.log("Agendamentos retornados:", data);
                // Limpa a div de listagem
                agendamentosList.innerHTML = "";
                if (data.length === 0) {
                    agendamentosList.innerHTML = "<p>Nenhum agendamento encontrado.</p>";
                } else {
                    let table = document.createElement("table");
                    table.classList.add("table", "table-striped");
                    let thead = document.createElement("thead");
                    thead.innerHTML = `<tr>
                        <th>Chapa</th>
                        <th>Nome</th>
                        <th>Área</th>
                        <th>Data de Início</th>
                        <th>Dias</th>
                        <th>Data de Retorno</th>
                    </tr>`;
                    table.appendChild(thead);
                    let tbody = document.createElement("tbody");
                    data.forEach(item => {
                        let tr = document.createElement("tr");
                        // Se o registro for do mesmo setor do usuário, destaca a linha
                        if (item.area === meuSetor) {
                            tr.classList.add("highlight");
                        }
                        tr.innerHTML = `<td>${item.chapa}</td>
                                        <td>${item.nome}</td>
                                        <td>${item.area}</td>
                                        <td>${formatDateBR(item.dataFerias)}</td>
                                        <td>${item.diasFerias}</td>
                                        <td>${formatDateBR(item.data_retorno)}</td>`;
                        tbody.appendChild(tr);
                    });
                    table.appendChild(tbody);
                    agendamentosList.appendChild(table);
                }
            })
            .catch(error => {
                console.error("Erro ao listar agendamentos:", error);
            });
    }

    // Evento para enviar o agendamento
    document.getElementById('selecionarDataForm').addEventListener('submit', (e) => {
        e.preventDefault();
        console.log("Evento de agendamento acionado.");
        if (isSubmitting) return;
        isSubmitting = true;

        const chapa = chapaInput.value.trim();
        const dataFerias = dataFeriasInput.value;
        const diasFerias = diasFeriasInput.value;
        console.log("Dados do agendamento:", { chapa, dataFerias, diasFerias });

        // Validação: a data de início deve ser hoje ou futura
        const dataFeriasDate = new Date(dataFerias);
        const hoje = new Date();
        hoje.setHours(0, 0, 0, 0);
        if (dataFeriasDate < hoje) {
            Swal.fire({
                title: "Atenção",
                text: "A data de início das férias não pode ser anterior à data atual.",
                icon: "warning",
                timer: 2000,
                showConfirmButton: false
            });
            isSubmitting = false;
            return;
        }

        // Calcula a data de retorno, ajustando para fins de semana
        let dataRetorno = new Date(dataFerias);
        dataRetorno.setDate(dataRetorno.getDate() + parseInt(diasFerias));
        if (dataRetorno.getDay() === 6) {
            dataRetorno.setDate(dataRetorno.getDate() + 2);
        } else if (dataRetorno.getDay() === 0) {
            dataRetorno.setDate(dataRetorno.getDate() + 1);
        }
        const dataRetornoStr = dataRetorno.toISOString().split('T')[0];
        console.log("Data de retorno calculada:", dataRetornoStr);

        // Converte datas para o formato brasileiro para exibição
        const dataFeriasBR = formatDateBR(dataFerias);
        const dataRetornoBR = formatDateBR(dataRetornoStr);

        Swal.fire({
            title: "Confirmação",
            text: `Você escolheu ${dataFeriasBR} como data de início por ${diasFerias} dias. Data de retorno: ${dataRetornoBR}. Confirma?`,
            icon: "question",
            showCancelButton: true,
            confirmButtonText: "Sim",
            cancelButtonText: "Não"
        }).then((result) => {
            if (result.isConfirmed) {
                fetch('/agendar_ferias', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chapa: chapa, dataFerias: dataFerias, diasFerias: diasFerias })
                })
                .then(response => response.json())
                .then(data => {
                    console.log("Resposta do agendamento:", data);
                    isSubmitting = false;
                    if (data.conflito) {
                        conflitoData = { chapa: chapa, dataFerias: dataFerias, diasFerias: diasFerias };
                        mensagemConflitoP.textContent = `Conflito: ${data.nome} já está agendado para ${formatDateBR(data.dataFerias)}. Retorno: ${formatDateBR(data.dataRetorno)}. Uma solicitação será enviada ao responsável.`;
                        conflitoModal.show();
                    } else {
                        Swal.fire({
                            title: "Sucesso!",
                            text: data.message,
                            icon: "success",
                            timer: 2000,
                            showConfirmButton: false
                        }).then(() => {
                            location.reload();
                        });
                    }
                })
                .catch(error => {
                    isSubmitting = false;
                    console.error("Erro no agendamento:", error);
                    Swal.fire({
                        title: "Erro",
                        text: error.message,
                        icon: "error",
                        timer: 2000,
                        showConfirmButton: false
                    });
                });
            } else {
                isSubmitting = false;
            }
        });
    });

    // Evento para cancelar o agendamento
    cancelarButton.addEventListener('click', (e) => {
        e.preventDefault();
        const chapa = chapaInput.value.trim();
        if (chapa) {
            fetch('/cancelar_agendamento', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chapa: chapa })
            })
            .then(response => response.json())
            .then(data => {
                Swal.fire({
                    title: "Informação",
                    text: data.message,
                    icon: "info",
                    timer: 2000,
                    showConfirmButton: false
                }).then(() => {
                    location.reload();
                });
            })
            .catch(error => {
                Swal.fire({
                    title: "Erro",
                    text: error.message,
                    icon: "error",
                    timer: 2000,
                    showConfirmButton: false
                });
            });
        }
    });

    // Evento para alterar o agendamento
    alterarButton.addEventListener('click', (e) => {
        e.preventDefault();
        if (isSubmitting) return;
        isSubmitting = true;
        const chapa = chapaInput.value.trim();
        const dataFerias = dataFeriasInput.value;
        const diasFerias = diasFeriasInput.value;
        const dataFeriasDate = new Date(dataFerias);
        const hoje = new Date();
        hoje.setHours(0, 0, 0, 0);
        if (dataFeriasDate < hoje) {
            Swal.fire({
                title: "Atenção",
                text: "A data de início das férias não pode ser anterior à data atual.",
                icon: "warning",
                timer: 2000,
                showConfirmButton: false
            });
            isSubmitting = false;
            return;
        }
        fetch('/alterar_agendamento', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chapa: chapa, dataFerias: dataFerias, diasFerias: diasFerias })
        })
        .then(response => response.json())
        .then(data => {
            isSubmitting = false;
            if (data.conflito) {
                conflitoData = { chapa: chapa, dataFerias: dataFerias, diasFerias: diasFerias };
                mensagemConflitoP.textContent = `Conflito: ${data.nome} já está agendado para ${formatDateBR(data.dataFerias)}. Retorno: ${formatDateBR(data.dataRetorno)}. Uma solicitação será enviada ao responsável.`;
                conflitoModal.show();
            } else {
                Swal.fire({
                    title: "Sucesso!",
                    text: data.message,
                    icon: "success",
                    timer: 2000,
                    showConfirmButton: false
                }).then(() => {
                    location.reload();
                });
            }
        })
        .catch(error => {
            isSubmitting = false;
            Swal.fire({
                title: "Erro",
                text: error.message,
                icon: "error",
                timer: 2000,
                showConfirmButton: false
            });
        });
    });

    // Evento para solicitar aprovação em caso de conflito
    solicitarAprovacaoButton.addEventListener('click', (e) => {
        e.preventDefault();
        if (isSubmitting) return;
        isSubmitting = true;
        if (conflitoData) {
            fetch('/solicitar_aprovacao', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(conflitoData)
            })
            .then(response => response.json())
            .then(data => {
                isSubmitting = false;
                Swal.fire({
                    title: "Informação",
                    text: data.message,
                    icon: "info",
                    timer: 2000,
                    showConfirmButton: false
                }).then(() => {
                    location.reload();
                });
            })
            .catch(error => {
                isSubmitting = false;
                Swal.fire({
                    title: "Erro",
                    text: error.message,
                    icon: "error",
                    timer: 2000,
                    showConfirmButton: false
                });
            });
        }
    });

    // Evento para fechar o modal de conflito e escolher outra data
    escolherOutraDataButton.addEventListener('click', (e) => {
        e.preventDefault();
        conflitoModal.hide();
    });
});
