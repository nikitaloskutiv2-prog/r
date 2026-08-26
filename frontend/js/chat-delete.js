const chatMoreWrapper =
    document.getElementById("chatMoreWrapper");

const chatMoreBtn =
    document.getElementById("chatMoreBtn");

const chatMoreMenu =
    document.getElementById("chatMoreMenu");

const deleteChatSelfBtn =
    document.getElementById("deleteChatForMeBtn");

const deleteChatAllBtn =
    document.getElementById("deleteChatForAllBtn");

const chatDeleteModal =
    document.getElementById("chatDeleteModal");

const chatDeleteCancel =
    document.getElementById("chatDeleteCancel");

const chatDeleteConfirm =
    document.getElementById("chatDeleteConfirm");

const chatDeleteModalTitle =
    document.getElementById("chatDeleteModalTitle");

const chatDeleteModalText =
    document.getElementById("chatDeleteModalText");


let chatDeleteAction = null;

function initChatDeleteMenu() {

    if (!chatMoreBtn || !chatMoreMenu) {
        return;
    }

    chatMoreBtn.addEventListener(
        "click",
        (event) => {

            event.stopPropagation();

            chatMoreMenu.classList.toggle("show");

        }
    );


    document.addEventListener(
        "click",
        () => {

            chatMoreMenu.classList.remove("show");

        }
    );


    chatMoreMenu.addEventListener(
        "click",
        (event) => {

            event.stopPropagation();

        }
    );


    deleteChatSelfBtn.addEventListener(
        "click",
        deleteChatForMe
    );


    deleteChatAllBtn.addEventListener(
        "click",
        deleteChatForAll
    );
}



async function deleteChatForMe() {

    if (!currentChatId) {
        return;
    }
    logger.info("Delete chat for me requested", {
        chatId: currentChatId
    });
    chatMoreMenu.classList.remove("show");

    openChatDeleteModal("self");
}



async function deleteChatForAll() {

    if (!currentChatId) {
        return;
    }
    logger.info("Delete chat for all requested", {
        chatId: currentChatId
    });
    chatMoreMenu.classList.remove("show");

    openChatDeleteModal("all");
}


function closeDeletedChat() {
    logger.info("Closing deleted chat", {
        chatId: currentChatId
    });
    disconnectWebSocket(true);

    currentChatId = null;
    currentCompanionId = null;

    clearChat();

    document.getElementById(
        "chatName"
    ).textContent =
        "Выберите чат";

    document.getElementById(
        "chatStatus"
    ).textContent =
        "";

    document.getElementById(
        "chatAvatar"
    ).style.display =
        "none";

    document.getElementById(
        "chatSearchBtn"
    ).style.display =
        "none";

    chatMoreWrapper.style.display =
        "none";

    document.getElementById(
        "inputArea"
    ).style.display =
        "none";

    document.getElementById(
        "chatBlockedPanel"
    ).style.display =
        "none";

    if (isMobile) {
        goBack();
    }
}

function removeChatFromSidebar(chatId) {
    logger.info("Removing chat from sidebar", {
        chatId
    });
    chatId = Number(chatId);

    allChats = allChats.filter(
        chat => Number(chat.id) !== chatId
    );

    const chatItem =
        document.querySelector(
            `.chat-item[data-chat-id="${chatId}"]`
        );

    if (chatItem) {
        chatItem.remove();
    }

    if (allChats.length === 0) {

        document.getElementById(
            "chatsList"
        ).innerHTML =
            '<div class="empty-sidebar-message">Нет чатов. Найдите пользователя.</div>';
    }
}

async function performDeleteChatForMe() {

    if (!currentChatId) {
        return;
    }
    logger.info("Deleting chat for me", {
        chatId: currentChatId
    });
    try {

        const response =
            await fetch(
                `${API_URL}/chats/${currentChatId}/delete-for-me`,
                {
                    method: "DELETE",
                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );

        if (!response.ok) {

            const error =
                await response.json()
                    .catch(() => ({}));

            logger.warn("Delete chat for me failed", {
                chatId: currentChatId,
                status: response.status,
                detail: error.detail
            });
            showToast(
                error.detail ||
                "Не удалось удалить чат"
            );

            return;
        }

        const deletedChatId =
            Number(currentChatId);

        removeChatFromSidebar(
            deletedChatId
        );

        closeDeletedChat();
        logger.info("Chat deleted for me", {
            chatId: deletedChatId
        });
        showToast(
            "Чат удалён у вас"
        );

    } catch (error) {

        logger.error(
            "Delete chat for me error",
            error
        );

        showToast(
            "Ошибка удаления чата"
        );
    }
}

async function performDeleteChatForAll() {

    if (!currentChatId) {
        return;
    }
    logger.info("Deleting chat for all", {
        chatId: currentChatId
    });
    try {

        const response =
            await fetch(
                `${API_URL}/chats/${currentChatId}/delete-for-all`,
                {
                    method: "DELETE",
                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );

        if (!response.ok) {

            const error =
                await response.json()
                    .catch(() => ({}));
            logger.warn("Delete chat for all failed", {
                chatId: currentChatId,
                status: response.status,
                detail: error.detail
            });
            showToast(
                error.detail ||
                "Не удалось удалить чат"
            );

            return;
        }
        logger.info("Chat deleted for all", {
            chatId: currentChatId
        });
        closeDeletedChat();
        
        showToast(
            "Чат удалён для всех"
        );

    } catch (error) {

        logger.error(
            "Delete chat for all error",
            error
        );

        showToast(
            "Ошибка удаления чата"
        );
    }
}

function openChatDeleteModal(type) {

    if (!chatDeleteModal) {
        return;
    }

    if (type === "self") {

        chatDeleteModalTitle.textContent =
            "Удалить чат у себя?";

        chatDeleteModalText.textContent =
            "Чат будет удалён только у вас. У собеседника он останется.";

    } else {

        chatDeleteModalTitle.textContent =
            "Удалить чат для всех?";

        chatDeleteModalText.textContent =
            "Все сообщения и файлы этого чата будут удалены для всех участников. Это действие нельзя отменить.";

    }

    chatDeleteAction = type;
    logger.info("Chat delete confirmation opened", {
        chatId: currentChatId,
        action: type
    });
    chatDeleteModal.classList.add("active");
}


function closeChatDeleteModal() {

    chatDeleteModal.classList.remove("active");

    chatDeleteAction = null;
}


chatDeleteCancel.addEventListener(
    "click",
    closeChatDeleteModal
);


chatDeleteConfirm.addEventListener(
    "click",
    async () => {

        const action = chatDeleteAction;
        logger.info("Chat delete confirmed", {
            chatId: currentChatId,
            action
        });
        closeChatDeleteModal();

        if (action === "self") {

            await performDeleteChatForMe();

        } else if (action === "all") {

            await performDeleteChatForAll();

        }

    }
);


chatDeleteModal.addEventListener(
    "click",
    (event) => {

        if (event.target === chatDeleteModal) {
            closeChatDeleteModal();
        }

    }
);


document.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key === "Escape" &&
            chatDeleteModal.classList.contains("active")
        ) {
            closeChatDeleteModal();
        }

    }
);