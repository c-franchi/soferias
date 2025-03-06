/*
  login.js
  --------
  Faz o POST para /login com { usuario, senha } em JSON.
  Em caso de sucesso, redireciona para /dashboard.
*/

document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault(); // Impede o envio tradicional do formulário
  
    const usuario = document.getElementById('usuario').value;
    const senha = document.getElementById('senha').value;
    const loginMessage = document.getElementById('loginMessage');
  
    // Envia os dados de login via fetch
    fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usuario, senha })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Se login der certo, redireciona para /dashboard
        window.location.href = '/dashboard';
      } else {
        // Exibe mensagem de erro
        loginMessage.style.display = 'block';
        loginMessage.textContent = data.message;
      }
    })
    .catch(error => {
      console.error('Erro ao fazer login:', error);
      loginMessage.style.display = 'block';
      loginMessage.textContent = 'Ocorreu um erro. Tente novamente mais tarde.';
    });
  });
  