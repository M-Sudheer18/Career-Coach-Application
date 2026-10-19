document.addEventListener("DOMContentLoaded", () => {
// CAREER COACH
const careerQuestion = document.getElementById("career-question");
    const careerSendBtn = document.getElementById("career-send-btn");
    const chatMessages = document.getElementById("chat-messages");

    if (careerQuestion && careerSendBtn && chatMessages) {

        careerSendBtn.addEventListener("click", sendCareerMessage);

        careerQuestion.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendCareerMessage();
            }
        });

        async function sendCareerMessage() {

            const question = careerQuestion.value.trim();

            if (!question) {
                return;
            }

            addChatMessage(question, "user");

            careerQuestion.value = "";
            careerSendBtn.disabled = true;

            const loadingMessage = addLoadingMessage();

            try {

                const response = await fetch("/career/api/chat", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        question: question
                    })
                });

                const data = await response.json();

                loadingMessage.remove();

                if (!response.ok) {
                    addChatMessage(
                        data.error || "Unable to process your request.",
                        "ai"
                    );
                    return;
                }

                addChatMessage(
                    data.response || "No response received.",
                    "ai"
                );

            } catch (error) {

                loadingMessage.remove();

                addChatMessage(
                    "Something went wrong. Please try again.",
                    "ai"
                );

                console.error("Career Coach Error:", error);

            } finally {

                careerSendBtn.disabled = false;
                careerQuestion.focus();
            }
        }

        function addChatMessage(message, type) {

            const messageWrapper = document.createElement("div");

            messageWrapper.className =
                type === "user"
                    ? "chat-message user-message"
                    : "chat-message ai-message";

            const avatar = document.createElement("div");
            avatar.className = "message-avatar";
            avatar.textContent = type === "user" ? "You" : "AI";

            const content = document.createElement("div");
            content.className = "message-content";

            const paragraph = document.createElement("p");
            paragraph.textContent = message;

            content.appendChild(paragraph);

            messageWrapper.appendChild(avatar);
            messageWrapper.appendChild(content);

            chatMessages.appendChild(messageWrapper);

            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function addLoadingMessage() {

            const messageWrapper = document.createElement("div");

            messageWrapper.className =
                "chat-message ai-message";

            messageWrapper.innerHTML = `
                <div class="message-avatar">AI</div>

                <div class="message-content">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;

            chatMessages.appendChild(messageWrapper);

            chatMessages.scrollTop = chatMessages.scrollHeight;

            return messageWrapper;
        }
    }


    /* COVER LETTER GENERATOR */

    const jobDescription =
        document.getElementById("jobDescription");

    const generateCoverLetterBtn =
        document.getElementById("generateCoverLetterBtn");

    const coverLetterOutput =
        document.getElementById("coverLetterOutput");

    const coverLetterLoading =
        document.getElementById("coverLetterLoading");

    const coverLetterError =
        document.getElementById("coverLetterError");

    const copyCoverLetterBtn =
        document.getElementById("copyCoverLetterBtn");


    if (
        jobDescription &&
        generateCoverLetterBtn &&
        coverLetterOutput
    ) {

        generateCoverLetterBtn.addEventListener(
            "click",
            generateCoverLetter
        );

        async function generateCoverLetter() {

            const description =
                jobDescription.value.trim();

            if (!description) {

                if (coverLetterError) {
                    coverLetterError.textContent =
                        "Please enter a job description.";
                }

                return;
            }

            if (coverLetterError) {
                coverLetterError.textContent = "";
            }

            generateCoverLetterBtn.disabled = true;

            if (coverLetterLoading) {
                coverLetterLoading.style.display = "block";
            }

            coverLetterOutput.innerHTML = "";

            try {

                const response = await fetch(
                    "/career/api/cover_letter",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            job_description: description
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        "Unable to generate cover letter."
                    );
                }

                const result =
                    data.response || "No cover letter generated.";

                coverLetterOutput.textContent = result;

            } catch (error) {

                coverLetterOutput.innerHTML = `
                    <p class="placeholder-text">
                        Unable to generate the cover letter.
                    </p>
                `;

                if (coverLetterError) {
                    coverLetterError.textContent =
                        error.message;
                }

                console.error(
                    "Cover Letter Error:",
                    error
                );

            } finally {

                generateCoverLetterBtn.disabled = false;

                if (coverLetterLoading) {
                    coverLetterLoading.style.display = "none";
                }
            }
        }
    }


    /* COPY COVER LETTER */

    if (copyCoverLetterBtn && coverLetterOutput) {

        copyCoverLetterBtn.addEventListener(
            "click",
            async () => {

                const text =
                    coverLetterOutput.innerText.trim();

                if (!text) {
                    return;
                }

                try {

                    await navigator.clipboard.writeText(text);

                    const originalText =
                        copyCoverLetterBtn.textContent;

                    copyCoverLetterBtn.textContent =
                        "Copied!";

                    setTimeout(() => {
                        copyCoverLetterBtn.textContent =
                            originalText;
                    }, 1500);

                } catch (error) {

                    console.error(
                        "Copy failed:",
                        error
                    );
                }
            }
        );
    }


    /* RESUME SCORER */

    const scoreJobDescription =
        document.getElementById("scoreJobDescription");

    const scoreResumeBtn =
        document.getElementById("scoreResumeBtn");

    const resumeScoreOutput =
        document.getElementById("resumeScoreOutput");

    const resumeScoreLoading =
        document.getElementById("resumeScoreLoading");

    const resumeScoreError =
        document.getElementById("resumeScoreError");


    if (scoreJobDescription && scoreResumeBtn) {

        scoreResumeBtn.addEventListener(
            "click",
            scoreResume
        );

        async function scoreResume() {

            const description =
                scoreJobDescription.value.trim();

            if (!description) {

                if (resumeScoreError) {
                    resumeScoreError.textContent =
                        "Please enter a job description.";
                }

                return;
            }

            if (resumeScoreError) {
                resumeScoreError.textContent = "";
            }

            scoreResumeBtn.disabled = true;

            if (resumeScoreLoading) {
                resumeScoreLoading.style.display = "block";
            }

            try {

                const response = await fetch(
                    "/career/api/score",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            job_description: description
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        "Unable to score resume."
                    );
                }

                if (resumeScoreOutput) {
                    resumeScoreOutput.textContent =
                        data.response ||
                        "No score result received.";
                }

            } catch (error) {

                if (resumeScoreError) {
                    resumeScoreError.textContent =
                        error.message;
                }

                console.error(
                    "Resume Scorer Error:",
                    error
                );

            } finally {

                scoreResumeBtn.disabled = false;

                if (resumeScoreLoading) {
                    resumeScoreLoading.style.display = "none";
                }
            }
        }
    }


    /* CAREER RECOMMENDATIONS */

    const targetRole =
        document.getElementById("targetRole");

    const recommendationsBtn =
        document.getElementById("recommendationsBtn");

    const recommendationsOutput =
        document.getElementById("recommendationsOutput");

    const recommendationsLoading =
        document.getElementById("recommendationsLoading");

    const recommendationsError =
        document.getElementById("recommendationsError");


    if (targetRole && recommendationsBtn) {

        recommendationsBtn.addEventListener(
            "click",
            getRecommendations
        );

        async function getRecommendations() {

            const role =
                targetRole.value.trim();

            if (recommendationsError) {
                recommendationsError.textContent = "";
            }

            recommendationsBtn.disabled = true;

            if (recommendationsLoading) {
                recommendationsLoading.style.display = "block";
            }

            try {

                const response = await fetch(
                    "/career/api/recommendations",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            target_role: role
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        "Unable to generate recommendations."
                    );
                }

                if (recommendationsOutput) {
                    recommendationsOutput.textContent =
                        data.response ||
                        "No recommendations received.";
                }

            } catch (error) {

                if (recommendationsError) {
                    recommendationsError.textContent =
                        error.message;
                }

                console.error(
                    "Recommendations Error:",
                    error
                );

            } finally {

                recommendationsBtn.disabled = false;

                if (recommendationsLoading) {
                    recommendationsLoading.style.display = "none";
                }
            }
        }
    }

});