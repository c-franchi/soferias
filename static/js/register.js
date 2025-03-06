/*
  register.js
  -----------
  Envia (usuario, senha) via JSON para /register.
  Em caso de sucesso, exibe mensagem e redireciona para /login.
*/

document.getElementById('registerForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const usuario = document.getElementById('usuario').value;
    const senha = document.getElementById('senha').value;
    const registerMessage = document.getElementById('registerMessage');
  
    fetch('/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usuario, senha })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        registerMessage.style.display = 'block';
        registerMessage.classList.remove('text-danger');
        registerMessage.classList.add('text-success');
        registerMessage.textContent = data.message;
        setTimeout(() => {
          window.location.href = '/login';
        }, 2000);
      } else {
        registerMessage.style.display = 'block';
        registerMessage.classList.remove('text-success');
        registerMessage.classList.add('text-danger');
        registerMessage.textContent = data.message;
      }
    })
    .catch(error => {
      console.error('Erro no registro:', error);
      registerMessage.style.display = 'block';
      registerMessage.classList.remove('text-success');
      registerMessage.classList.add('text-danger');
      registerMessage.textContent = 'Ocorreu um erro. Tente novamente.';
    });
  });
  