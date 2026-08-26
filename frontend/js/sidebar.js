let allChats = [];
let isRenderingChats = false;
let renderChatsAgain = false;


async function loadChats() {

    try {

        const response = await fetch(
            `${API_URL}/chats/`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {

           logger.error(
                "Ошибка загрузки чатов",
                response.status
            );

            return;
        }

        let chats = await response.json();

        allChats = chats;
        sortChats()
        renderChats();

    } catch (error) {

        logger.error(
            "Ошибка загрузки чатов",
            error
        );
    }
    
}

async function loadUnreadCounts() {
    try {
        const response = await fetch(`${API_URL}/messages/unread/counts`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        
        if (!response.ok) {
            logger.error("Error loading unread counts:", response.status);
            return;
        }
        
        unreadCounts = await response.json();
        
        // Обновляем UI с бейджами
        updateChatBadges();
    } catch (error) {
        logger.error("Error loading unread counts:", error);
    }
}

async function renderChats() {

    if (isRenderingChats) {
        renderChatsAgain = true;
        return;
    }

    isRenderingChats = true;

    try {

        const chatsList =
            document.getElementById("chatsList");

        chatsList.innerHTML = "";

        if (allChats.length === 0) {

            chatsList.innerHTML =
                '<div class="empty-sidebar-message">Нет чатов. Найдите пользователя.</div>';

            return;
        }

        for (const chat of allChats) {

            const chatItem =
                await createChatItem(chat);

            chatsList.appendChild(chatItem);

        }

        updateChatBadges();

    } finally {

        isRenderingChats = false;

        if (renderChatsAgain) {

            renderChatsAgain = false;

            renderChats();

        }

    }
}

async function createChatItem(chat) {

    const div =
        document.createElement("div");

    div.className = "chat-item";

    div.dataset.chatId =
        chat.id;

    const otherUserId =
        chat.members.find(
            id =>
                Number(id) !==
                Number(currentUserId)
        );
        
    let blockInfo = {
        blocked: false,
        blocked_me: false,
        i_blocked: false
    };

    if (otherUserId) {

        const response = await fetch(
            `${API_URL}/users/${otherUserId}/block-status`,
            {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        );

        if (response.ok) {
            blockInfo = await response.json();
        }

    }
    let isOnline = false;

    if (
        !chat.is_favorite &&
        otherUserId &&
        !blockInfo.blocked_me
    ) {
        isOnline = await loadSidebarUserStatus(otherUserId);
    }

    const info =
        buildLastMessageInfo(chat);



    const avatar =
        document.createElement("div");

    avatar.className =
        `chat-avatar ${
            !chat.is_favorite && isOnline
                ? "online"
                : ""
        }`;

    if (
        chat.avatar &&
        !blockInfo.blocked_me
    ) {

        const img = document.createElement("img");
        img.src = `${API_URL}${chat.avatar}`;
        img.className =
            chat.is_favorite
                ? "favorite-avatar-image"
                : "chat-avatar-image";

        avatar.appendChild(img);

    } else {

        avatar.textContent = chat.name.charAt(0).toUpperCase() || "?";

    }

    div.innerHTML = `
        <div class="chat-info">

            <div class="chat-top-row">

                <div class="chat-name">
                    ${chat.name}
                </div>

                <div class="chat-meta">

                    ${
                        info.readStatus
                            ? `<span class="last-message-status">${info.readStatus}</span>`
                            : ""
                    }

                    <div class="chat-time">
                        ${info.time}
                    </div>

                </div>

            </div>

            <div class="chat-preview">
                ${info.preview}
            </div>

        </div>
    `;

    div.insertBefore(
        avatar,
        div.firstChild
    );

    div.addEventListener(
        "click",
        () => selectChat(chat)
    );

    return div;

}

function buildLastMessageInfo(chat) {

    const lastMsg = chat.last_message;

    return {

        preview: getMessagePreview(lastMsg),

        time: formatChatTime(lastMsg),

        readStatus:
            lastMsg &&
            lastMsg.sender_id === currentUserId
                ? (
                    lastMsg.is_read
                        ? "✓✓"
                        : "✓"
                )
                : ""

    };

}

function getMessagePreview(msg) {
    if (!msg) {
        return "Нет сообщений";
    }
    if (msg.file) {

        let preview;

        if (msg.file.mime_type.startsWith("audio/")) {

            if (msg.voice_duration != null) {

                preview = "🎤 Голосовое сообщение";

            } else {

                preview = `🎵 ${msg.file.original_name}`;

            }

        }
        else if (msg.file.mime_type.startsWith("image/")) {

            preview = "📷 Фото";

        }
        else if (msg.file.mime_type.startsWith("video/")) {

            preview = "🎥 Видео";

        }
        else {

            preview = `📎 ${msg.file.original_name}`;

        }

        return preview;
    }

    return msg.content || "Нет сообщений";
}

function formatChatTime(lastMsg) {

    if (!lastMsg) {
        return "";
    }

    return new Date(
        lastMsg.created_at + "Z"
    ).toLocaleTimeString(
        "ru-RU",
        {
            hour: "2-digit",
            minute: "2-digit"
        }
    );

}

async function loadSidebarUserStatus(userId) {

    try {

        const response =
            await fetch(
                `${API_URL}/users/${userId}/status`,
                {
                    headers: {
                        Authorization:
                            `Bearer ${token}`
                    }
                }
            );

        if (!response.ok) {
            return false;
        }

        const data =
            await response.json();

        return data.status === "online";

    } catch {

        return false;

    }

}

function updateSidebarOnlineStatus(
    userId,
    isOnline
) {

    const chatItems =
        document.querySelectorAll(".chat-item");

    chatItems.forEach(item => {

        const chatId =
            Number(item.dataset.chatId);

        const chat =
            allChats.find(
                c => Number(c.id) === chatId
            );

        if (!chat || chat.is_favorite) {
            return;
        }

        const otherUserId =
            chat.members.find(
                id =>
                    Number(id) !==
                    Number(currentUserId)
            );

        if (
            !otherUserId ||
            Number(otherUserId) !== userId
        ) {
            return;
        }

        const avatar =
            item.querySelector(".chat-avatar");

        if (!avatar) {
            return;
        }

        avatar.classList.toggle(
            "online",
            isOnline
        );
    });
}


function updateChatBadges() {

    const chatItems =
        document.querySelectorAll(".chat-item");

    chatItems.forEach(item => {

        const oldBadge =
            item.querySelector(".unread-badge");

        if (oldBadge) {
            oldBadge.remove();
        }

        const avatar =
            item.querySelector(".chat-avatar");

        if (!avatar) return;

        const chatId =
            Number(item.dataset.chatId);

        const chat =
            allChats.find(
                c => c.id === chatId
            );

        if (
            chat &&
            unreadCounts[chat.id] > 0
        ) {

            const badge =
                document.createElement("div");

            badge.className =
                "unread-badge";

            badge.textContent =
                unreadCounts[chat.id];

            avatar.appendChild(badge);
        }
    });
}

function updateChatPreview(msg) {

    const item = document.querySelector(
        `.chat-item[data-chat-id="${msg.chat_id}"]`
    );

    if (!item) {
        return;
    }

    item.querySelector(".chat-preview").textContent =
        getMessagePreview(msg);

    item.querySelector(".chat-time").textContent =
        formatChatTime(msg);

    const status =
        item.querySelector(".last-message-status");

    if (msg.sender_id === currentUserId) {

        if (status) {
            status.textContent = "✓";
        }
        else {

            const meta =
                item.querySelector(".chat-meta");

            meta.insertAdjacentHTML(
                "afterbegin",
                `<span class="last-message-status">✓</span>`
            );
        }

    }

    item.parentElement.prepend(item);

    const chat =
        allChats.find(c => c.id === msg.chat_id);

    if (chat) {
        chat.last_message = msg;
    }
}


function handleChatUpdated(chatUpdate) {

    if (!chatUpdate || !chatUpdate.id) {
        return;
    }

    const chat =
        allChats.find(
            c => c.id === chatUpdate.id
        );

    /*
     * Чат уже есть.
     */
    if (chat) {

        chat.last_message =
            chatUpdate.last_message;

        updateChatPreview(
            chatUpdate.last_message
        );

        return;
    }

    allChats.push({
        ...chatUpdate
    });

    sortChats();
    renderChats();
}


function sortChats() {

    allChats.sort((a, b) => {

        const aTime =
            a.last_message
                ? new Date(a.last_message.created_at)
                : 0;

        const bTime =
            b.last_message
                ? new Date(b.last_message.created_at)
                : 0;

        return bTime - aTime;

    });

}


function updateChatAfterMessageDelete(
    chatId,
    lastMessage
) {

    const chat =
        allChats.find(
            c => c.id === chatId
        );

    if (!chat) {
        return;
    }

    chat.last_message =
        lastMessage;

    sortChats();
    renderChats();
}


async function handleChatDeleted(msg) {

    if (!msg || !msg.chat_id) {
        return;
    }

    const chatId = Number(msg.chat_id);



    allChats = allChats.filter(
        chat => Number(chat.id) !== chatId
    );


    delete unreadCounts[chatId];

    if (Number(currentChatId) === chatId) {

        if (typeof stopChatWebSocket === "function") {
            stopChatWebSocket();
        }

        closeDeletedChat();
    }

    await renderChats();
}

