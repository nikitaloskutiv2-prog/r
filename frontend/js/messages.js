let typingTimeout = null;
let liveActivity = null;


function postRenderHooks(div, msg, container) {

    attachMediaClick(div, msg);

    attachVideoLoader(div);

    attachVoicePlayer(div);

    attachReplyClick(div);

    attachContextMenu(div, msg);

    attachReactions(div, msg);

    const waveform =
        div.querySelector(".voice-waveform");

    if (
        waveform &&
        msg.waveform
    ) {
        drawWaveformFromData(
            msg.waveform,
            waveform
        );
    }
}


function attachMediaClick(div, msg) {

    if (!msg.file) return;

    const media =
        div.querySelector(
            ".message-image, .message-video-preview"
        );

    if (!media) return;

    media.addEventListener("click", () => {

        openMediaViewer(msg.file);

    });
}

function attachVideoLoader(div) {

    const preview =
        div.querySelector(".message-video-preview");

    const img =
        preview?.querySelector("img");

    if (!img) return;

    const show = () => {

        img.classList.add("loaded");

        preview.classList.add("loaded");

    };

    if (img.complete) {
        show();
    } else {
        img.onload = show;
    }
}





function scrollToBottom(container) {

    container.scrollTop =
        container.scrollHeight;
}

function attachContextMenu(div, msg) {

    div.addEventListener("contextmenu", (e) => {

        e.preventDefault();

        openContextMenu(e, div, msg);

    });
}

function getMessageText(msg){

    return (
        msg?.content?.trim() || ""
    );

}


function handleMessageEvent(event) {
    const msg = JSON.parse(event.data);

    switch (msg.type) {

        case "new_message":
            handleNewMessage(msg.message ?? msg);
            break;

        case "message_edited":
            handleEditMessage(msg);
            break;

        case "message_deleted":
            handleDeleteMessage(msg);
            break;

        case "message_deleted_for_me":
            handleDeleteMessage(msg);
            break;

        case "message_read":
            handleMessageRead(msg);
            break;

        case "reaction_updated":
            handleReactionUpdated(msg);
            break;

        case "message_pinned":
            handlePinned(msg);
            break;

        case "message_unpinned":
            handleUnpinned(msg);
            break;

        case "chat_read_all":
            handleChatReadAll(msg);
            break;

        case "typing":
            handleTyping(msg);
            break;

        case "stop_typing":
            handleStopTyping(msg);
            break;

        case "voice_played":
            handleVoicePlayed(msg);
            break;
        
        case "voice_recording":
            handleVoiceRecording(msg);
            break;

        case "voice_recording_stop":
            handleVoiceRecordingStop(msg);
            break;

        case "block_status_changed": {

            if (!currentChatId)
                break;

            const otherUserId = getCurrentCompanionId();

            if (otherUserId) {
                loadUserStatus(otherUserId);
            }

            break;
        }

        default:
            logger.warn(
                "Unknown websocket message",
                msg
            );
    }
}


function handleMessageRead(msg) {

    updateMessageReadStatus(
        msg.message_id
    );

    allChats.forEach(chat => {

        if (
            chat.last_message &&
            chat.last_message.id === msg.message_id
        ) {

            chat.last_message.is_read = true;

        }

    });

    renderChats();

}

function handlePinned() {

    loadPins();

    showToast(
        "Сообщение закреплено"
    );

}

function handleUnpinned() {

    loadPins();

    showToast(
        "Сообщение откреплено"
    );

}



function handleChatReadAll(msg) {

    if (
        msg.user_id === currentUserId
    ) {
        return;
    }

    document
        .querySelectorAll(
            ".message-status-badges.unread"
        )
        .forEach(el => {

            el.classList.remove(
                "unread"
            );

            el.textContent =
                "✓✓";

        });

    unreadCounts[msg.chat_id] = 0;

    updateChatBadges();

    const chat =
        allChats.find(
            c => c.id === msg.chat_id
        );

    if (chat?.last_message) {

        chat.last_message.is_read = true;

    }

    renderChats();

}

