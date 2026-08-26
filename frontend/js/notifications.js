
let notificationSocket = null;
let unreadCounts = {};

function initNotifications() {
    connectNotifications();
}

function connectNotifications() {

    notificationSocket = new WebSocket(
        `ws://${WAPI_URL}/ws/notifications?token=${token}`
    );

    notificationSocket.onopen = () => {
        logger.info("Notifications connected");
    };

    notificationSocket.onmessage = async (event) => {

        const msg = JSON.parse(event.data);
        logger.debug(
            "Notification received",
            {
                type: msg.type,
                chatId: msg.chat_id,
                userId: msg.user_id
            }
        );
        if (msg.type === "unread_update") {

            await loadUnreadCounts();

            if (Number(msg.chat_id) === Number(currentChatId)) {
                unreadCounts[currentChatId] = 0;
            }

            updateChatBadges();
        }

        else if (msg.type === "chat_updated") {

            handleChatUpdated(msg.chat);
        }
        else if (msg.type === "user_status_changed") {

            const changedUserId = Number(msg.user_id);

            updateSidebarOnlineStatus(
                changedUserId,
                msg.status === "online"
            );

            if (
                currentCompanionId &&
                Number(currentCompanionId) === changedUserId
            ) {
                await loadUserStatus(changedUserId);
            }
        }

        else if (msg.type === "chat_deleted") {

            await handleChatDeleted(msg);
        }

        else if (msg.type === "message_deleted") {

            handleDeleteMessage(msg);

            if (
                msg.delete_for === "self" &&
                msg.last_message !== undefined
            ) {

                updateChatAfterMessageDelete(
                    msg.chat_id,
                    msg.last_message
                );
            }
        }

        else if (msg.type === "block_status_changed") {

            if (currentChatId) {

                await updateInputState();

                if (currentCompanionId) {
                    await loadUserStatus(
                        currentCompanionId
                    );
                }
            }

            await renderChats();
        }
        else if (msg.type === "account_deleted") {

            const deletedUserId =
                Number(msg.user_id);

            if (
                currentCompanionId &&
                Number(currentCompanionId) === deletedUserId
            ) {

                await handleDeletedAccount(
                    deletedUserId
                );
            }

        }
    };

    notificationSocket.onclose = () => {
        logger.warn("Notifications disconnected");
    };
}

function sendNotificationVisibilityStatus(status) {

    if (
        notificationSocket &&
        notificationSocket.readyState === WebSocket.OPEN
    ) {
        logger.debug(
            "Sending notification visibility status",
            {
                status
            }
        );
        notificationSocket.send(
            JSON.stringify({
                type: "visibility_changed",
                status: status
            })
        );

    }

}