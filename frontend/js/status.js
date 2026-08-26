
function initStatus() {

}

async function loadUserStatus(userId) {
    if (!userId) {
        logger.warn("loadUserStatus: userId отсутствует");
        return;
    }

    if (window.isRecordingVoice || window.isTyping) {
        return;
    }


    const status = document.getElementById("chatStatus");
    const avatar = document.getElementById("chatAvatar");

    const chat = allChats.find(
        c => Number(c.id) === Number(currentChatId)
    );


    if (chat?.is_favorite) {

        if (status) {
            status.textContent = "";
            status.style.display = "none";
        }

        if (avatar) {
            avatar.classList.remove("online");
        }

        return;
    }

    // =========================================
    // ПРОВЕРКА БЛОКИРОВКИ
    // =========================================

    const blockResponse = await fetch(
        `${API_URL}/users/${userId}/block-status`,
        {
            headers: {
                Authorization: `Bearer ${token}`
            }
        }
    );

    if (blockResponse.ok) {

        const block = await blockResponse.json();

        if (block.blocked_me) {

            if (status) {
                status.textContent =
                    "был(а) в сети давно";

                status.style.color = "#999";
                status.style.display = "";
            }

            if (avatar) {
                avatar.classList.remove("online");

                avatar.innerHTML = "";

                avatar.textContent =
                    chat?.name?.charAt(0).toUpperCase() || "?";
            }

            return;
        }
    }

    // =========================================
    // ПОЛУЧАЕМ ИНФОРМАЦИЮ О ПОЛЬЗОВАТЕЛЕ
    // =========================================

    const userResponse = await fetch(
        `${API_URL}/users/${userId}`,
        {
            headers: {
                Authorization: `Bearer ${token}`
            }
        }
    );

    if (userResponse.ok) {

        const user = await userResponse.json();

        // Удалённый аккаунт
        if (user.is_deleted) {

            if (status) {
                status.textContent =
                    "Был(а) в сети очень давно";

                status.style.color = "#999";
                status.style.display = "";
            }

            if (avatar) {
                avatar.classList.remove("online");
            }

            return;
        }
    }

    // =========================================
    // АВАТАР СОБЕСЕДНИКА
    // =========================================

    if (chat?.avatar && avatar) {

        avatar.innerHTML = "";

        const img =
            document.createElement("img");

        img.src =
            `${API_URL}${chat.avatar}`;

        img.className =
            chat.is_favorite
                ? "favorite-avatar-image"
                : "chat-avatar-image";

        avatar.appendChild(img);
    }

    // =========================================
    // СТАТУС
    // =========================================

    try {

        const response = await fetch(
            `${API_URL}/users/${userId}/status`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            return;
        }

        const data =
            await response.json();

        // На случай, если до этого был открыт
        // "Избранное", снова показываем статус
        // для обычного чата.
        if (status) {
            status.style.display = "";
        }

        if (data.status === "online") {

            if (status) {
                status.textContent = "в сети";
                status.style.color = "#34c759";
            }

            if (avatar) {
                avatar.classList.add("online");
            }

        } else {

            if (status) {
                status.textContent =
                    formatLastSeen(data.last_seen);

                status.style.color = "#999";
            }

            if (avatar) {
                avatar.classList.remove("online");
            }
        }

    } catch (error) {

        logger.error(
            "Ошибка загрузки статуса:",
            error
        );
    }
}

async function updateUserStatus(status) {
    try {
        const response = await fetch(
            `${API_URL}/users/me/status`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    status: status,
                    last_seen: new Date().toISOString()
                }),
                keepalive: true
            }
        );

        if (!response.ok) {
            logger.error(
                "Ошибка обновления статуса:",
                response.status
            );
        }

    } catch (error) {
        logger.error(
            "Ошибка обновления статуса:",
            error
        );
    }
}

function formatLastSeen(lastSeen) {
    const now = new Date();
    const date = new Date(
        lastSeen.endsWith("Z")
            ? lastSeen
            : lastSeen + "Z"
    );

    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const time =
        date.toLocaleTimeString(
            "ru-RU",
            {
                hour: "2-digit",
                minute: "2-digit"
            }
        );
    if (diffDays === 0) {
        return `был(а) в сети в ${time}`;
    }
    if (diffDays === 1) {
        return `был(а) в сети вчера в ${time}`;
    }
    if (diffDays <= 7) {
        const weekday =
            date.toLocaleDateString(
                "ru-RU",
                {
                    weekday: "long"
                }
            );
        return `был(а) в сети в ${weekday}`;
    }
    if (diffDays <= 30) {
        return "был(а) в сети в этом месяце";
    }
    return "был(а) в сети очень давно";
}




function getCurrentCompanionId() {

    const chat = allChats.find(
        c => Number(c.id) === Number(currentChatId)
    );

    if (!chat || chat.is_favorite) {
        return null;
    }

    return chat.members.find(
        id =>
            Number(id) !==
            Number(currentUserId)
    ) || null;
}