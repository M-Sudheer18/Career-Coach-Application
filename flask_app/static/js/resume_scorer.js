document.addEventListener("DOMContentLoaded", () => {
    const jobDescription =
        document.getElementById("scoreJobDescription");

    const scoreButton =
        document.getElementById("scoreResumeBtn");

    const errorMessage =
        document.getElementById("resumeScoreError");

    const loadingMessage =
        document.getElementById("resumeScoreLoading");

    const output =
        document.getElementById("resumeScoreOutput");

    if (!jobDescription || !scoreButton || !output) {
        return;
    }

    let pollingTimer = null;
    let isGenerating = false;


    // =====================================================
    // LOAD CURRENT RESUME SCORER STATE
    // =====================================================

    loadResumeScoreState();


    async function loadResumeScoreState() {
        try {
            const response = await fetch(
                "/career/api/score/state"
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error ||
                    "Unable to load Resume Scorer state."
                );
            }

            restoreState(data);

        } catch (error) {
            console.error(
                "Resume Scorer State Error:",
                error
            );
        }
    }


    // =====================================================
    // RESTORE STATE
    // =====================================================

    function restoreState(data) {

        // Restore Job Description
        if (data.job_description) {
            jobDescription.value =
                data.job_description;
        }

        // Clear previous error
        if (errorMessage) {
            errorMessage.textContent = "";
        }

        // Generation is still running
        if (data.status === "generating") {

            isGenerating = true;

            scoreButton.disabled = true;

            showGeneratingIndicator();

            startPolling();

            return;
        }

        // Generation completed
        if (data.status === "completed") {

            isGenerating = false;

            scoreButton.disabled = false;

            hideGeneratingIndicator();

            displayResult(
                data.result
            );

            return;
        }

        // Generation failed
        if (data.status === "error") {

            isGenerating = false;

            scoreButton.disabled = false;

            hideGeneratingIndicator();

            if (errorMessage) {
                errorMessage.textContent =
                    data.error ||
                    "Unable to score your resume.";
            }

            return;
        }

        // Idle state
        isGenerating = false;

        scoreButton.disabled = false;

        hideGeneratingIndicator();
    }


    // =====================================================
    // GENERATE RESUME SCORE
    // =====================================================

    scoreButton.addEventListener(
        "click",
        async () => {

            const jobDescriptionText =
                jobDescription.value.trim();

            if (errorMessage) {
                errorMessage.textContent = "";
            }

            if (!jobDescriptionText) {

                if (errorMessage) {
                    errorMessage.textContent =
                        "Please enter a job description.";
                }

                return;
            }

            // Prevent duplicate requests
            if (isGenerating) {
                return;
            }

            isGenerating = true;

            scoreButton.disabled = true;

            output.innerHTML = "";

            showGeneratingIndicator();

            try {

                const response = await fetch(
                    "/career/api/score",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            job_description:
                                jobDescriptionText
                        })
                    }
                );

                const data =
                    await response.json();

                if (!response.ok) {

                    throw new Error(
                        data.error ||
                        "Unable to start Resume Scoring."
                    );
                }

                // Background generation started
                startPolling();

            } catch (error) {

                console.error(
                    "Resume Scorer API Error:",
                    error
                );

                isGenerating = false;

                scoreButton.disabled = false;

                hideGeneratingIndicator();

                if (errorMessage) {
                    errorMessage.textContent =
                        error.message ||
                        "Unable to score your resume.";
                }
            }
        }
    );


    // =====================================================
    // START POLLING
    // =====================================================

    function startPolling() {

        stopPolling();

        pollingTimer = setInterval(
            checkResumeScoreState,
            1000
        );

        // Check immediately
        checkResumeScoreState();
    }


    // =====================================================
    // STOP POLLING
    // =====================================================

    function stopPolling() {

        if (pollingTimer !== null) {

            clearInterval(
                pollingTimer
            );

            pollingTimer = null;
        }
    }


    // =====================================================
    // CHECK SERVER STATE
    // =====================================================

    async function checkResumeScoreState() {

        try {

            const response = await fetch(
                "/career/api/score/state"
            );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    data.error ||
                    "Unable to check Resume Scorer state."
                );
            }

            // ---------------------------------------------
            // Still generating
            // ---------------------------------------------

            if (data.status === "generating") {

                isGenerating = true;

                scoreButton.disabled = true;

                showGeneratingIndicator();

                return;
            }

            // ---------------------------------------------
            // Completed
            // ---------------------------------------------

            if (data.status === "completed") {

                stopPolling();

                isGenerating = false;

                scoreButton.disabled = false;

                hideGeneratingIndicator();

                displayResult(
                    data.result
                );

                return;
            }

            // ---------------------------------------------
            // Error
            // ---------------------------------------------

            if (data.status === "error") {

                stopPolling();

                isGenerating = false;

                scoreButton.disabled = false;

                hideGeneratingIndicator();

                if (errorMessage) {
                    errorMessage.textContent =
                        data.error ||
                        "Unable to score your resume.";
                }

                return;
            }

        } catch (error) {

            console.error(
                "Resume Scorer State Polling Error:",
                error
            );

            // Do NOT immediately stop polling.
            // The server-side job may still be running.
        }
    }


    // =====================================================
    // GENERATING INDICATOR
    // =====================================================

    function showGeneratingIndicator() {

        let indicator =
            document.getElementById(
                "resume-score-generating-indicator"
            );

        if (indicator) {
            return;
        }

        indicator =
            document.createElement("div");

        indicator.id =
            "resume-score-generating-indicator";

        indicator.className =
            "resume-score-generating";

        indicator.innerHTML = `
            <span>AI is scoring your resume</span>
            <span class="resume-score-dots">
                <span></span>
                <span></span>
                <span></span>
            </span>
        `;

        if (loadingMessage) {

            loadingMessage.style.display =
                "none";

            loadingMessage.parentNode.insertBefore(
                indicator,
                loadingMessage.nextSibling
            );

        } else {

            output.parentNode.insertBefore(
                indicator,
                output
            );
        }
    }


    // =====================================================
    // HIDE GENERATING INDICATOR
    // =====================================================

    function hideGeneratingIndicator() {

        const indicator =
            document.getElementById(
                "resume-score-generating-indicator"
            );

        if (indicator) {
            indicator.remove();
        }
    }


    // =====================================================
    // DISPLAY RESULT
    // =====================================================

    function displayResult(result) {

        if (!result) {
            output.textContent =
                "Resume scored successfully.";
            return;
        }

        const text = String(result);

        const scoreMatch =
            text.match(/Score:\s*(\d+)/);

        const skillsMatch =
            text.match(/Skills_match_score:\s*(\d+)/);

        const perfectMatch =
            text.match(/Perfect_match_score:\s*(\d+)/);

        if (
            scoreMatch ||
            skillsMatch ||
            perfectMatch
        ) {

            output.innerHTML = `
                <div class="resume-score-results">

                    <p>
                        <strong>Score :</strong>
                        ${scoreMatch ? scoreMatch[1] : "--"}%
                    </p>

                    <p>
                        <strong>Skills_match_score :</strong>
                        ${skillsMatch ? skillsMatch[1] : "--"}%
                    </p>

                    <p>
                        <strong>Perfect_match_score :</strong>
                        ${perfectMatch ? perfectMatch[1] : "--"}%
                    </p>

                </div>
            `;

            return;
        }

        output.textContent = text;
    }
});