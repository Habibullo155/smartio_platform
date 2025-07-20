// app/static/javascripts/main.js

document.addEventListener('DOMContentLoaded', () => {
    const adminLoginForm = document.getElementById('adminLoginForm');
    const errorMessageDiv = document.getElementById('errorMessage');
    const logoutButton = document.getElementById('logoutButton');
    const adminUsernameSpan = document.getElementById('adminUsername');

    // --- Логика для страницы логина администратора ---
    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Предотвращаем стандартную отправку формы

            errorMessageDiv.textContent = ''; // Очищаем предыдущие ошибки
            errorMessageDiv.classList.add('hidden');

            const username = adminLoginForm.username.value;
            const password = adminLoginForm.password.value;

            // Создаем объект FormData для отправки данных формы
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            try {
                const response = await fetch('/admin/token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded', // Важно для OAuth2PasswordRequestForm
                    },
                    body: formData.toString() // Преобразуем FormData в строку
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Ошибка входа');
                }

                const data = await response.json();
                localStorage.setItem('admin_access_token', data.access_token); // Сохраняем токен в localStorage
                window.location.href = '/admin/dashboard'; // Перенаправляем на дашборд
            } catch (error) {
                console.error('Ошибка входа:', error.message);
                errorMessageDiv.textContent = error.message;
                errorMessageDiv.classList.remove('hidden');
            }
        });
    }

    // --- Логика для дашборда администратора (и других защищенных страниц) ---
    if (adminUsernameSpan) { // Проверяем, что мы на дашборде или другой админ-странице
        const token = localStorage.getItem('admin_access_token');

        if (!token) {
            window.location.href = '/admin/login'; // Если нет токена, перенаправляем на страницу логина
            return; // Прерываем выполнение
        }

        // Функция для получения данных о текущем администраторе
        async function fetchAdminInfo() {
            try {
                const response = await fetch('/admin/me', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}` // Отправляем токен в заголовке
                    }
                });

                if (response.status === 401) { // Если токен недействителен или истек
                    localStorage.removeItem('admin_access_token'); // Удаляем токен
                    window.location.href = '/admin/login'; // Перенаправляем на логин
                    return;
                }

                if (!response.ok) {
                    throw new Error('Не удалось получить информацию об администраторе.');
                }

                const adminInfo = await response.json();
                adminUsernameSpan.textContent = adminInfo.full_name || adminInfo.username; // Отображаем имя админа
            } catch (error) {
                console.error('Ошибка при получении данных об администраторе:', error.message);
                localStorage.removeItem('admin_access_token'); // В случае ошибки также удаляем токен
                window.location.href = '/admin/login';
            }
        }

        fetchAdminInfo(); // Вызываем функцию при загрузке страницы

        // Логика выхода из системы
        if (logoutButton) {
            logoutButton.addEventListener('click', () => {
                localStorage.removeItem('admin_access_token'); // Удаляем токен
                window.location.href = '/admin/login'; // Перенаправляем на страницу логина
            });
        }
    }
});