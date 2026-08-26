let currentPinnedIndex = 0;
let pinnedMessages = [];

function initPin() {
    document.getElementById("pinMessageBtn")
        ?.addEventListener("click",pinMessage);

    document
        .getElementById(
            "pinnedPreview"
        )
        ?.addEventListener(
            "click",
            () => {

                if (
                    !pinnedMessages.length
                ) {
                    return;
                }

                const pin =
                    pinnedMessages[
                        currentPinnedIndex
                    ];

                jumpToMessage(
                    pin.message_id
                );

                if (
                    currentPinnedIndex <
                    pinnedMessages.length - 1
                ) {

                    currentPinnedIndex++;

                } else {

                    currentPinnedIndex = 0;
                }

                renderPinnedPreview();
            }
        );
}



function togglePin() {
    logger.debug(
        "Переключение закрепления сообщения",
        {
            messageId: selectedMessageId
        }
    );
    if (!selectedMessageId) return;

    sendSocket({
        type: "toggle_pin",
        message_id: selectedMessageId
    });

    closeContextMenu();
}

async function pinMessage() {
    logger.debug(
        "Изменение закрепления сообщения",
        {
            messageId: selectedMessage?.id,
            chatId: currentChatId
        }
    );
    if (!selectedMessage) {
        return;
    }

    const isPinned =
        pinnedMessages.some(
            pin =>
                pin.message_id ===
                selectedMessage.id
        );

    try {

        let response;

        if (isPinned) {

            response =
                await fetch(
                    `${API_URL}/chats/${currentChatId}/pins/${selectedMessage.id}`,
                    {
                        method: "DELETE",

                        headers: {
                            "Authorization":
                                `Bearer ${token}`
                        }
                    }
                );

        } else {

            response =
                await fetch(
                    `${API_URL}/chats/${currentChatId}/pins`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "Authorization":
                                `Bearer ${token}`
                        },

                        body: JSON.stringify({
                            message_id:
                                selectedMessage.id
                        })
                    }
                );
        }

        if (!response.ok) {

            logger.warn(
                "Не удалось изменить закрепление сообщения",
                {
                    messageId: selectedMessage.id,
                    chatId: currentChatId,
                    status: response.status
                }
            );

            return;
        }
        document
            .getElementById(
                "messageContextMenu"
            )
            .style.display = "none";
        showToast(
            isPinned
                ? "Сообщение откреплено"
                : "Сообщение закреплено"
        );
        logger.info(
            isPinned
                ? "Сообщение откреплено"
                : "Сообщение закреплено",
            {
                messageId: selectedMessage.id,
                chatId: currentChatId
            }
        );

    } catch (error) {

        logger.error(
            "Ошибка изменения закрепления сообщения",
            error
        );
    }
}

function getPinnedPreviewText(pin) {

    if (!pin.file) {
        return pin.content || "";
    }

    let title = "";

    if (pin.file.mime_type?.startsWith("image/")) {

        title = "📷 Фото";

    } else if (pin.file.mime_type?.startsWith("video/")) {
        title = "🎥 Видео";

    } else if (pin.voice_duration != null) {

        title = "🎤 Голосовое сообщение";

    } else {

        title = `📄 ${pin.file.original_name}`;
    }

    if (pin.content?.trim()) {

        return `${title}\n${pin.content}`;

    }

    return title;
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
        getPinnedPreviewText(pin);
}