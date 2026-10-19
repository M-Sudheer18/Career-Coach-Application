document.addEventListener("DOMContentLoaded", () => {

    const messagesContainer =
        document.getElementById("interview-messages");

    const answerInput =
        document.getElementById("candidate-answer");

    const sendButton =
        document.getElementById("interview-send-btn");


    if (!messagesContainer || !answerInput || !sendButton) {
        return;
    }


    // INTERVIEW STATE

    let conversationHistory = [];
    let pollingTimer = null;
    let isGenerating = false;


    // LOAD SAVED INTERVIEW STATE

    async function loadInterviewState() {
        try {
            const response = await fetch(
                "/interview/api/state",
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    },
                    cache: "no-store"
                }
            );

            const state = await response.json();

            if (!response.ok) {
                console.error(
                    "Failed to load Interview state:",
                    state.error
                );
                return;
            }

            conversationHistory =
                state.conversation || [];

            renderConversation(
                conversationHistory
            );

            if (state.status === "generating") {

                isGenerating = true;
                sendButton.disabled = true;

                showGeneratingIndicator();

                startPolling();

            } else {

                isGenerating = false;
                sendButton.disabled = false;
            }

        } catch (error) {
            console.error(
                "Interview state loading error:",
                error
            );
        }
    }


    // SEND ANSWER

    async function sendAnswer() {

        if (isGenerating) {
            return;
        }

        const answer =
            answerInput.value.trim();

        if (!answer) {
            return;
        }


        // Disable immediately

        isGenerating = true;
        sendButton.disabled = true;


        // Show candidate answer immediately

        addMessage(
            answer,
            "user"
        );


        // Clear input

        answerInput.value = "";


        // Show typing indicator

        showGeneratingIndicator();

        try {

            const response = await fetch(
                "/interview/api/chat",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        candidate_answer: answer
                    })
                }
            );


            const data =
                await response.json();


            if (!response.ok) {

                removeGeneratingIndicator();

                addMessage(
                    data.error ||
                    "Unable to start interview generation.",
                    "ai"
                );

                isGenerating = false;
                sendButton.disabled = false;

                return;
            }


            // Generation is now running on the server

            startPolling();


        } catch (error) {

            removeGeneratingIndicator();

            addMessage(
                "Something went wrong while starting the interview generation. Please try again.",
                "ai"
            );

            console.error(
                "Interview API Error:",
                error
            );

            isGenerating = false;
            sendButton.disabled = false;
        }
    }

    // SHOW AI RESPONDING INDICATOR

    function showGeneratingIndicator() {

        // Prevent duplicate indicators
        if (
            document.getElementById(
                "interview-generating-indicator"
            )
        ) {
            return;
        }

        const messageWrapper =
            document.createElement("div");

        messageWrapper.id =
            "interview-generating-indicator";

        messageWrapper.className =
            "interview-message ai-message";

        messageWrapper.innerHTML = `
            <div class="message-avatar">
                AI
            </div>

            <div class="message-content">
                <div class="ai-responding">
                    <span>AI is responding</span>
                    <span class="responding-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </span>
                </div>
            </div>
        `;

        messagesContainer.appendChild(
            messageWrapper
        );

        scrollToBottom();
    }

    // REMOVE AI RESPONDING INDICATOR

    function removeGeneratingIndicator() {

        const indicator =
            document.getElementById(
                "interview-generating-indicator"
            );

        if (indicator) {
            indicator.remove();
        }
    }


    // START POLLING

    function startPolling() {

        if (pollingTimer) {
            clearInterval(pollingTimer);
        }

        pollingTimer =
            setInterval(
                checkInterviewState,
                1000
            );

        checkInterviewState();
    }


    // CHECK SERVER STATE

    async function checkInterviewState() {

        try {

            const response = await fetch(
                "/interview/api/state",
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    },
                    cache: "no-store"
                }
            );


            const state =
                await response.json();


            if (!response.ok) {
                return;
            }


            conversationHistory =
                state.conversation || [];


            // AI is still generating

            if (state.status === "generating") {

                isGenerating = true;
                sendButton.disabled = true;

                return;
            }


            // Generation finished

            if (
                state.status === "completed" ||
                state.status === "error"
            ) {
                removeGeneratingIndicator();
                if (pollingTimer) {

                    clearInterval(
                        pollingTimer
                    );

                    pollingTimer = null;
                }


                renderConversation(
                    state.conversation || []
                );


                isGenerating = false;
                sendButton.disabled = false;

                answerInput.focus();
            }

        } catch (error) {

            console.error(
                "Interview polling error:",
                error
            );
        }
    }


    // RENDER SAVED CONVERSATION

    function renderConversation(
        conversation
    ) {

        messagesContainer.innerHTML = "";


        conversation.forEach(
            (turn) => {

                const type =
                    turn.role === "candidate"
                        ? "user"
                        : "ai";

                addMessage(
                    turn.content,
                    type,
                    false
                );
            }
        );


        scrollToBottom();
    }


    // ADD MESSAGE

    function addMessage(
        message,
        type,
        shouldScroll = true
    ) {

        const messageWrapper =
            document.createElement("div");


        messageWrapper.className =
            type === "user"
                ? "interview-message user-message"
                : "interview-message ai-message";


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


        content.appendChild(
            paragraph
        );


        messageWrapper.appendChild(
            avatar
        );


        messageWrapper.appendChild(
            content
        );


        messagesContainer.appendChild(
            messageWrapper
        );


        if (shouldScroll) {
            scrollToBottom();
        }
    }

    // SCROLL TO BOTTOM

    function scrollToBottom() {

        messagesContainer.scrollTop =
            messagesContainer.scrollHeight;
    }


    // SEND BUTTON

    sendButton.addEventListener(
        "click",
        sendAnswer
    );


    // KEYBOARD INPUT

    answerInput.addEventListener(
        "keydown",
        (event) => {

            /*
             * Enter = Send
             * Shift + Enter = New Line
             */

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendAnswer();
            }
        }
    );


    // AUTO RESIZE TEXTAREA

    answerInput.addEventListener(
        "input",
        () => {

            answerInput.style.height =
                "auto";

            answerInput.style.height =
                Math.min(
                    answerInput.scrollHeight,
                    150
                ) + "px";
        }
    );


    // LOAD STATE WHEN PAGE OPENS

    loadInterviewState();

});