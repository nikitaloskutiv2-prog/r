

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

// 🔐 Вход
async function handleLogin(event) {
    event.preventDefault();
    
    const login = document.getElementById("login").value.trim();
    const password = document.getElementById("password").value;
    const errorDiv = document.getElementById("error");
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                login: login,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            if (response.status === 429) {
                errorDiv.textContent =
                    data.detail || "Слишком много попыток. Попробуйте позже.";
                errorDiv.style.display = "block";
                return;
            }
            errorDiv.textContent = data.detail || "Ошибка входа";
            errorDiv.style.display = "block";
            return;
        }
        
        // Сохраняем токен и юзера
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", JSON.stringify({
            user_id: data.user_id,
            username: data.username
        }));
        
        window.location.href = "index.html";
        
    } catch (error) {
        logger.error("Login error", error);
        errorDiv.textContent = "Ошибка соединения с сервером";
        errorDiv.style.display = "block";
    }
}

// Инициализация темы при загрузке
initTheme();