function addMessageToUI(
    msg,
    prepend = false
) {
    logger.debug("addMessageToUI", {
        messageId: msg?.id,
        prepend,
        chatId: currentChatId
    });
    const container =
        document.getElementById(
            "messagesContainer"
        );

    removeEmptyState(container);

    const div =
        createMessageElement(msg);

    div.innerHTML =
        buildMessageContent(msg);

    if (prepend) {

        insertOldMessage(
            container,
            div,
            msg
        );

    } else {

        insertNewMessage(
            container,
            div,
            msg
        );
    }

    postRenderHooks(
        div,
        msg,
        container
    );
    logger.debug("Message rendered", {
        messageId: msg.id,
        prepend
    });
}



function buildMediaElement(msg) {

    const isImage =
        msg.file &&
        msg.file.mime_type.startsWith("image/");

    const isVideo =
        msg.file &&
        msg.file.mime_type.startsWith("video/");

    const isVoice =
        msg.voice_duration !== null &&
        msg.voice_duration !== undefined;

    const isFile =
        msg.file &&
        !isImage &&
        !isVideo &&
        !isVoice;

    const sec =
        msg.voice_duration ?? 0;

    const duration =
        formatVoiceDuration(sec);


    logger.debug("Building media element", {
        messageId: msg?.id,
        type: isImage
            ? "image"
            : isVideo
                ? "video"
                : isVoice
                    ? "voice"
                    : isFile
                        ? "file"
                        : "none"
    });
    if (isImage) {

        return `
            <img
                class="message-image"
                src="${API_URL}/${msg.file.path}"
                alt="${msg.file.original_name}"
            >
        `;

    }

    if (isVideo) {

        return `
            <div class="message-video-preview">

                <img
                    class="message-image"
                    src="${API_URL}/${msg.file.thumbnail_path}"
                >

                <div class="video-play-button">
                    ▶
                </div>

            </div>
        `;

    }
    if (isVoice) {

        return `
            <div class="voice-message">

                <button
                    class="voice-play"
                    data-path="${API_URL}/${msg.file.path}">
                    ▶
                </button>

                <div class="voice-content">

                    <canvas
                        class="voice-waveform"
                        data-waveform='${JSON.stringify(msg.waveform || [])}'
                        data-progress="0">
                    </canvas>

                    <div class="voice-bottom">

                        <span
                            class="voice-duration"
                            data-duration="${sec}">
                            ${duration}
                        </span>

                        <span
                            class="voice-unheard"
                            style="${
                                msg.voice_played
                                    ? "visibility:hidden"
                                    : ""
                            }">
                        </span>

                    </div>

                </div>

            </div>
        `;

    }

    if (isFile) {

        return `
            <div
                class="message-file"
                onclick="downloadFile(
                    ${msg.file.id},
                    '${msg.file.original_name}'
                )"
            >

                <div class="message-file-icon">
                    ${getFileIcon(msg.file.original_name)}
                </div>

                <div class="message-file-info">

                    <div class="message-file-name">
                        ${msg.file.original_name}
                    </div>

                    <div class="message-file-size">
                        ${formatFileSize(msg.file.size)}
                    </div>

                </div>

            </div>
        `;

    }

    return "";

}

function removeEmptyState(container) {

    const emptyState =
        container.querySelector(".empty-state");

    if (emptyState) {
        emptyState.remove();
    }
}



function getMessageDateKey(dateString) {

    const normalized =
        dateString.endsWith("Z")
            ? dateString
            : dateString + "Z";

    return new Date(normalized)
        .toISOString()
        .split("T")[0];
}

function createDateSeparator(dateString) {

    const separator =
        document.createElement("div");

    separator.className =
        "date-separator";

    separator.dataset.date =
        getMessageDateKey(dateString);

    const normalized =
        dateString.endsWith("Z")
            ? dateString
            : dateString + "Z";

    const date =
        new Date(normalized);

    separator.textContent =
        date.toLocaleDateString(
            "ru-RU",
            {
                day: "numeric",
                month: "long",
                year: "numeric"
            }
        );

    return separator;
}


function rebuildDateSeparators(container) {
    logger.debug("Rebuilding date separators", {
        chatId: currentChatId,
        messageCount:
            container.querySelectorAll(".message").length
    });

    container
        .querySelectorAll(".date-separator")
        .forEach(separator => {
            separator.remove();
        });

    /*
     * Теперь DOM содержит только messages.
     */
    const messages =
        Array.from(
            container.querySelectorAll(".message")
        );

    let previousDate = null;

    messages.forEach(message => {

        const createdAt =
            message.dataset.createdAt;

        if (!createdAt) {
            return;
        }

        const dateKey =
            getMessageDateKey(createdAt);

        /*
         * Новая дата —
         * вставляем separator ПЕРЕД message.
         */
        if (dateKey !== previousDate) {

            const separator =
                createDateSeparator(
                    createdAt
                );

            container.insertBefore(
                separator,
                message
            );

            previousDate = dateKey;
        }
    });
    logger.debug("Date separators rebuilt", {
        separatorCount:
            container.querySelectorAll(".date-separator").length
    });
}