function handleTyping() {
    liveActivity = "typing";
    const status =
        document.getElementById(
            "chatStatus"
        );

    status.innerHTML = `
        печатает
        <span class="typing-dots">
            <span></span><span></span><span></span>
        </span>
    `;

    status.style.color =
        "#34c759";

    clearTimeout(
        typingTimeout
    );

    typingTimeout =
        setTimeout(async () => {

            const otherUserId =
                allChats
                    .find(
                        c => c.id === currentChatId
                    )
                    ?.members.find(
                        id =>
                            id !== currentUserId
                    );

            if (otherUserId) {

                await loadUserStatus(
                    otherUserId
                );

            }

        }, 3000);

}

function handleStopTyping() {
    liveActivity = null;
    clearTimeout(
        typingTimeout
    );

    const otherUserId =
        allChats
            .find(
                c => c.id === currentChatId
            )
            ?.members.find(
                id =>
                    id !== currentUserId
            );

    if (otherUserId) {

        loadUserStatus(
            otherUserId
        );

    }

}

function handleNewMessage(msg) {
    logger.debug(
        "Получено новое сообщение",
        {
            messageId: msg?.message?.id ?? msg?.id,
            chatId: msg?.message?.chat_id ?? msg?.chat_id
        }
    );
    const message =
        msg.message || msg;

    const container =
        document.getElementById(
            "messagesContainer"
        );

    if (!container) {
        return;
    }

    /*
     * Проверяем, находился ли пользователь
     * внизу ДО добавления сообщения.
     */
    const distanceFromBottom =
        container.scrollHeight -
        container.scrollTop -
        container.clientHeight;

    const wasAtBottom =
        distanceFromBottom < 100;

    cacheMessage(message);

    addMessageToUI(message);

    /*
     * Если это наше сообщение —
     * всегда уходим вниз.
     *
     * Если сообщение собеседника пришло,
     * но пользователь уже был внизу —
     * тоже уходим вниз.
     */
    if (
        message.sender_id === currentUserId ||
        wasAtBottom
    ) {

        requestAnimationFrame(() => {

            scrollToBottom(
                container
            );

        });
    }

    /*
     * Обработка входящего сообщения.
     */
    if (
        message.chat_id === currentChatId &&
        message.sender_id !== currentUserId &&
        isPageVisible &&
        document.hasFocus()
    ) {

        markChatAsRead(
            currentChatId
        );

        unreadCounts[currentChatId] = 0;

        updateChatBadges();
    }
}


function handleEditMessage(msg) {
    logger.debug(
        "Редактирование сообщения",
        {
            messageId: msg.message_id
        }
    );
    const message =
        document.querySelector(
            `[data-message-id="${msg.message_id}"]`
        );

    if (!message) return;

    // 1. обновляем текст (универсально)
    const text =
        getMessageTextElement(message);

    if (text) {
        text.textContent = msg.content;
    }

    // 2. обновляем meta
    const meta =
        message.querySelector(".message-meta");

    if (meta && !meta.querySelector(".message-edited")) {

        meta.insertAdjacentHTML(
            "afterbegin",
            `
                <span class="message-edited">
                    изменено
                </span>
            `
        );
    }

    const msgObj =
        findMessageInMemory(msg.message_id);

    if (msgObj) {
        msgObj.content = msg.content;
        msgObj.edited = true;
    }
}

function handleDeleteMessage(msg) {
    logger.debug(
        "Удаление сообщения",
        {
            messageId: msg.message_id,
            chatId: msg.chat_id
        }
    );
    const element =
        document.querySelector(
            `[data-message-id="${msg.message_id}"]`
        );

    if (element) {

        element.classList.add("deleting");

        setTimeout(() => {
            element.classList.add("collapse");
        }, 10);

        setTimeout(() => {
            element.remove();
        }, 260);
    }

    if (msg.last_message !== undefined) {

        updateChatAfterMessageDelete(
            msg.chat_id,
            msg.last_message
        );
    }
}

