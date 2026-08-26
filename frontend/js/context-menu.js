let selectedMessageId = null;
let selectedMessage = null;
let selectedMessageElement = null;

function openContextMenu(
    e,
    div,
    msg
) {

    selectedMessageId = msg.id;
    selectedMessage = msg;

    updateContextMenuButtons(msg);

    positionContextMenu(e);

    selectMessageElement(div);
}

function updateContextMenuButtons(msg) {

    const text =
        getMessageText(msg);

    const isVoiceMessage =
        msg.voice_duration != null;

    const editBtn =
        document.getElementById(
            "editMessageBtn"
        );

    editBtn.style.display =
        (
            msg.sender_id === currentUserId &&
            text
        )
            ? "block"
            : "none";

    // Удаление доступно для любого сообщения
    const deleteSelfBtn =
        document.getElementById(
            "deleteMessageSelfBtn"
        );

    const deleteAllBtn =
        document.getElementById(
            "deleteMessageAllBtn"
        );

    if (deleteSelfBtn) {
        deleteSelfBtn.style.display =
            "block";
    }

    if (deleteAllBtn) {
        deleteAllBtn.style.display =
            "block";
    }

    const copyBtn =
        document.getElementById(
            "copyMessageBtn"
        );

    copyBtn.style.display =
        text
            ? "block"
            : "none";

    const pinBtn =
        document.getElementById(
            "pinMessageBtn"
        );

    const isPinned =
        pinnedMessages.some(
            pin =>
                pin.message_id === msg.id
        );

    pinBtn.textContent =
        isPinned
            ? "Открепить"
            : "Закрепить";

    const downloadBtn =
        document.getElementById(
            "downloadFileBtn"
        );

    downloadBtn.style.display =
        (msg.file && !isVoiceMessage)
            ? "block"
            : "none";
}

function positionContextMenu(e) {

    const menu =
        document.getElementById(
            "messageContextMenu"
        );

    menu.style.display =
        "block";

    const menuWidth =
        menu.offsetWidth;

    const menuHeight =
        menu.offsetHeight;

    const padding = 10;

    let left =
        e.pageX;

    let top =
        e.pageY;

    if (
        left + menuWidth >
        window.innerWidth
    ) {

        left =
            window.innerWidth -
            menuWidth -
            padding;
    }

    if (
        top + menuHeight >
        window.innerHeight
    ) {

        top =
            window.innerHeight -
            menuHeight -
            padding;
    }

    left =
        Math.max(
            padding,
            left
        );

    top =
        Math.max(
            padding,
            top
        );

    menu.style.left =
        `${left}px`;

    menu.style.top =
        `${top}px`;
}

function selectMessageElement(div) {

    if (
        selectedMessageElement
    ) {

        selectedMessageElement.classList.remove(
            "context-selected"
        );
    }

    selectedMessageElement =
        div;

    selectedMessageElement.classList.add(
        "context-selected"
    );
}

function closeContextMenu() {

    document
        .getElementById(
            "messageContextMenu"
        )
        .style.display = "none";

    if (selectedMessageElement) {

        selectedMessageElement.classList.remove(
            "context-selected"
        );

        selectedMessage = null;
        selectedMessageId = null;
        selectedMessageElement = null;
    }

    document.getElementById(
        "messagesContainer"
    ).style.overflow = "";
}

function deleteMessageForMe() {

    if (!selectedMessageId) {
        return;
    }

    sendSocket({
        type: "delete_message_self",
        message_id: selectedMessageId
    });

    closeContextMenu();
}

function deleteMessageForEveryone() {

    if (!selectedMessageId) {
        return;
    }

    sendSocket({
        type: "delete_message_all",
        message_id: selectedMessageId
    });

    closeContextMenu();
}

function copyMessage() {

    if (!selectedMessage)
        return;

    navigator.clipboard.writeText(
        selectedMessage.content
    );

    closeContextMenu();

    showToast(
        "Текст скопирован"
    );
}

function initContextMenu() {

    document.addEventListener(
        "click",
        (e) => {

            const menu =
                document.getElementById(
                    "messageContextMenu"
                );

            if (
                !menu.contains(
                    e.target
                )
            ) {

                closeContextMenu();
            }
        }
    );

    document
        .getElementById(
            "deleteMessageSelfBtn"
        )
        ?.addEventListener(
            "click",
            deleteMessageForMe
        );

    document
        .getElementById(
            "deleteMessageAllBtn"
        )
        ?.addEventListener(
            "click",
            deleteMessageForEveryone
        );

    document
        .getElementById(
            "copyMessageBtn"
        )
        ?.addEventListener(
            "click",
            copyMessage
        );

    document
        .getElementById(
            "downloadFileBtn"
        )
        ?.addEventListener(
            "click",
            async () => {

                if (
                    !selectedMessage ||
                    !selectedMessage.file
                ) {
                    return;
                }

                const file =
                    selectedMessage.file;

                const fileId =
                    file.id;

                const fileName =
                    file.original_name ||
                    "file";

                await downloadFile(
                    fileId,
                    fileName
                );
            }
        );
}

