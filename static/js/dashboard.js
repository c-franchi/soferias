/*
  dashboard.js
  ------------
  - Carrega os dados do dashboard via endpoint /dashboard_data.
  - Se não houver agendamentos, exibe a mensagem "Sem agendamentos de férias."
  - Caso haja agendamentos, monta um gráfico de barras com os meses (labels) e datasets (por área).
  - Configura os tooltips para exibir o mês no formato MM/YYYY e detalhes (nome do funcionário e dias de férias).
  - Também inclui a configuração dos ticks do eixo x para exibir as datas no formato MM/YYYY.
  - Inclui funções para copiar o link, aprovar/rejeitar pedidos e excluir agendamentos.
  - Utiliza SweetAlert2 para popups animados em caso de erro.
*/

document.addEventListener('DOMContentLoaded', function() {
  console.log("dashboard.js carregado");
  const chartContainer = document.getElementById('chartContainer');
  const ctx = document.getElementById('feriasChart').getContext('2d');

  // Requisição para obter os dados do dashboard
  fetch('/dashboard_data')
    .then(response => response.json())
    .then(data => {
        console.log("Dados do dashboard:", data);
        if (data.total_agendamentos === 0) {
            chartContainer.innerHTML = "<p class='text-center'>Sem agendamentos de férias.</p>";
        } else {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels, // Exemplo: ["2023-06", "2023-07", ...]
                    datasets: data.datasets  // Dados agrupados por área com propriedade customData para detalhes
                },
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            beginAtZero: true,
                            title: { display: true, text: 'Meses' },
                            ticks: {
                                // Converte o rótulo de cada tick de "YYYY-MM" para "MM/YYYY"
                                callback: function(value, index, ticks) {
                                    let label = this.getLabelForValue(value);
                                    const parts = label.split("-");
                                    if (parts.length === 2) {
                                        return parts[1] + "/" + parts[0];
                                    }
                                    return label;
                                }
                            }
                        },
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Número de Funcionários' }
                        }
                    },
                    plugins: {
                        legend: { position: 'top' },
                        title: { display: true, text: 'Agendamentos de Férias por Área e Mês' },
                        tooltip: {
                            callbacks: {
                                // Converte o título do tooltip (rótulo) de "YYYY-MM" para "MM/YYYY"
                                title: function(tooltipItems) {
                                    let label = tooltipItems[0].label;
                                    const parts = label.split("-");
                                    if (parts.length === 2) {
                                        return parts[1] + "/" + parts[0];
                                    }
                                    return label;
                                },
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    label += context.parsed.y;
                                    // Se houver dados customizados, exibe os detalhes
                                    let custom = context.dataset.customData ? context.dataset.customData[context.dataIndex] : '';
                                    if (custom) {
                                        label += "\nDetalhes: " + custom;
                                    }
                                    return label;
                                }
                            }
                        }
                    }
                }
            });
        }
    })
    .catch(error => {
        console.error('Erro ao carregar dados do dashboard:', error);
        Swal.fire({
            title: "Erro",
            text: error.message,
            icon: "error",
            timer: 2000,
            showConfirmButton: false
        });
    });

  // Função para copiar o link para marcar férias
  const copyLinkButton = document.getElementById('copyLinkButton');
  if (copyLinkButton) {
      copyLinkButton.addEventListener('click', function() {
          const feriasLink = document.getElementById('feriasLink');
          feriasLink.select();
          document.execCommand('copy');
          document.getElementById('copyMessage').style.display = 'block';
          setTimeout(() => {
              document.getElementById('copyMessage').style.display = 'none';
          }, 2000);
      });
  }
});

/* Funções para Aprovar/Rejeitar Pedidos */
function aprovarPedido(idString) {
  const id = parseInt(idString, 10);
  fetch('/aprovar_pedido', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pedido_id: id, acao: 'aprovar' })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      location.reload();
    } else {
      Swal.fire({
        title: "Erro",
        text: "Erro ao aprovar pedido.",
        icon: "error",
        timer: 2000,
        showConfirmButton: false
      });
    }
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

function rejeitarPedido(idString) {
  const id = parseInt(idString, 10);
  fetch('/aprovar_pedido', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pedido_id: id, acao: 'rejeitar' })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      location.reload();
    } else {
      Swal.fire({
        title: "Erro",
        text: "Erro ao rejeitar pedido.",
        icon: "error",
        timer: 2000,
        showConfirmButton: false
      });
    }
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

/* Função para Excluir Todos os Agendamentos */
function excluirAgendamentos() {
  fetch('/excluir_agendamentos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      location.reload();
    } else {
      Swal.fire({
        title: "Erro",
        text: "Erro ao excluir agendamentos.",
        icon: "error",
        timer: 2000,
        showConfirmButton: false
      });
    }
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
