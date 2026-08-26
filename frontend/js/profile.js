let openedProfileUserId = null;
let currentBlockStatus = null;

async function openProfile(user, isOwnProfile = false) {
    logger.debug(
        "Открытие профиля",
        {
            userId: user?.id,
            isOwnProfile
        }
    );
    const overlay = document.getElementById("modalOverlay");
    const editBtn = document.querySelector(".btn-edit");
    const blockBtn = document.getElementById("blockUserBtn");
    const deleteBtn = document.getElementById("deleteAccountBtn")


    if (user.is_deleted) {

        openedProfileUserId = user.id;
        currentBlockStatus = null;

        renderAvatar(user, null);

        document.getElementById("ausername").textContent = user.username;
        document.getElementById("ausernameid").textContent = "";
        document.getElementById("abio").textContent = "";
        document.getElementById("ahappy").textContent = "";
        document.getElementById("info").style.display = "flex";
        document.getElementById("infoEdit").style.display = "none";
        editBtn.style.display = "none";
        deleteBtn.style.display = "none";
        blockBtn.style.display = "none";
        overlay.classList.add("active");
        return;
    }


    await loadBlockStatus(user.id);
    renderAvatar(user, currentBlockStatus);
    // данные
    document.getElementById("ausername").textContent = user.username || "";
    document.getElementById("ausernameid").textContent = user.usernameid || "@unknown";
    document.getElementById("abio").textContent = user.bio || "Не указано";
    document.getElementById("ahappy").textContent = user.birthday || "Не указано";

    // режим просмотра
    document.getElementById("info").style.display = "flex";
    document.getElementById("infoEdit").style.display = "none";

    if (isOwnProfile) {

        editBtn.style.display = "block";
        deleteBtn.style.display = "block";
        blockBtn.style.display = "none";

    } else {

        editBtn.style.display = "none";
        deleteBtn.style.display = "none";
        blockBtn.style.display = "block";

}
    overlay.classList.add("active");
}


function renderAvatar(user, blockStatus) {

    const avatar =
        document.getElementById("avatar");

    avatar.innerHTML = "";

    if (blockStatus?.blocked_me) {

        const div =
            document.createElement("div");

        div.className = "setava";

        div.textContent =
            user.username?.charAt(0).toUpperCase() || "?";

        avatar.appendChild(div);

        return;

    }

    if (user.avatar) {

        const img =
            document.createElement("img");

        img.src =
            `${API_URL}${user.avatar}`;

        img.className =
            "profile-avatar-image";

        avatar.appendChild(img);

    } else {

        const div =
            document.createElement("div");

        div.className = "setava";

        div.textContent =
            user.username?.charAt(0).toUpperCase() || "?";

        avatar.appendChild(div);

    }

}

function showChatMemberProfile() {
    const chat = allChats.find(
        c => Number(c.id) === Number(currentChatId)
    );

    if (!chat) return;

    const memberId = chat.members.find(
        id => Number(id) !== Number(currentUserId)
    );

    if (memberId) {
        showUserProfile(memberId);
    }
}
// 👤 Показать профиль собеседника
async function showUserProfile(userId) {
    try {

        const response = await fetch(
            `${API_URL}/users/${userId}`,
            {
                headers:{
                    Authorization:`Bearer ${token}`
                }
            }
        );

        if (!response.ok) {

            logger.warn(
                "Не удалось загрузить профиль пользователя",
                {
                    userId,
                    status: response.status
                }
            );

            return;
        }

        const user = await response.json();
        logger.debug(
            "Профиль пользователя загружен",
            {
                userId: user.id
            }
        );
        openedProfileUserId = user.id;
        openProfile(user, false);

    } catch (e) {

        logger.error(
            "Ошибка загрузки профиля пользователя",
            e
        );

    }
}

