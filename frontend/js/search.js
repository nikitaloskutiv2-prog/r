let searchResults = [];
let currentSearchIndex = 0;
let searchLoadingOlder = false;

function initSearch() {

    document
        .getElementById("chatSearchBtn")
        ?.addEventListener(
            "click",
            toggleChatSearch
        );

    document
        .getElementById("searchNextBtn")
        ?.addEventListener(
            "click",
            nextSearchResult
        );

    document
        .getElementById("searchPrevBtn")
        ?.addEventListener(
            "click",
            prevSearchResult
        );

    document
        .getElementById("chatSearchInput")
        ?.addEventListener(
            "input",
            searchMessages
        );

    document
        .getElementById("closeSearchBtn")
        ?.addEventListener(
            "click",
            closeSearch
        );

}

function toggleChatSearch() {

    const bar =
        document.getElementById(
            "chatSearchBar"
        );

    if (
        bar.style.display === "none"
    ) {

        bar.style.display = "flex";

        document
            .getElementById(
                "chatSearchInput"
            )
            .focus();

    } else {

        closeSearch();
    }
}

function closeSearch() {

    document.getElementById(
        "chatSearchBar"
    ).style.display = "none";

    document.getElementById(
        "chatSearchInput"
    ).value = "";

    searchResults = [];
    currentSearchIndex = 0;

    document.getElementById(
        "searchCounter"
    ).textContent = "0/0";

    document
        .querySelectorAll(".message-content")
        .forEach(content => {

            content.classList.remove(
                "search-current"
            );
        });
}




function getAllCachedMessages() {

    return Array.from(messageCache.values())
        .sort((a, b) =>
            new Date(a.created_at) -
            new Date(b.created_at)
        );

}


function getCurrentSearchQuery() {

    return document
        .getElementById("chatSearchInput")
        ?.value
        .toLowerCase()
        .trim() || "";

}


function rebuildSearchResults() {

    const query =
        getCurrentSearchQuery();

    searchResults = [];

    if (!query) {
        return;
    }

    const messages =
        getAllCachedMessages();

    messages.forEach(msg => {

        /*
         * Только сообщения текущего чата.
         */
        if (
            Number(msg.chat_id) !==
            Number(currentChatId)
        ) {
            return;
        }

        const text =
            String(msg.content || "")
                .toLowerCase();

        if (text.includes(query)) {

            searchResults.push(
                msg.id
            );
        }

    });

}


function getSearchMessageElement(messageId) {

    return document.querySelector(
        `[data-message-id="${messageId}"]`
    );

}


function searchMessages() {

    currentSearchIndex = 0;

    document
        .querySelectorAll(".message-content")
        .forEach(content => {

            content.classList.remove(
                "search-current"
            );

        });

    rebuildSearchResults();

    if (
        searchResults.length === 0
    ) {

        updateSearchCounter();

        /*
         * Если результатов пока нет,
         * попробуем догрузить старую историю.
         */
        loadMoreForSearch();

        return;
    }

    /*
     * Стараемся выбрать результат,
     * ближайший к текущей позиции.
     */
    let nearestIndex = 0;
    let nearestDistance = Infinity;

    const viewportCenter =
        window.innerHeight / 2;

    searchResults.forEach(
        (messageId, index) => {

            const element =
                getSearchMessageElement(
                    messageId
                );

            if (!element) {
                return;
            }

            const rect =
                element.getBoundingClientRect();

            const distance =
                Math.abs(
                    rect.top -
                    viewportCenter
                );

            if (
                distance <
                nearestDistance
            ) {

                nearestDistance =
                    distance;

                nearestIndex =
                    index;
            }

        }
    );

    currentSearchIndex =
        nearestIndex;

    updateSearchCounter();

    highlightCurrentResult();

    scrollToSearchResult(
        currentSearchIndex
    );

}


function highlightCurrentResult() {

    document
        .querySelectorAll(".message-content")
        .forEach(content => {

            content.classList.remove(
                "search-current"
            );

        });

    if (
        searchResults.length === 0
    ) {
        return;
    }

    const messageId =
        searchResults[
            currentSearchIndex
        ];

    const message =
        getSearchMessageElement(
            messageId
        );

    if (!message) {
        return;
    }

    const content =
        message.querySelector(
            ".message-content"
        );

    content?.classList.add(
        "search-current"
    );

}


