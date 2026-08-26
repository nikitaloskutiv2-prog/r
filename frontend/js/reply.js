let replyToMessage = null;

function initReply() {

    document
        .getElementById("replyMessageBtn")
        ?.addEventListener(
            "click",
            startReply
        );

    document
        .getElementById("cancelReplyBtn")
        ?.addEventListener(
            "click",
            cancelReply
        );

}

function buildReplyHtml(msg) {
    if (!msg.reply_to) {
        return "";
    }

    const author =
        msg.reply_to.sender_id === currentUserId
            ? "Вы"
            : document
                .getElementById("chatName")
                .textContent;

    let preview = "";



    if (msg.reply_to.file) {
        if (msg.reply_to.file.mime_type.startsWith("image/")) {

            preview = "📷 Фото";

        }
        else if (msg.reply_to.file.mime_type.startsWith("video/")) {

            preview = "🎥 Видео";

        }

        else if (msg.reply_to.voice_duration != null) {
            preview = "🎤 Голосовое сообщение";
        }
        else {

            preview = `📎 ${msg.reply_to.file.original_name}`;

        }

        if (msg.reply_to.content?.trim()) {

            preview += `<br>${msg.reply_to.content}`;

        }
    }

    else {

        preview = msg.reply_to.content;

    }

    return `
        <div
            class="reply-bubble"
            data-reply-id="${msg.reply_to.id}"
        >

            <div class="reply-author">
                ${author}
            </div>

            <div class="reply-text">
                ${preview}
            </div>

        </div>
    `;
}

function attachReplyClick(div) {

    const bubble =
        div.querySelector(".reply-bubble");

    if (!bubble) return;

    bubble.addEventListener("click", () => {
        logger.debug("Reply bubble clicked", {
            replyId: bubble.dataset.replyId
        });
        jumpToMessage(bubble.dataset.replyId);

    });
}

function startReply() {
    cancelEdit()
    if (!selectedMessage) {
        return;
    }

    replyToMessage =
        selectedMessage;
    logger.info("Reply started", {
        messageId: selectedMessage?.id,
        content: selectedMessage?.content,
        hasFile: !!selectedMessage?.file,
        voiceDuration: selectedMessage?.voice_duration
    });
    document.getElementById(
        "replyPreview"
    ).style.display = "flex";

    let preview = "";

    if (replyToMessage.voice_duration != null) {

        preview = "🎤 Голосовое сообщение";

    }
    else if (replyToMessage.file) {

        if (replyToMessage.file.mime_type.startsWith("image/")) {

            preview = "📷 Фото";

        }
        else if (replyToMessage.file.mime_type.startsWith("video/")) {

            preview = "🎥 Видео";

        }
        else {

            preview = `📎 ${replyToMessage.file.original_name}`;

        }

        if (replyToMessage.content?.trim()) {

            preview += `\n${replyToMessage.content}`;

        }

    }
    else {

        preview = replyToMessage.content;

    }

    document.getElementById("replyPreviewText").innerHTML = preview;

    document.getElementById(
        "messageContextMenu"
    ).style.display = "none";

    document.getElementById(
        "messageInput"
    ).focus();
}

function cancelReply() {
    logger.info("Reply cancelled", {
        messageId: replyToMessage?.id
    });
    replyToMessage = null;

    document.getElementById(
        "replyPreview"
    ).style.display = "none";
}