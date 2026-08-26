function initReactions() {

    document
        .querySelectorAll(
            ".reaction-bar button"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                async () => {
                    logger.debug(
                        "Добавление реакции",
                        {
                            messageId: selectedMessageId,
                            emoji: button.dataset.emoji
                        }
                    );
                    await addReaction(
                        selectedMessageId,
                        button.dataset.emoji
                    );

                    closeContextMenu();

                }
            );

        });

}

function attachReactions(div, msg) {

    const container =
        div.querySelector(".message-reactions");

    if (!container)
        return;

    renderReactions(
        msg.reactions || {},
        container,
        msg.id
    );

}


function renderReactions(
    reactions,
    reactionsContainer,
    messageId
) {

    reactionsContainer.innerHTML = "";

    Object.entries(reactions).forEach(
        ([emoji, data]) => {

            const chip =
                document.createElement("div");

            chip.className =
                "reaction-chip";

            chip.textContent =
                `${emoji} ${data.count}`;

            if (
                data.users?.includes(currentUserId)
            ) {
                chip.classList.add("active");
            }

            chip.onclick = async () => {

                await addReaction(
                    messageId,
                    emoji
                );

            };

            reactionsContainer.appendChild(
                chip
            );

        }
    );

    const wrapper =
        reactionsContainer.closest(
            ".message-text-wrapper"
        );

    const bottom =
        reactionsContainer.closest(
            ".message-bottom"
        );

    if (
        Object.keys(reactions).length === 0
    ) {

        reactionsContainer.style.display =
            "none";

        wrapper?.classList.add(
            "no-reactions"
        );

        bottom?.classList.remove(
            "has-reactions"
        );

    } else {

        reactionsContainer.style.display =
            "flex";

        wrapper?.classList.remove(
            "no-reactions"
        );

        bottom?.classList.add(
            "has-reactions"
        );

    }

}

function handleReactionUpdated(msg) {
    logger.debug(
        "Обновление реакций сообщения",
        {
            messageId: msg.message_id
        }
    );
    const messageElement =
        document.querySelector(
            `[data-message-id="${msg.message_id}"]`
        );

    if (!messageElement)
        return;

    const reactionsContainer =
        messageElement.querySelector(
            ".message-reactions"
        );

    if (!reactionsContainer)
        return;

    renderReactions(
        msg.reactions || {},
        reactionsContainer,
        msg.message_id
    );

    // обновляем кэш сообщения
    const cached =
        findMessageInMemory(msg.message_id);

    if (cached) {

        cached.reactions =
            msg.reactions || {};

    }

}

async function addReaction(
    messageId,
    emoji
) {
    logger.debug(
        "Отправка реакции",
        {
            messageId,
            emoji
        }
    );
    await fetch(
        `${API_URL}/messages/${messageId}/reaction`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },

            body: JSON.stringify({
                emoji
            })
        }
    );
    
    if (!response.ok) {

        logger.warn(
            "Не удалось добавить реакцию",
            {
                messageId,
                emoji,
                status: response.status
            }
        );

        return;
    }

    logger.info(
        "Реакция добавлена",
        {
            messageId,
            emoji
        }
    );
}