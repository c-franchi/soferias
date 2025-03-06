/*
  profile.js
  ----------
  - Envia o formulário de perfil via fetch para /profile.
  - Em caso de sucesso, exibe um popup animado com SweetAlert2 e redireciona para o dashboard.
  - Em caso de erro, registra o erro no console e exibe um popup com a mensagem de erro.
*/

document.addEventListener('DOMContentLoaded', () => {
    const profileForm = document.querySelector('.profile-form');
    const profilePicUpload = document.getElementById('profilePicUpload');
    const uploadPlanilha = document.getElementById('uploadPlanilha');
    const profilePic = document.getElementById('profilePic');
    // Se houver um elemento para mobile, ex.: profilePicMobile (opcional)
    const profilePicMobile = document.getElementById('profilePicMobile');

    profileForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const profilePicFile = profilePicUpload.files[0];
        const planilhaFile = uploadPlanilha.files[0];
        const formData = new FormData();

        if (profilePicFile) {
            formData.append('profilePicUpload', profilePicFile);
        }
        if (planilhaFile) {
            formData.append('uploadPlanilha', planilhaFile);
        }

        fetch('/profile', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.profilePicUrl) {
                profilePic.src = data.profilePicUrl;
                if (profilePicMobile) {
                    profilePicMobile.src = data.profilePicUrl;
                }
            }
            if (data.message) {
                Swal.fire({
                    title: "Sucesso!",
                    text: data.message,
                    icon: "success",
                    timer: 2000,
                    showConfirmButton: false,
                    showClass: {
                        popup: 'animate__animated animate__fadeInDown'
                    },
                    hideClass: {
                        popup: 'animate__animated animate__fadeOutUp'
                    }
                }).then(() => {
                    window.location.href = '/dashboard';
                });
            }
        })
        .catch(error => {
            console.error('Erro ao salvar perfil:', error);
            Swal.fire({
                title: "Erro!",
                text: "Erro: " + error.message,
                icon: "error",
                timer: 3000,
                showConfirmButton: false,
                showClass: {
                    popup: 'animate__animated animate__shakeX'
                }
            });
        });
    });

    // Atualiza a pré-visualização da imagem de perfil quando o usuário seleciona um arquivo
    profilePicUpload.addEventListener('change', () => {
        const file = profilePicUpload.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                profilePic.src = e.target.result;
                if (profilePicMobile) {
                    profilePicMobile.src = e.target.result;
                }
            };
            reader.readAsDataURL(file);
        }
    });
});