async function nextSearchResult() {

    if (
        searchLoadingOlder
    ) {
        return;
    }

    /*
     * Если результатов вообще нет —
     * пытаемся догрузить историю.
     */
    if (
        searchResults.length === 0
    ) {

        await loadMoreForSearch();

        return;
    }

    currentSearchIndex++;

    /*
     * Есть следующий результат.
     */
    if (
        currentSearchIndex <
        searchResults.length
    ) {

        updateSearchCounter();
        highlightCurrentResult();

        scrollToSearchResult(
            currentSearchIndex
        );

        return;
    }

    /*
     * Дошли до конца уже загруженной
     * истории.
     */
    if (!allMessagesLoaded) {

        currentSearchIndex =
            searchResults.length - 1;

        await loadMoreForSearch();

        /*
         * После загрузки перестраиваем
         * результаты.
         */
        rebuildSearchResults();

        /*
         * Ищем следующий результат
         * после текущего сообщения.
         */
        const currentMessageId =
            searchResults[
                currentSearchIndex
            ];

        const currentMessage =
            messageCache.get(
                currentMessageId
            );

        let nextIndex =
            searchResults.findIndex(
                id => {

                    const msg =
                        messageCache.get(id);

                    return (
                        msg &&
                        currentMessage &&
                        new Date(
                            msg.created_at
                        ) >
                        new Date(
                            currentMessage.created_at
                        )
                    );

                }
            );

        /*
         * findIndex может вернуть сам
         * текущий/более ранний элемент,
         * поэтому ищем строго следующий.
         */
        nextIndex =
            searchResults.findIndex(
                id => {

                    const msg =
                        messageCache.get(id);

                    return (
                        msg &&
                        currentMessage &&
                        new Date(
                            msg.created_at
                        ) >
                        new Date(
                            currentMessage.created_at
                        )
                    );

                }
            );

        if (
            nextIndex !== -1
        ) {

            currentSearchIndex =
                nextIndex;

            updateSearchCounter();
            highlightCurrentResult();

            scrollToSearchResult(
                currentSearchIndex
            );

        } else {

            updateSearchCounter();

        }

        return;
    }

    /*
     * Вся история загружена —
     * переходим по кругу.
     */
    currentSearchIndex = 0;

    updateSearchCounter();
    highlightCurrentResult();

    scrollToSearchResult(
        currentSearchIndex
    );

}


async function prevSearchResult() {

    if (
        searchLoadingOlder
    ) {
        return;
    }

    if (
        searchResults.length === 0
    ) {

        await loadMoreForSearch();

        return;
    }

    currentSearchIndex--;

    if (
        currentSearchIndex >= 0
    ) {

        updateSearchCounter();
        highlightCurrentResult();

        scrollToSearchResult(
            currentSearchIndex
        );

        return;
    }

    /*
     * Назад упёрся в начало уже
     * загруженной истории.
     *
     * Если старые сообщения ещё
     * существуют — догружаем их.
     */
    if (!allMessagesLoaded) {

        currentSearchIndex = 0;

        await loadMoreForSearch();

        rebuildSearchResults();

        /*
         * После prepend старые сообщения
         * находятся раньше текущих.
         * Берём самый старый найденный
         * результат.
         */
        if (
            searchResults.length > 0
        ) {

            currentSearchIndex = 0;

            updateSearchCounter();
            highlightCurrentResult();

            scrollToSearchResult(
                currentSearchIndex
            );

        }

        return;
    }

    /*
     * Вся история уже загружена —
     * переходим на последний результат.
     */
    currentSearchIndex =
        searchResults.length - 1;

    updateSearchCounter();
    highlightCurrentResult();

    scrollToSearchResult(
        currentSearchIndex
    );

}


function scrollToSearchResult(index) {

    if (
        searchResults.length === 0
    ) {
        return;
    }

    const messageId =
        searchResults[index];

    const element =
        getSearchMessageElement(
            messageId
        );

    if (!element) {
        return;
    }

    element.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

}


