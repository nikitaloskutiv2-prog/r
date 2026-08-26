const messageInput =
    document.getElementById("messageInput");

const sendBtn =
    document.getElementById("sendBtn");

const voiceBtn =
    document.getElementById("voiceBtn");

const cancelVoiceBtn =
    document.getElementById("cancelVoiceBtn");

voiceBtn.onclick = startVoiceRecording;
cancelVoiceBtn.onclick = stopVoiceRecording;

let isRecording = false;
let currentCompanionId = null;

let oldestMessageId = null;
let loadingMoreMessages = false;
let allMessagesLoaded = false;
let restoringScrollPosition = false;

function initChat() {

        messageInput?.addEventListener("input",sendTyping);

        messageInput?.addEventListener(
            "keypress",
            (e) => {

                if (e.key === "Enter") {
                    handleSend();
                }

            }
        );
        initChatDeleteMenu()

}

async function selectChat(chat) {
    
    currentChatId = chat.id;
    document.getElementById(
        "chatSearchBtn"
    ).style.display = "block";

    document.getElementById(
        "chatMoreWrapper"
    ).style.display = "flex";
    
    // Загружаем статус собеседника
    if (chat.is_favorite) {
        currentCompanionId = null;

        const status = document.getElementById("chatStatus");

        if (status) {
            status.textContent = "";
            status.style.display = "none";
        }
    } else {
        const otherUserId = chat.members.find(
            id => Number(id) !== Number(currentUserId)
        );

        currentCompanionId = otherUserId || null;

        if (otherUserId) {
            await loadUserStatus(otherUserId);
        }
    }
    
    updateChatHeader(chat);
    
    messageIds.clear();
    
    // Правильно добавляем active класс
    const chatItems = document.querySelectorAll(".chat-item");
    chatItems.forEach(item => {
        item.classList.remove("active");
    });
    
    const activeChat = Array.from(chatItems).find(item => 
        item.textContent.includes(chat.name)
    );
    if (activeChat) {
        activeChat.classList.add("active");
    }
    
    await loadMessages();
    await loadPins();
    await updateInputState();

    connectWebSocket();

    if (isMobile) {
        requestAnimationFrame(() => {
            showChat();
        });
    }
}

async function updateChatHeader(chat) {

    const status = document.getElementById("chatStatus");
    const avatar = document.getElementById("chatAvatar");


    const deleteChatAllBtn =
        document.getElementById("deleteChatForAllBtn");

    if (deleteChatAllBtn) {
        deleteChatAllBtn.style.display =
            chat.is_favorite ? "none" : "";
    }
    // Избранное — это чат самого пользователя,
    // поэтому статус подключения здесь не показываем
    if (chat.is_favorite) {

        if (status) {
            status.textContent = "";
            status.style.display = "none";
        }

        if (avatar) {

            avatar.innerHTML = "";

            if (chat.avatar) {

                const img = document.createElement("img");

                img.src = `${API_URL}${chat.avatar}`;
                img.className =
                    chat.is_favorite
                        ? "favorite-avatar-image"
                        : "chat-avatar-image";

                avatar.appendChild(img);

            } else {

                avatar.textContent =
                    chat.name?.charAt(0).toUpperCase() || "?";
            }

            avatar.style.display = "flex";
        }

        document.getElementById("chatName").textContent =
            chat.name;

        document.getElementById("chatSearchBtn").style.display =
            "block";

        document.getElementById("chatMoreWrapper").style.display =
            "flex";

        return;
    }

    // Обычный чат — статус показываем
    if (status) {
        status.style.display = "";
    }

    const otherUserId =
        chat.members?.find(
            id => Number(id) !== Number(currentUserId)
        );

    // Защита от /users/undefined/...
    if (!otherUserId) {

        logger.warn(
            "Не найден собеседник для чата",
            chat
        );
        if (status) {
            status.textContent = "";
            status.style.display = "none";
        }

        return;
    }

    const response = await fetch(
        `${API_URL}/users/${otherUserId}/block-status`,
        {
            headers: {
                Authorization: `Bearer ${token}`
            }
        }
    );

    if (!response.ok) {
        logger.error(
            "Ошибка получения block-status",
            response.status
        );
        return;
    }

    const block = await response.json();

    avatar.innerHTML = "";

    if (block.blocked_me) {

        avatar.textContent =
            chat.name?.charAt(0).toUpperCase() || "?";

    } else if (chat.avatar) {

        const img = document.createElement("img");

        img.src = `${API_URL}${chat.avatar}`;
        img.className =
            chat.is_favorite
                ? "favorite-avatar-image"
                : "chat-avatar-image";

        avatar.appendChild(img);

    } else {

        avatar.textContent =
            chat.name?.charAt(0).toUpperCase() || "?";
    }

    avatar.style.display = "flex";

    document.getElementById("chatName").textContent =
        chat.name;

    document.getElementById("chatSearchBtn").style.display =
        "block";

    document.getElementById("chatMoreWrapper").style.display =
        "flex";
}

