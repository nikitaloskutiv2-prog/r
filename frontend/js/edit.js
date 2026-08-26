let editingMessage = null;


function initEdit() {

    document
        .getElementById("editMessageBtn")
        ?.addEventListener(
            "click",
            startEditMessage
        );

    document
        .getElementById("cancelEditBtn")
        ?.addEventListener(
            "click",
            cancelEdit
        );
}

function startEditMessage() {
    cancelReply()
    if (!selectedMessage)
        return;

    editingMessage = selectedMessage;

    document.getElementById(
        "editPreview"
    ).style.display = "flex";

    document.getElementById(
        "editPreviewText"
    ).textContent =
        editingMessage.content;

    const input =
        document.getElementById(
            "messageInput"
        );

    input.value =
        editingMessage.content;

    input.focus();

    document.getElementById(
        "messageContextMenu"
    ).style.display = "none";
}

function cancelEdit() {

    editingMessage = null;

    document.getElementById(
        "editPreview"
    ).style.display = "none";
}

function sendEditedMessage(content) {

    sendSocket({
        type: "edit_message",
        message_id: editingMessage.id,
        content
    });

    editingMessage = null;

    cancelEdit();

    const input =
        document.getElementById("messageInput");

    input.value = "";

    input.focus();
}