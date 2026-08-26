
logger.info("INDEX.HTML LOADED");

let currentChatId = null;
let currentUserId = null;
let messageIds = new Set();
let currentUser = null;
let isMobile = window.innerWidth <= 768;
let isPageVisible = true;
let lastTypingSent = 0;
let lastRenderedDate = null;




    
// 👁️ Отслеживание видимости вкладки
document.addEventListener("visibilitychange", async () => {

    isPageVisible = !document.hidden;

    if (document.hidden) {

        await updateUserStatus("away");
        sendNotificationVisibilityStatus("away");

    } else {

        await updateUserStatus("online");
        sendNotificationVisibilityStatus("online");


        // Полностью синхронизируем открытый чат
        if (currentChatId) {

            await refreshChatOnVisible();

        }
    }
});

// 📱 Проверка мобильного экрана
window.addEventListener("resize", () => {
    isMobile = window.innerWidth <= 768;
});




// 💬 Создать приватный чат
async function createPrivateChat(userId, username) {

    try {
        const response = await fetch(
            `${API_URL}/chats/private`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    user_id: userId
                })
            }
        );

        if (!response.ok) {

            logger.error(
                "Error creating chat",
                response.status
            );

            const errorData =
                await response.json();

            logger.error(
                "Error details",
                errorData
            );

            return;
        }

        const chat =
            await response.json();

        // Закрываем поиск
        const searchInput =
            document.getElementById(
                "searchInput"
            );

        const searchResults =
            document.getElementById(
                "searchResults"
            );

        if (searchInput) {
            searchInput.value = "";
        }

        if (searchResults) {
            searchResults.classList.remove(
                "show"
            );
        }

        // Обновляем список чатов
        await loadChats();

        // Находим именно этот чат
        const existingChat =
            allChats.find(
                c =>
                    Number(c.id) ===
                    Number(chat.id)
            );

        if (existingChat) {

            // Сразу открываем его
            await selectChat(
                existingChat
            );

        } else {

            // На случай, если loadChats()
            // ещё не добавил его в список
            allChats.push(chat);

            sortChats();
            await renderChats();

            await selectChat(chat);
        }

    } catch (error) {

        logger.error(
            "Error creating private chat",
            error
        );
    }
}

// 🚀 Запуск
async function init() {
    logger.info("APP INIT");

    // Инициализируем тему
    initTheme();

    const user = await initAuth();
    if (!user) {
        return;
    }

    currentUserId = user.id;
    currentUser = user;

    localStorage.setItem("user", JSON.stringify(user));

    await loadChats();
    await loadUnreadCounts();

    initNotifications()

    document.getElementById(
        "messagesContainer"
    ).style.overflow = "hidden";    
   
    initUI();
    initStatus();
    initPin();
    initSearch();
    initChat();
    initReactions();
    initEdit();
    initReply();
    initAttachmentModule();
    initContextMenu();

}

init();