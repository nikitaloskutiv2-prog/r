

// 🌙 Инициализация темы
function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    if (savedTheme === "dark") {
        document.body.classList.add("dark-theme");
    }
}

// 🌙 Переключение темы
function toggleTheme() {
    document.body.classList.toggle("dark-theme");
    const isDark = document.body.classList.contains("dark-theme");
    localStorage.setItem("theme", isDark ? "dark" : "light");
}

// 📝 Регистрация
async function handleRegister(event) {
    event.preventDefault();
    const login = document.getElementById("login").value.trim();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const passwordConfirm = document.getElementById("passwordConfirm").value;
    const errorDiv = document.getElementById("error");
    const successDiv = document.getElementById("success");
    
    // Скрываем сообщения
    errorDiv.style.display = "none";
    successDiv.style.display = "none";
    
    // Проверка паролей
    if (password !== passwordConfirm) {
        errorDiv.textContent = "Пароли не совпадают";
        errorDiv.style.display = "block";
        return;
    }
    
    logger.info(
        "Попытка регистрации",
        {
            login,
            username
        }
    );
    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                login: login,
                username: username,
                password: password
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            if (response.status === 429) {
                errorDiv.textContent =
                    data.detail || "Слишком много попыток регистрации. Попробуйте позже.";
                errorDiv.style.display = "block";
                return;
            }
            logger.warn(
                "Регистрация отклонена сервером",
                {
                    login,
                    status: response.status,
                    detail: data.detail
                }
            );

            errorDiv.textContent = data.detail || "Ошибка регистрации";
            errorDiv.style.display = "block";
            return;
        }
        
        // Успешная регистрация
        successDiv.textContent = "✅ Регистрация успешна! Перенаправляю на вход...";
        successDiv.style.display = "block";
        
        logger.info(
            "Регистрация успешна, перенаправление на вход"
        );
        setTimeout(() => {
            window.location.href = "login.html";
        }, 2000);
        
    } catch (error) {
        logger.error(
            "Ошибка регистрации",
            error
        );
        errorDiv.textContent = "Ошибка соединения с сервером";
        errorDiv.style.display = "block";
    }
}

// Инициализация темы при загрузке
initTheme();