function addDateSeparatorBefore(
    container,
    element,
    dateString
) {

    const date =
        new Date(
            dateString + "Z"
        );

    const separator =
        document.createElement(
            "div"
        );

    separator.className =
        "date-separator";

    separator.dataset.date =
        date.toISOString()
            .split("T")[0];

    separator.textContent =
        date.toLocaleDateString(
            "ru-RU",
            {
                day: "numeric",
                month: "long",
                year: "numeric"
            }
        );

    container.insertBefore(
        separator,
        element
    );
}


function insertNewMessage(
    container,
    messageElement,
    msg
) {
    logger.debug("Inserting new message", {
        messageId: msg?.id,
        createdAt: msg?.created_at
    });
    const dateKey =
        getMessageDateKey(
            msg.created_at
        );

    const lastMessage =
        container.querySelector(
            ".message:last-of-type"
        );

    if (!lastMessage) {

        container.appendChild(
            createDateSeparator(
                msg.created_at
            )
        );

    } else {

        const lastDate =
            getMessageDateKey(
                lastMessage.dataset.createdAt
            );

        if (lastDate !== dateKey) {

            container.appendChild(
                createDateSeparator(
                    msg.created_at
                )
            );
        }
    }

    container.appendChild(
        messageElement
    );

    messageElement.dataset.createdAt =
        msg.created_at;
}

function insertOldMessage(
    container,
    messageElement,
    msg
) {
    logger.debug("Inserting old message", {
        messageId: msg?.id,
        createdAt: msg?.created_at
    });
    const firstMessage =
        container.querySelector(".message");

    if (!firstMessage) {

        container.appendChild(
            messageElement
        );

    } else {

        container.insertBefore(
            messageElement,
            firstMessage
        );
    }

    messageElement.dataset.createdAt =
        msg.created_at;
}


function createMessageElement(msg) {
    logger.debug("Creating message element", {
        messageId: msg?.id,
        senderId: msg?.sender_id,
        isOwn: msg?.sender_id === currentUserId
    });
    const div =
        document.createElement("div");

    div.className = "message";

    div.setAttribute(
        "data-message-id",
        msg.id
    );

    div.setAttribute(
        "data-created-at",
        msg.created_at
    );

    div.dataset.createdAt =
        msg.created_at;

    div.classList.add(
        msg.sender_id === currentUserId
            ? "sent"
            : "received"
    );

    return div;
}

function buildMessageContent(msg) {

    return `
        <div class="message-content ${hasMedia(msg) ? "has-media" : ""} ${hasFile(msg) ? "has-file" : ""}">

            ${buildReplyHtml(msg)}

            <div class="message-text-wrapper">

                ${buildBodyHtml(msg)}

            </div>

        </div>
    `;

}

function buildBodyHtml(msg) {

    const time =
        formatTime(msg.created_at);

    const statusBadges =
        buildStatusBadges(msg);

    const media =
        buildFileBlock(
            msg,
            time,
            statusBadges
        );

    const text =
        buildTextBlock(msg);

    const bottom =
        buildBottomBlock(
            msg,
            time,
            statusBadges
        );

    return `
        ${media}

        ${text}

        ${bottom}
    `;

}

function hasMedia(msg) {

    return !!(
        msg.file &&
        (
            msg.file.mime_type.startsWith("image/") ||
            msg.file.mime_type.startsWith("video/")
        )
    );

}

function hasFile(msg) {

    return !!(
        msg.file &&
        !msg.file.mime_type.startsWith("image/") &&
        !msg.file.mime_type.startsWith("video/")
    );

}

function formatTime(dateStr) {

    const normalized =
        dateStr.endsWith("Z")
            ? dateStr
            : dateStr + "Z";

    return new Date(normalized)
        .toLocaleTimeString("ru-RU", {
            hour: "2-digit",
            minute: "2-digit"
        });
}

function buildTextBlock(msg) {

    if (!msg.content)
        return "";

    const media =
        hasMedia(msg);

    const file =
        hasFile(msg);

    if (
        (media || file) &&
        msg.content
    ) {

        return "";

    }

    return `
        <div class="message-text">

            ${msg.content}

        </div>
    `;

}

function buildBottomBlock(
    msg,
    time,
    statusBadges
) {

    const media =
        hasMedia(msg);

    const file =
        hasFile(msg);

    const mediaCaption =
        media &&
        msg.content;

    const mediaOnly =
        media &&
        !msg.content;

    const fileCaption =
        file &&
        msg.content;

    const fileOnly =
        file &&
        !msg.content;

    if (
        mediaOnly ||
        mediaCaption ||
        fileOnly ||
        fileCaption
    ) {

        return "";

    }

    return `
        <div class="message-bottom">

            <div class="message-reactions"></div>

           ${buildMessageMeta(
                msg,
                time,
                statusBadges
            )}

        </div>
    `;

}