function updateSearchCounter() {

    const counter =
        document.getElementById(
            "searchCounter"
        );

    if (!counter) {
        return;
    }

    if (
        searchResults.length === 0
    ) {

        counter.textContent =
            "0/0";

        return;
    }

    counter.textContent =
        `${currentSearchIndex + 1}/${searchResults.length}`;

}


async function loadMoreForSearch() {

    if (
        searchLoadingOlder ||
        allMessagesLoaded ||
        !oldestMessageId
    ) {
        return;
    }

    searchLoadingOlder = true;

    try {

        await loadOlderMessages();

        rebuildSearchResults();

        updateSearchCounter();

    } finally {

        searchLoadingOlder = false;

    }

}

let searchTimeout;
document.getElementById("searchInput").addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value.trim();
    
    if (query.length < 1) {
        document.getElementById("searchResults").classList.remove("show");
        return;
    }
    
    searchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`${API_URL}/users/?query=${encodeURIComponent(query)}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            
            if (!response.ok) return;
            
            const users = await response.json();
            
            const resultsDiv = document.getElementById("searchResults");
            resultsDiv.innerHTML = "";
            
            if (users.length === 0) {
                resultsDiv.classList.remove("show");
                return;
            }
            
            users.forEach(user => {

                const div = document.createElement("div");
                div.className = "search-result-item";

                if (Number(user.id) === Number(currentUserId)) {

                    div.classList.add("favorite-search-result");

                    div.innerHTML = `
                        <div class="search-result-avatar favorite-avatar">
                            <img
                                src="/storage/bookmark.png"
                                alt="Избранное"
                            >
                        </div>

                        <div class="search-result-name">
                            Избранное
                        </div>
                    `;

                    div.onclick = () => openFavoriteChat();

                } else {

                    const firstLetter =
                        user.username?.charAt(0).toUpperCase() || "?";

                    const avatarHtml =
                        user.avatar
                            ? `
                                <img
                                    src="${API_URL}${user.avatar}"
                                    alt="${user.username}"
                                    class="search-result-avatar-image"
                                >
                            `
                            : `
                                <div class="search-result-avatar-placeholder">
                                    ${firstLetter}
                                </div>
                            `;

                    div.innerHTML = `
                        <div class="search-result-avatar">
                            ${avatarHtml}
                        </div>

                        <div class="search-result-name">
                            ${user.username}
                        </div>
                    `;

                    div.onclick = () =>
                        createPrivateChat(
                            user.id,
                            user.username
                        );
                }

                resultsDiv.appendChild(div);
            });
            
            resultsDiv.classList.add("show");
        } catch (error) {
            logger.error("Error searching users", error);
        }
    }, 300);
});

document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-box")) {
        document.getElementById("searchResults").classList.remove("show");
    }
    if (!e.target.closest(".sidebar-header")) {
        document.getElementById("menuDropdown").classList.remove("show");
    }
});


async function openFavoriteChat() {

    try {

        const response = await fetch(
            `${API_URL}/chats/favorite`,
            {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            }
        );

        if (!response.ok) {

            logger.error(
                "Не удалось открыть Избранное",
                response.status
            );

            return;
        }

        // Новый чат, который создал сервер
        const chat = await response.json();
        chat.is_favorite = true;

        // Закрываем результаты поиска
        const searchResults =
            document.getElementById("searchResults");

        if (searchResults) {
            searchResults.classList.remove("show");
        }

        // Проверяем, есть ли этот чат уже в allChats
        const existingIndex =
            allChats.findIndex(
                c =>
                    Number(c.id) ===
                    Number(chat.id)
            );

        if (existingIndex === -1) {

            // Добавляем новый чат
            allChats.push(chat);

        } else {

            // Если уже есть — обновляем его
            allChats[existingIndex] = chat;
        }

        // Перерисовываем сайдбар
        await renderChats();

        // Открываем именно новый чат
        await selectChat(chat);

    } catch (error) {

        logger.error(
            "Ошибка открытия Избранного",
            error
        );
    }
}