document.addEventListener("DOMContentLoaded", () => {
    const messagesContainer =
        document.getElementById("chat-messages");

    const questionInput =
        document.getElementById("career-question");

    const sendButton =
        document.getElementById("career-send-btn");
    
    const newChatButton =
        document.getElementById("new-career-chat-btn");

    if (
        !messagesContainer ||
        !questionInput ||
        !sendButton ||
        !newChatButton
    ) {
        return;
    }

    const resumeUploaded =
        localStorage.getItem("resumeUploaded") === "true";

    if (!resumeUploaded) {
        questionInput.disabled = true;
        questionInput.placeholder =
            "Please upload and analyze your resume first.";
        sendButton.disabled = true;
        sendButton.title =
            "Please upload and analyze your resume first.";
    }

    let conversationHistory = [];
    let pollingTimer = null;
    let currentJobId = null;
    let loadingMessage = null;

    async function sendQuestion() {
        const question =
            questionInput.value.trim();

        if (!question || pollingTimer) {
            return;
        }

        addMessage(question, "user");

        conversationHistory.push({
            role: "user",
            content: question
        });

        questionInput.value = "";
        questionInput.style.height = "auto";
        sendButton.disabled = true;

        loadingMessage = addLoadingMessage();

        try {
            const response = await fetch(
                "/career/api/chat",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        question: question
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                removeLoadingMessage();

                addMessage(
                    data.error ||
                    "Unable to process your question.",
                    "ai"
                );

                enableInput();
                return;
            }

            currentJobId =
                data.job_id || null;

            startPolling();

        } catch (error) {
            console.error(
                "Career Coach API Error:",
                error
            );

            removeLoadingMessage();

            addMessage(
                "Something went wrong while processing your question. Please try again.",
                "ai"
            );

            enableInput();
        }
    }

    async function startNewConversation() {
        if (pollingTimer) {
            return;
        }

        try {
            const response = await fetch(
                "/career/api/chat/new",
                {
                    method: "POST"
                }
            );

            const data = await response.json();

            if (!response.ok) {
                console.error(
                    "Failed to start new conversation:",
                    data.error
                );

                return;
            }

            conversationHistory = [];
            currentJobId = null;

            removeLoadingMessage();
            stopPolling();

            messagesContainer.innerHTML = `
                <div class="chat-message ai-message">
                    <div class="message-avatar">
                        AI
                    </div>

                    <div class="message-content">
                        <p>
                            Hello! I'm your AI Career Coach.
                            Ask me anything about your career, skills,
                            resume, job search, or professional growth.
                        </p>
                    </div>
                </div>
            `;

            questionInput.value = "";
            questionInput.style.height = "auto";

            enableInput();

        } catch (error) {
            console.error(
                "New Career Coach Conversation Error:",
                error
            );
        }
    }

    function startPolling() {
        if (pollingTimer) {
            return;
        }

        checkCareerCoachState();

        pollingTimer = setInterval(
            checkCareerCoachState,
            2000
        );
    }

    async function checkCareerCoachState() {
        try {
            const response = await fetch(
                "/career/api/chat/state",
                {
                    method: "GET"
                }
            );

            const data = await response.json();

            if (!response.ok) {
                console.error(
                    "Failed to load Career Coach state:",
                    data.error
                );
                return;
            }

            if (data.status === "generating") {
                currentJobId =
                    data.job_id || currentJobId;

                sendButton.disabled = true;

                if (!loadingMessage) {
                    loadingMessage =
                        addLoadingMessage();
                }

                return;
            }

            if (data.status === "completed") {
                stopPolling();
                removeLoadingMessage();

                const aiResponse =
                    data.result ||
                    "No response received from the AI Career Coach.";

                const lastMessage =
                    conversationHistory[
                        conversationHistory.length - 1
                    ];

                if (
                    !lastMessage ||
                    lastMessage.role !== "assistant" ||
                    lastMessage.content !== aiResponse
                ) {
                    addMessage(
                        aiResponse,
                        "ai"
                    );

                    conversationHistory.push({
                        role: "assistant",
                        content: aiResponse
                    });
                }

                currentJobId =
                    data.job_id || null;

                enableInput();
                return;
            }

            if (data.status === "error") {
                stopPolling();
                removeLoadingMessage();

                addMessage(
                    data.error ||
                    "Career Coach generation failed.",
                    "ai"
                );

                enableInput();
                return;
            }

            if (data.status === "idle") {
                stopPolling();
                removeLoadingMessage();
                enableInput();
            }

        } catch (error) {
            console.error(
                "Career Coach State Error:",
                error
            );
        }
    }

    async function restoreCareerCoachState() {
        try {
            const response = await fetch(
                "/career/api/chat/state",
                {
                    method: "GET"
                }
            );

            const data = await response.json();

            if (!response.ok) {
                console.error(
                    "Unable to restore Career Coach state:",
                    data.error
                );
                return;
            }

            if (
                Array.isArray(data.messages) &&
                data.messages.length > 0
            ) {
                conversationHistory =
                    data.messages;

                renderConversation(
                    data.messages
                );
            }

            currentJobId =
                data.job_id || null;

            if (data.status === "generating") {
                sendButton.disabled = true;

                loadingMessage =
                    addLoadingMessage();

                startPolling();
                return;
            }

            if (data.status === "completed") {
                enableInput();
                return;
            }

            if (data.status === "error") {
                if (data.error) {
                    addMessage(
                        data.error,
                        "ai"
                    );
                }

                enableInput();
            }

        } catch (error) {
            console.error(
                "Career Coach Restore Error:",
                error
            );
        }
    }

    function renderConversation(messages) {
        messagesContainer.innerHTML = `
            <div class="chat-message ai-message">
                <div class="message-avatar">
                    AI
                </div>

                <div class="message-content">
                    <p>
                        Hello! I'm your AI Career Coach.
                        Ask me anything about your career, skills,
                        resume, job search, or professional growth.
                    </p>
                </div>
            </div>
        `;

        messages.forEach(message => {
            if (
                !message ||
                !message.role ||
                !message.content
            ) {
                return;
            }

            if (message.role === "user") {
                addMessage(
                    message.content,
                    "user"
                );
                return;
            }

            if (message.role === "assistant") {
                addMessage(
                    message.content,
                    "ai"
                );
            }
        });

        scrollToBottom();
    }

    function addMessage(message, type) {
        const messageWrapper =
            document.createElement("div");

        messageWrapper.className =
            type === "user"
                ? "chat-message user-message"
                : "chat-message ai-message";

        const avatar =
            document.createElement("div");

        avatar.className =
            "message-avatar";

        avatar.textContent =
            type === "user"
                ? "You"
                : "AI";

        const content =
            document.createElement("div");

        content.className =
            "message-content";

        const paragraph =
            document.createElement("p");

        paragraph.textContent =
            message;

        content.appendChild(paragraph);

        messageWrapper.appendChild(avatar);
        messageWrapper.appendChild(content);
        messagesContainer.appendChild(messageWrapper);

        scrollToBottom();
    }

    function addLoadingMessage() {
        const messageWrapper =
            document.createElement("div");

        messageWrapper.className =
            "chat-message ai-message";

        messageWrapper.innerHTML = `
            <div class="message-avatar">
                AI
            </div>

            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        messagesContainer.appendChild(
            messageWrapper
        );

        scrollToBottom();

        return messageWrapper;
    }

    function removeLoadingMessage() {
        if (loadingMessage) {
            loadingMessage.remove();
            loadingMessage = null;
        }
    }

    function stopPolling() {
        if (pollingTimer) {
            clearInterval(pollingTimer);
            pollingTimer = null;
        }
    }

    function enableInput() {
        const resumeUpload =
            localStorage.getItem("resumeUploaded") === "true";

        if (!resumeUpload) {
            return;
        }

        sendButton.disabled = false;
        questionInput.disabled = false;
        questionInput.focus();
    }

    function scrollToBottom() {
        messagesContainer.scrollTop =
            messagesContainer.scrollHeight;
    }

    sendButton.addEventListener(
        "click",
        sendQuestion
    );

    newChatButton.addEventListener(
        "click",
        startNewConversation
    );

    questionInput.addEventListener(
        "keydown",
        event => {
            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {
                event.preventDefault();
                sendQuestion();
            }
        }
    );

    questionInput.addEventListener(
        "input",
        () => {
            questionInput.style.height = "auto";

            questionInput.style.height =
                Math.min(
                    questionInput.scrollHeight,
                    150
                ) + "px";
        }
    );

    restoreCareerCoachState();
});