function buildStatusBadges(msg) {

    if (msg.sender_id !== currentUserId) {
        return "";
    }

    return `
        <div class="message-status-badges ${!msg.is_read ? "unread" : ""}">
            ${msg.is_read ? "✓✓" : "✓"}
        </div>
    `;

}

function buildFileBlock(
    msg,
    time,
    statusBadges
) {
    logger.debug("Building message file block", {
        messageId: msg?.id,
        hasFile: !!msg?.file,
        isImage: isImageMessage(msg),
        isVideo: isVideoMessage(msg),
        isVoice: isVoiceMessage(msg)
    });
    if (
        isImageMessage(msg)
    ) {

        return buildImageMessage(
            msg,
            time,
            statusBadges
        );

    }

    if (
        isVideoMessage(msg)
    ) {

        return buildVideoMessage(
            msg,
            time,
            statusBadges
        );

    }

    if (
        isVoiceMessage(msg)
    ) {

        return buildVoiceMessage(
            msg,
            time,
            statusBadges
        );

    }

    if (
        isFileMessage(msg)
    ) {

        return buildFileMessage(
            msg,
            time,
            statusBadges
        );

    }

    return "";

}

function isImageMessage(msg) {

    return !!(
        msg.file &&
        msg.file.mime_type.startsWith(
            "image/"
        )
    );

}

function isVideoMessage(msg) {

    return !!(
        msg.file &&
        msg.file.mime_type.startsWith(
            "video/"
        )
    );

}

function isVoiceMessage(msg) {
    return msg.voice_duration != null;
}

function isFileMessage(msg) {

    return !!(
        msg.file &&
        !isImageMessage(msg) &&
        !isVideoMessage(msg)
    );

}

function buildImageMessage(
    msg,
    time,
    statusBadges
) {

    const media =
        buildMediaElement(msg);

    if (!msg.content) {

        return `
            <div class="image-media image-only">

                ${media}

                <div class="image-meta">

                    <span class="message-time">
                        ${time}
                    </span>

                    ${statusBadges}

                </div>

                <div class="message-reactions"></div>

            </div>
        `;

    }

    return `
        <div class="image-media">

            ${media}

            <div class="image-caption-row">

                <div class="image-caption">
                    ${msg.content}
                </div>

                ${buildMessageMeta(
                    msg,
                    time,
                    statusBadges
                )}

            </div>

            <div class="message-reactions"></div>

        </div>
    `;

}

function buildVideoMessage(
    msg,
    time,
    statusBadges
) {

    const media =
        buildMediaElement(msg);

    if (!msg.content) {

        return `
            <div class="image-media image-only">

                ${media}

                <div class="image-meta">

                    <span class="message-time">
                        ${time}
                    </span>

                    ${statusBadges}

                </div>

                <div class="message-reactions"></div>

            </div>
        `;

    }

    return `
        <div class="image-media">

            ${media}

            <div class="image-caption-row">

                <div class="image-caption">
                    ${msg.content}
                </div>

                ${buildMessageMeta(
                    msg,
                    time,
                    statusBadges
                )}

            </div>

            <div class="message-reactions"></div>

        </div>
    `;

}

function buildVoiceMessage(
    msg,
    time,
    statusBadges
) {

    return `
        <div class="voice-wrapper">

            <div class="voice-player">

                ${buildMediaElement(msg)}

            </div>

            <div class="voice-footer">

                <div class="voice-footer-left">

                    <div class="message-reactions"></div>

                </div>

                <div class="voice-footer-right">

                    ${buildMessageMeta(
                        msg,
                        time,
                        statusBadges
                    )}

                </div>

            </div>

        </div>
    `;

}

function buildFileMessage(msg, time, statusBadges) {
  const media = buildMediaElement(msg);
  const hasCaption = !!msg.content;
  const metaHtml = buildMessageMeta(msg, time, statusBadges);

  if (hasCaption) {
    // Есть подпись: подпись+мета в одной строке, реакции — отдельной строкой ниже
    return `
      <div class="file-message" data-message-id="${msg.id}">
        ${media}
        <div class="file-footer file-footer--with-caption">
          <div class="file-caption-meta-row">
            <div class="file-caption">${msg.content}</div>
            <div class="file-meta">${metaHtml}</div>
          </div>
          <div class="message-reactions"></div>
        </div>
      </div>
    `;
  } else {
    // Нет подписи: реакция слева, мета справа — в одной строке
    return `
      <div class="file-message" data-message-id="${msg.id}">
        ${media}
        <div class="file-footer">
          <div class="file-no-caption-row">
            <div class="file-meta">${metaHtml}</div>
            <div class="message-reactions"></div>
          </div>
        </div>
      </div>
    `;
  }
}



function buildMessageMeta(
    msg,
    time,
    statusBadges
) {

    return `
        <div class="message-meta">

            ${
                msg.edited
                    ? `
                        <span class="message-edited">
                            изменено
                        </span>
                    `
                    : ""
            }

            <span class="message-time">

                ${time}

            </span>

            ${statusBadges}

        </div>
    `;

}