function getMessageTextElement(message) {

    return message.querySelector(".message-text")
        || message.querySelector(".image-caption")
        || message.querySelector(".file-caption");
}

const messageCache = new Map();

function cacheMessage(msg) {
    messageCache.set(msg.id, msg);
}

function findMessageInMemory(id) {
    return messageCache.get(id);
}

function markChatAsRead(chatId) {

    unreadCounts[chatId] = 0;
    updateChatBadges();

    if (
        socket &&
        socket.readyState === WebSocket.OPEN
    ) {

        sendSocket({
            type: "chat_read_all"
        });
    }
}

function attachVoicePlayer(div) {

    const btn =
        div.querySelector(".voice-play");

    if (!btn)
        return;

    const canvas =
        div.querySelector(".voice-waveform");

    const durationLabel =
        div.querySelector(".voice-duration");

    const audio =
        new Audio(btn.dataset.path);

    const waveform =
        JSON.parse(
            canvas.dataset.waveform || "[]"
        );

    // исходная длительность
    const totalSeconds =
        audio.duration || Number(durationLabel.dataset.duration || 0);

    // если duration пришла в тексте "00:15"
    const parseTime = (text) => {

        const parts =
            text.split(":").map(Number);

        if (parts.length === 2)
            return parts[0] * 60 + parts[1];

        return parts[0];

    };

    const originalDuration =
        Number(durationLabel.dataset.duration);

    btn.onclick = () => {

        if (audio.paused) {

            audio.play();

            btn.textContent = "⏸";

        } else {

            audio.pause();

            btn.textContent = "▶";

        }

    };

    audio.ontimeupdate = () => {

        const progress =
            audio.currentTime /
            audio.duration;

        canvas.dataset.progress =
            progress;

        drawWaveformFromData(
            waveform,
            canvas
        );

        // уменьшаем время
        const left =
            Math.max(
                0,
                Math.ceil(
                    originalDuration -
                    audio.currentTime
                )
            );

        durationLabel.textContent = formatVoiceDuration(left);

    };

    audio.onpause = () => {

        if (!audio.ended)
            btn.textContent = "▶";

    };

    audio.onended = () => {

        btn.textContent = "▶";

        canvas.dataset.progress = 0;

        drawWaveformFromData(
            waveform,
            canvas
        );

        // возвращаем исходную длительность
        durationLabel.textContent = formatVoiceDuration(originalDuration);

        if (
            socket &&
            socket.readyState === WebSocket.OPEN
        ) {

            const messageId =
                div.closest(".message").dataset.messageId;

            socket.send(JSON.stringify({
                type: "voice_played",
                message_id: Number(messageId)
            }));

        }  
    };

}

function handleVoicePlayed(msg) {
    logger.debug(
        "Голосовое сообщение прослушано",
        {
            messageId: msg.message_id
        }
    );
    const message =
        document.querySelector(
            `[data-message-id="${msg.message_id}"]`
        );

    if (!message)
        return;

    const dot =
        message.querySelector(".voice-unheard");

    if (dot)
        dot.style.visibility = "hidden";

}

function handleVoiceRecording(msg) {
    if (msg.user_id === currentUserId) return;

    liveActivity = "voice";

    const status = document.getElementById("chatStatus");

    status.innerHTML = `
        записывает голос
        <span class="typing-dots">
            <span></span><span></span><span></span>
        </span>
    `;

    status.style.color = "#34c759";
}

function handleVoiceRecordingStop(msg) {
    if (msg.user_id === currentUserId) return;

    liveActivity = null;

    const otherUserId = getCurrentCompanionId();

    if (otherUserId) {
        loadUserStatus(otherUserId);
    }
}