async function loadBlockStatus(userId) {
    try {

        const response = await fetch(
            `${API_URL}/users/${userId}/block-status`,
            {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {

            logger.warn(
                "Не удалось загрузить статус блокировки",
                {
                    userId,
                    status: response.status
                }
            );

            return;
        }

        currentBlockStatus = await response.json();

        updateBlockButton();

    } catch (e) {

        logger.error(
            "Ошибка загрузки статуса блокировки",
            e
        );

    }
}

function updateBlockButton() {

    const btn = document.getElementById("blockUserBtn");

    if (!btn || !currentBlockStatus) return;

    if (currentBlockStatus.i_blocked) {

        btn.textContent = "Разблокировать";

        btn.classList.add("danger");

    } else {

        btn.textContent = "Заблокировать";

        btn.classList.add("danger");

    }

}

async function toggleBlockUser(event) {

    if (event)
        event.preventDefault();

    if (!openedProfileUserId)
        return;
    logger.info(
        currentBlockStatus.i_blocked
            ? "Разблокировка пользователя"
            : "Блокировка пользователя",
        {
            userId: openedProfileUserId
        }
    );
    try {

        let response;

        if (currentBlockStatus.i_blocked) {

            response = await fetch(
                `${API_URL}/users/${openedProfileUserId}/block`,
                {
                    method:"DELETE",
                    headers:{
                        Authorization:`Bearer ${token}`
                    }
                }
            );

        }else{

            response = await fetch(
                `${API_URL}/users/${openedProfileUserId}/block`,
                {
                    method:"POST",
                    headers:{
                        Authorization:`Bearer ${token}`
                    }
                }
            );

        }

        if (!response.ok) {

            logger.warn(
                "Не удалось изменить блокировку пользователя",
                {
                    userId: openedProfileUserId,
                    status: response.status
                }
            );

            return;
        }

        await loadBlockStatus(openedProfileUserId);
        await updateInputState();
        await loadUserStatus(openedProfileUserId);
        
    } catch (e) {

        logger.error(
            "Ошибка изменения блокировки пользователя",
            e
        );

    }

}

function openDeleteAccountModal() {

    const modal = document.getElementById("deleteAccountModal");

    if (!modal) return;

    modal.classList.add("active");
}


function closeDeleteAccountModal() {

    const modal = document.getElementById("deleteAccountModal");

    if (!modal) return;

    modal.classList.remove("active");
}


async function confirmDeleteAccount() {

    const confirmBtn =
        document.querySelector(".delete-confirm-btn");

    if (confirmBtn) {
        confirmBtn.disabled = true;
        confirmBtn.textContent = "Удаление...";
    }

    try {

        const response = await fetch(
            `${API_URL}/users/me`,
            {
                method: "DELETE",
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        );

        const data = await response.json();

        if (!response.ok) {

            logger.error(
                "Ошибка удаления аккаунта",
                data
            );

            showToast(
                data.detail ||
                "Не удалось удалить аккаунт"
            );

            if (confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.textContent = "Удалить аккаунт";
            }

            return;
        }

        // Закрываем websocket
        logger.info(
            "Аккаунт успешно удалён"
        );
        if (
            typeof socket !== "undefined" &&
            socket
        ) {
            socket.close();
        }

        // Удаляем локальную авторизацию
        localStorage.removeItem("token");
        localStorage.removeItem("user");

        // Переходим на вход
        window.location.href = "login.html";

    } catch (error) {

        logger.error(
            "Ошибка удаления аккаунта",
            error
        );

        showToast("Ошибка соединения с сервером");

        if (confirmBtn) {
            confirmBtn.disabled = false;
            confirmBtn.textContent = "Удалить аккаунт";
        }
    }
}

document
    .getElementById("deleteAccountModal")
    .addEventListener("click", function(event) {

        if (event.target === this) {
            closeDeleteAccountModal();
        }

    });


document
    .getElementById("blockUserBtn")
    .addEventListener(
        "click",
        (e) => toggleBlockUser(e)
    );