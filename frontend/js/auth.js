
async function getCurrentUser() {
    try {
        logger.info("Checking current user");
        const response = await fetch(`${API_URL}/auth/me`, {
            method: "GET",
            headers: { 
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });
        
        
        if (!response.ok) {
            logger.warn("Authentication failed", {
                status: response.status
            });

            let errorData = null;

            try {
                errorData = await response.json();
            } catch (error) {
                // Ответ не содержит JSON
            }

            if (errorData) {
                logger.warn("Authentication error details", {
                    detail: errorData.detail
                });
            }

            localStorage.removeItem("token");
            localStorage.removeItem("user");
            window.location.href = "login.html";
            return null;
        }
        
        const user = await response.json();
        logger.info("Current user loaded", {
            userId: user.id,
            username: user.username
        });
        return user;
        
    } catch (error) {
        logger.error("Error getting current user", error);
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.href = "login.html";
        return null;
    }
}

async function logout(event) {
    event.preventDefault();
    logger.info("Logout started");
    try {
        await updateUserStatus("offline");
    } catch (error) {
        logger.error(
            "Failed to update user status during logout",
            error
        );
    }

    // Закрываем chat websocket
    if (socket) {
        socket.close();
    }

    // Закрываем notification websocket
    if (notificationSocket) {
        notificationSocket.close();
    }
    logger.info("Logout completed");
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    window.location.href = "login.html";
}

const token = localStorage.getItem("token");

function requireAuth() {
    if (!token) {
        logger.warn("Authentication required: token not found");
        window.location.href = "login.html";
        return false;
    }
    return true;
}

async function initAuth() {
    logger.info("Auth initialization started");

    if (!requireAuth()) return null;

    const user = await getCurrentUser();

    if (user) {
        logger.info("Auth initialization completed");
    }

    return user;
}