async function loadMessages() {
    try {
        
        const response = await fetch(`${API_URL}/messages/?chat_id=${currentChatId}&limit=50`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        
        if (!response.ok) {
            logger.error(
                "Ошибка загрузки сообщений",
                response.status
            );
            return;
        }
        
        const messages = await response.json();
        messages.forEach(msg => {
            cacheMessage(msg);
        });
        const container = document.getElementById("messagesContainer");
        clearChat();
        
        messages.forEach(msg => {
            messageIds.add(msg.id);
            addMessageToUI(msg);
        });
        
        scrollToBottom(
            document.getElementById("messagesContainer")
        );

        if (messages.length > 0) {
            oldestMessageId = messages[0].id;
        }
        allMessagesLoaded =
            messages.length < 50;
        
    } catch (error) {
        logger.error(
            "Ошибка загрузки сообщений",
            error
        );
    }
}

async function loadOlderMessages() {

    if (
        loadingMoreMessages ||
        allMessagesLoaded ||
        !oldestMessageId
    ) {
        return;
    }

    loadingMoreMessages = true;

    try {

        const response = await fetch(
            `${API_URL}/messages/?chat_id=${currentChatId}&limit=50&before_id=${oldestMessageId}`,
            {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            logger.error(
                "Ошибка загрузки старых сообщений",
                response.status
            );
            return;
        }

        const messages = await response.json();
        messages.forEach(msg => {
            cacheMessage(msg);
        });

        if (messages.length === 0) {

            allMessagesLoaded = true;
            return;

        }

        oldestMessageId =
            messages[0].id;

        if (messages.length < 50) {

            allMessagesLoaded = true;

        }

        prependMessages(messages);

    } finally {

        loadingMoreMessages = false;

    }
}

function prependMessages(messages) {

    const container =
        document.getElementById(
            "messagesContainer"
        );

    if (!messages.length) {
        return;
    }
    restoringScrollPosition = true;
    /*
     * Запоминаем реальную позицию пользователя.
     */
    const oldScrollHeight =
        container.scrollHeight;

    const oldScrollTop =
        container.scrollTop;

    /*
     * На время изменения DOM отключаем
     * browser scroll anchoring.
     */
    const oldOverflowAnchor =
        container.style.overflowAnchor;

    container.style.overflowAnchor = "none";

    /*
     * Первый message в текущем DOM.
     */
    const firstMessage =
        container.querySelector(".message");

    /*
     * Создаём только сами сообщения.
     *
     * Даты здесь НЕ создаём вообще.
     */
    const fragment =
        document.createDocumentFragment();

    messages.forEach(msg => {

        const div =
            createMessageElement(msg);

        div.innerHTML =
            buildMessageContent(msg);

        fragment.appendChild(div);

        postRenderHooks(
            div,
            msg,
            container
        );
    });

    /*
     * Вставляем старые сообщения перед
     * самым первым существующим message.
     */
    if (firstMessage) {

        container.insertBefore(
            fragment,
            firstMessage
        );

    } else {

        container.appendChild(
            fragment
        );
    }

    /*
     * Теперь полностью пересобираем даты.
     *
     * Это гарантирует:
     *
     * 19 августа
     * message
     * message
     *
     * 20 августа
     * message
     * message
     */
    rebuildDateSeparators(container);

    /*
     * Высота после вставки.
     */
    const newScrollHeight =
        container.scrollHeight;

    const heightDiff =
        newScrollHeight -
        oldScrollHeight;

    /*
     * Возвращаем пользователя ровно туда,
     * где он находился до загрузки.
     */
    container.scrollTop =
        oldScrollTop + heightDiff;

    /*
     * Возвращаем browser scroll anchoring.
     */
    container.style.overflowAnchor =
        oldOverflowAnchor;

    restoringScrollPosition = false;
}


async function loadPins() {

    try {

        const response =
            await fetch(
                `${API_URL}/chats/${currentChatId}/pins`,
                {
                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );

        if (!response.ok) {
            return;
        }

        pinnedMessages =
            await response.json();

        currentPinnedIndex = 0;

        renderPinnedPreview();

    } catch (error) {
        logger.error(
            "Ошибка загрузки закреплённых сообщений",
            error
        );
    }
}

function renderPinnedPreview() {

    const preview =
        document.getElementById(
            "pinnedPreview"
        );

    if (
        !pinnedMessages.length
    ) {

        preview.style.display =
            "none";

        return;
    }

    preview.style.display =
        "flex";

    const pin =
        pinnedMessages[
            currentPinnedIndex
        ];

    document.getElementById(
        "pinnedCounter"
    ).textContent =
        `Закреплённое сообщение #${pinnedMessages.length - currentPinnedIndex}`;

    document.getElementById(
        "pinnedText"
    ).textContent =
        pin.content;
}

async function jumpToMessage(messageId) {

    const target =
        await ensureMessageLoaded(
            messageId
        );

    if (!target) {

        showToast(
            "Сообщение не найдено"
        );

        return;
    }

    target.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

    target.classList.add(
        "message-jump-highlight"
    );

    setTimeout(() => {

        target.classList.remove(
            "message-jump-highlight"
        );

    }, 2000);
}


function sendMessage() {

    const input =
        document.getElementById("messageInput");

    const content =
        input.value.trim();

    if (!content || !currentChatId || !socket) {
        return;
    }

    if (socket.readyState !== WebSocket.OPEN) {
        showToast("❌ Соединение потеряно");
        return;
    }

    sendSocket({
        type: "message",
        content,
        reply_to_id: replyToMessage
            ? replyToMessage.id
            : null
    });

    input.value = "";

    sendSocket({
        type: "stop_typing"
    });

    updateInputButtons();
    cancelReply();

    input.focus();
}


let typingStopTimeout = null;

function sendTyping() {

    if (!socket || socket.readyState !== WebSocket.OPEN)
        return;

    const now = Date.now();

    if (now - lastTypingSent > 1500) {

        lastTypingSent = now;

        sendSocket({
            type: "typing"
        });

    }

    clearTimeout(typingStopTimeout);

    typingStopTimeout = setTimeout(() => {

        sendSocket({
            type: "stop_typing"
        });

    }, 1500);
}


function handleSend() {

    const input =
        document.getElementById(
            "messageInput"
        );

    const content =
        input.value.trim();

    if (!content) {
        return;
    }

    if (editingMessage) {

        sendEditedMessage(content);

        return;
    }

    sendMessage();
}

function clearChat() {

    const container =
        document.getElementById(
            "messagesContainer"
        );

    container.innerHTML = "";

    messageIds.clear();

}

async function handleDeletedAccount(userId) {

    const deletedUserId = Number(userId);

    if (
        !currentCompanionId ||
        Number(currentCompanionId) !== deletedUserId
    ) {
        return;
    }

    // Обновляем данные в памяти чатов
    const chat = allChats.find(
        chat =>
            Number(chat.id) === Number(currentChatId)
    );

    if (chat) {
        chat.name = "Аккаунт удалён";
        chat.avatar = "/storage/ghost.png";
        chat.deleted = true;
    }

    // Обновляем заголовок
    const chatName =
        document.getElementById("chatName");

    if (chatName) {
        chatName.textContent =
            "Аккаунт удалён";
    }

    // Обновляем аватар
    const avatar =
        document.getElementById("chatAvatar");

    if (avatar) {

        avatar.innerHTML = "";

        const img =
            document.createElement("img");

        img.src =
            `${API_URL}/storage/ghost.png`;

        img.className =
            chat.is_favorite
                ? "favorite-avatar-image"
                : "chat-avatar-image";

        avatar.appendChild(img);

        avatar.style.display = "flex";
    }

    // Обновляем статус
    const status =
        document.getElementById("chatStatus");

    if (status) {
        status.textContent =
            "Был(а) в сети очень давно";

        status.style.color = "";
    }

    // Запрещаем писать
    const inputArea =
        document.getElementById("inputArea");

    const panel =
        document.getElementById("chatBlockedPanel");

    if (inputArea) {
        inputArea.style.display = "none";
    }

    if (panel) {
        panel.style.display = "flex";
        panel.textContent =
            "Пользователь удалил аккаунт";
    }

    // Обновляем sidebar
    await renderChats();
}

function updateInputButtons() {

    if (isRecording)
        return;

    if (messageInput.value.trim() === "") {

        sendBtn.style.display = "none";
        voiceBtn.style.display = "flex";

    } else {

        sendBtn.style.display = "flex";
        voiceBtn.style.display = "none";

    }

}

messageInput.addEventListener(
    "input",
    updateInputButtons
);

updateInputButtons();


async function updateInputState() {
    const chat = allChats.find(
        c => Number(c.id) === Number(currentChatId)
    );

    if (chat?.is_favorite) {

        const inputArea =
            document.getElementById("inputArea");

        const panel =
            document.getElementById("chatBlockedPanel");

        if (inputArea) {
            inputArea.style.display = "flex";
        }

        if (panel) {
            panel.style.display = "none";
        }

        return;
    }
    if (!currentChatId)
        return;

    if (!currentCompanionId)
        return;

    const response = await fetch(
        `${API_URL}/users/${currentCompanionId}/block-status`,
        {
            headers:{
                Authorization:`Bearer ${token}`
            }
        }
    );

    if (!response.ok)
        return;

    const status =
        await response.json();

    const userResponse = await fetch(
        `${API_URL}/users/${currentCompanionId}`,
        {
            headers: {
                Authorization: `Bearer ${token}`
            }
        }
    );

    if (!userResponse.ok)
        return;

    const user = await userResponse.json();

    const inputArea =
        document.getElementById("inputArea");

    const panel =
        document.getElementById("chatBlockedPanel");

    if (!panel || !inputArea)
        return;

    if (user.is_deleted) {

        panel.style.display = "flex";
        panel.textContent = "Пользователь удалил аккаунт";

        inputArea.style.display = "none";

    }

    else if (status.i_blocked) {

        panel.style.display = "flex";
        panel.textContent = "Вы заблокировали пользователя";

        inputArea.style.display = "none";

    }

    else if (status.blocked_me) {

        panel.style.display = "flex";
        panel.textContent = "Вас заблокировали";

        inputArea.style.display = "none";

    }

    else {

        panel.style.display = "none";
        inputArea.style.display = "flex";

    }

}

async function refreshChatOnVisible() {

    if (!currentChatId) {
        return;
    }


    // 1. Актуальные сообщения
    await loadMessages();

    // 2. Актуальные закреплённые
    await loadPins();

    // 3. Актуальный статус/блокировка пользователя
    if (currentCompanionId) {

        await loadUserStatus(
            currentCompanionId
        );

        await updateInputState();
    }


    if (
        typeof socket === "undefined" ||
        !socket ||
        socket.readyState !== WebSocket.OPEN
    ) {
        connectWebSocket();
    }

    // 5. Если чат открыт — сразу отмечаем сообщения прочитанными
    markChatAsRead(currentChatId);
}


async function ensureMessageLoaded(messageId) {

    messageId = Number(messageId);

    if (!messageId) {
        return null;
    }

    let target =
        document.querySelector(
            `[data-message-id="${messageId}"]`
        );

    if (target) {
        return target;
    }

    /*
     * Пока нужное сообщение не появилось
     * в DOM — грузим историю порциями.
     */
    while (
        !allMessagesLoaded &&
        oldestMessageId &&
        messageId < Number(oldestMessageId)
    ) {

        const previousOldest =
            oldestMessageId;

        await loadOlderMessages();

        /*
         * Защита от бесконечного цикла,
         * если API по какой-то причине
         * возвращает тот же oldestMessageId.
         */
        if (
            oldestMessageId === previousOldest
        ) {
            break;
        }

        target =
            document.querySelector(
                `[data-message-id="${messageId}"]`
            );

        if (target) {
            return target;
        }
    }

    return document.querySelector(
        `[data-message-id="${messageId}"]`
    );
}

const container =
    document.getElementById(
        "messagesContainer"
    );

container.addEventListener(
    "scroll",
    async () => {

        if (
            restoringScrollPosition
        ) {
            return;
        }

        if (
            loadingMoreMessages ||
            allMessagesLoaded
        ) {
            return;
        }

        if (
            container.scrollTop < 200
        ) {

            await loadOlderMessages();

        }

    }
);