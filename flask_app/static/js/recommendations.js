document.addEventListener("DOMContentLoaded", () => {
    const targetRole =
        document.getElementById("targetRole");

    const recommendationsButton =
        document.getElementById(
            "getRecommendationsBtn"
        );
    
    const newRecommendationButton = 
        document.getElementById(
            "newRecommendationBtn"
        );

    const errorMessage =
        document.getElementById(
            "recommendationsError"
        );

    const loadingMessage =
        document.getElementById(
            "recommendationsLoading"
        );

    const output =
        document.getElementById(
            "recommendationsOutput"
        );
    let currentJobId = null;
    let statePollTimer = null;
    
    if (
        !targetRole ||
        !recommendationsButton ||
        !output
    ) {
        return;
    }

    recommendationsButton.addEventListener(
        "click",
        async () => {
            const role =
                targetRole.value.trim();
            currentJobId = null;
            if (statePollTimer) {
                clearInterval(statePollTimer);
                statePollTimer = null;
            }
            errorMessage.textContent = "";

            if (!role) {
                errorMessage.textContent =
                    "Please enter a target job role.";

                return;
            }

            recommendationsButton.disabled =
                true;

            if (loadingMessage) {
                loadingMessage.style.display =
                    "block";
            }

            output.innerHTML = "";

            try {
                const response = await fetch(
                    "/career/api/recommendations",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body: JSON.stringify({
                            target_role: role
                        })
                    }
                );

                const data =
                    await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        "Unable to generate recommendations."
                    );
                }

                currentJobId = data.job_id;
                startRecommendationPolling();

            } catch (error) {
                console.error(
                    "Recommendations API Error:",
                    error
                );

                errorMessage.textContent =
                    error.message ||
                    "Unable to generate recommendations.";

            } finally {
                if (currentJobId) {
                    recommendationsButton.disabled = true;

                    if (loadingMessage) {
                        loadingMessage.style.display =
                            "block";
                    }
                } else {
                    recommendationsButton.disabled =
                        false;

                    if (loadingMessage) {
                        loadingMessage.style.display =
                            "none";
                    }
                }
            }
        }
    );
    if (newRecommendationButton) {
        newRecommendationButton.addEventListener(
            "click",
            resetRecommendationState
        );
    }
    async function resetRecommendationState() {
        try {
            const response = await fetch(
                "/career/api/recommendations/new",
                {
                    method: "POST"
                }
            );

            const data =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error ||
                    "Unable to start a new recommendation."
                );
            }

            currentJobId = null;

            if (statePollTimer) {
                clearInterval(statePollTimer);
                statePollTimer = null;
            }

            targetRole.value = "";

            errorMessage.textContent = "";

            output.innerHTML = "";

            if (loadingMessage) {
                loadingMessage.style.display =
                    "none";
            }

            recommendationsButton.disabled =
                false;

        } catch (error) {
            console.error(
                "Recommendation Reset Error:",
                error
            );

            errorMessage.textContent =
                error.message ||
                "Unable to reset recommendation state.";
        }
    }

    function displayRecommendations(data) {
        const result =
            data.result ||
            data.response ||
            data.recommendations ||
            data;

        if (typeof result !== "string") {
            output.textContent =
                "Recommendations generated successfully.";
            return;
        }

        const lines = result
            .split("\n")
            .map(line => line.trim())
            .filter(line => line);

        output.innerHTML = "";

        let currentSection = null;

        lines.forEach(line => {
            // Remove Markdown symbols generated by the AI
            line = line
                .replace(/^#+\s*/, "")
                .replace(/\*\*/g, "")
                .replace(/^\*\s*/, "");

            if (!line) {
                return;
            }

            // Main sections
            if (
                line === "Skills to Upgrade" ||
                line === "Recommended Certification" ||
                line === "Recommended Project" ||
                line === "Next Step"
            ) {
                currentSection =
                    document.createElement("div");

                currentSection.className =
                    "recommendation-section";

                const heading =
                    document.createElement("h3");

                heading.textContent = line;

                currentSection.appendChild(heading);
                output.appendChild(currentSection);

                return;
            }

            // Numbered skill
            if (/^\d+\.\s/.test(line)) {
                const skill =
                    document.createElement("p");

                skill.className =
                    "recommendation-skill";

                skill.textContent = line;

                if (currentSection) {
                    currentSection.appendChild(skill);
                } else {
                    output.appendChild(skill);
                }

                return;
            }

            // Normal recommendation text
            const text =
                document.createElement("p");

            text.textContent = line;

            if (currentSection) {
                currentSection.appendChild(text);
            } else {
                output.appendChild(text);
            }
        });
    }
    async function checkRecommendationState() {
        try {
            const response = await fetch(
                "/career/api/recommendations/state"
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error ||
                    "Unable to check recommendation state."
                );
            }

            if (data.status === "generating") {
                currentJobId = data.job_id;
                targetRole.value = data.target_role || "";
                recommendationsButton.disabled = true;
                if (newRecommendationButton) {
                    newRecommendationButton.disabled = true;
                }

                if (loadingMessage) {
                    loadingMessage.style.display =
                        "block";
                }
                if (!statePollTimer){
                    startRecommendationPolling();
                }
                return;
            }

            if (data.status === "completed") {
                currentJobId = data.job_id;
                targetRole.value = data.target_role || "";

                clearInterval(statePollTimer);
                statePollTimer = null;

                recommendationsButton.disabled = false;
                if (newRecommendationButton) {
                    newRecommendationButton.disabled = false;
                }

                if (loadingMessage) {
                    loadingMessage.style.display =
                        "none";
                }

                displayRecommendations({
                    result: data.result
                });

                return;
            }

            if (data.status === "error") {
                clearInterval(statePollTimer);
                statePollTimer = null;

                recommendationsButton.disabled = false;

                if (newRecommendationButton) {
                    newRecommendationButton.disabled = false;
                }

                targetRole.value = data.target_role || "";

                if (loadingMessage) {
                    loadingMessage.style.display =
                        "none";
                }

                errorMessage.textContent =
                    data.error ||
                    "Unable to generate recommendations.";

                return;
            }

            if (data.status === "idle") {
                currentJobId = null;

                recommendationsButton.disabled = false;

                if (newRecommendationButton) {
                    newRecommendationButton.disabled = false;
                }

                if (loadingMessage) {
                    loadingMessage.style.display =
                        "none";
                }

                return;
            }

        } catch (error) {
            console.error(
                "Recommendation State Error:",
                error
            );
        }
    }
    function startRecommendationPolling() {
        if (statePollTimer) {
            return;
        }

        statePollTimer = setInterval(
            async () => {
                await checkRecommendationState();
            },
            2000
        );
    }
    checkRecommendationState();
});