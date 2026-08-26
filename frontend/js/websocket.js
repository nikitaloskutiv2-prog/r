let socket = null;
let intentionallyClosed = false;

function initSocketEvents() {

    socket.addEventListener(
        "open",
        handleSocketOpen
    );

    socket.addEventListener(
        "close",
        handleSocketClose
    );

    socket.addEventListener(
        "error",
        handleSocketError
    );

    socket.addEventListener(
        "message",
        handleMessageEvent
    );

}

function connectWebSocket() {

    if (socket) {
        disconnectWebSocket(true);
    }

    intentionallyClosed = false;

    socket = new WebSocket(
        `ws://${WAPI_URL}/ws/chat/${currentChatId}?token=${token}`
    );

    initSocketEvents();
}


function disconnectWebSocket(silent = false) {

    if (!socket) {
        return;
    }

    intentionallyClosed = silent;

    socket.close();
    socket = null;
}


function handleSocketClose() {
    if (intentionallyClosed) {
        return;
    }

    document.getElementById(
        "chatStatus"
    ).textContent = "Подключение";
}

function sendSocket(data) {

    if (
        !socket ||
        socket.readyState !== WebSocket.OPEN
    ) {

        return false;

    }

    socket.send(
        JSON.stringify(data)
    );

    return true;

}


function handleSocketOpen() {
    markChatAsRead(currentChatId);

    const otherUserId =
        allChats
            .find(
                c => c.id === currentChatId
            )
            ?.members.find(
                id => id !== currentUserId
            );

    if (otherUserId) {

        loadUserStatus(
            otherUserId
        );

    }

}



function handleSocketError(error) {

    logger.error(
        "WebSocket error:",
        error
    );

    document.getElementById(
        "chatStatus"
    ).textContent =
        "Ошибка";

}