document.addEventListener("DOMContentLoaded", () => {

    const jobDescription =
        document.getElementById("jobDescription");

    const generateButton =
        document.getElementById(
            "generateCoverLetterBtn"
        );

    const copyButton =
        document.getElementById(
            "copyCoverLetterBtn"
        );

    const errorMessage =
        document.getElementById(
            "coverLetterError"
        );

    const loadingMessage =
        document.getElementById(
            "coverLetterLoading"
        );

    const output =
        document.getElementById(
            "coverLetterOutput"
        );


    if (!jobDescription || !generateButton || !output) {
        return;
    }


    // COVER LETTER STATE

    let pollingTimer = null;
    let isGenerating = false;


    // LOAD SAVED COVER LETTER STATE

    async function loadCoverLetterState() {

        try {

            const response = await fetch(
                "/career/api/cover_letter/state",
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

                console.error(
                    "Failed to load Cover Letter state:",
                    state.error
                );

                return;
            }


            // Restore Job Description

            if (state.job_description) {

                jobDescription.value =
                    state.job_description;
            }


            // Restore completed result

            if (
                state.status === "completed" &&
                state.result
            ) {

                displayCoverLetter(
                    state.result
                );

                isGenerating = false;
                generateButton.disabled = false;

                hideGeneratingIndicator();

                return;
            }


            // Resume generation state

            if (state.status === "generating") {

                isGenerating = true;
                generateButton.disabled = true;

                showGeneratingIndicator();

                startPolling();

                return;
            }


            // Error state

            if (state.status === "error") {

                isGenerating = false;
                generateButton.disabled = false;

                hideGeneratingIndicator();

                if (errorMessage) {

                    errorMessage.textContent =
                        state.error ||
                        "Unable to generate the cover letter.";
                }
            }

        } catch (error) {

            console.error(
                "Cover Letter state loading error:",
                error
            );
        }
    }


    // GENERATE COVER LETTER

    generateButton.addEventListener(
        "click",
        async () => {

            if (isGenerating) {
                return;
            }


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


            isGenerating = true;
            generateButton.disabled = true;


            // Clear old result

            output.innerHTML = "";


            // Show AI generation indicator

            showGeneratingIndicator();


            try {

                const response = await fetch(
                    "/career/api/cover_letter",
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

                    hideGeneratingIndicator();

                    if (errorMessage) {

                        errorMessage.textContent =
                            data.error ||
                            "Unable to start cover letter generation.";
                    }

                    isGenerating = false;
                    generateButton.disabled = false;

                    return;
                }


                // Generation is running on the server

                startPolling();

            } catch (error) {

                console.error(
                    "Cover Letter API Error:",
                    error
                );


                hideGeneratingIndicator();


                if (errorMessage) {

                    errorMessage.textContent =
                        "Something went wrong while starting the cover letter generation.";
                }


                isGenerating = false;
                generateButton.disabled = false;
            }
        }
    );


    // START POLLING

    function startPolling() {

        if (pollingTimer) {

            clearInterval(
                pollingTimer
            );
        }


        pollingTimer =
            setInterval(
                checkCoverLetterState,
                1000
            );


        checkCoverLetterState();
    }


    // CHECK SERVER STATE

    async function checkCoverLetterState() {

        try {

            const response = await fetch(
                "/career/api/cover_letter/state",
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


            // Still generating

            if (state.status === "generating") {

                isGenerating = true;
                generateButton.disabled = true;

                showGeneratingIndicator();

                return;
            }


            // Generation completed

            if (state.status === "completed") {

                stopPolling();

                hideGeneratingIndicator();


                if (state.job_description) {

                    jobDescription.value =
                        state.job_description;
                }


                displayCoverLetter(
                    state.result
                );


                isGenerating = false;
                generateButton.disabled = false;

                return;
            }


            // Generation failed

            if (state.status === "error") {

                stopPolling();

                hideGeneratingIndicator();


                if (errorMessage) {

                    errorMessage.textContent =
                        state.error ||
                        "Unable to generate the cover letter.";
                }


                isGenerating = false;
                generateButton.disabled = false;
            }

        } catch (error) {

            console.error(
                "Cover Letter polling error:",
                error
            );
        }
    }


    // STOP POLLING

    function stopPolling() {

        if (pollingTimer) {

            clearInterval(
                pollingTimer
            );

            pollingTimer = null;
        }
    }


    // SHOW AI GENERATING INDICATOR

    function showGeneratingIndicator() {

        if (
            document.getElementById(
                "cover-letter-generating-indicator"
            )
        ) {
            return;
        }


        if (!output) {
            return;
        }


        const indicator =
            document.createElement("div");


        indicator.id =
            "cover-letter-generating-indicator";


        indicator.className =
            "cover-letter-generating";


        indicator.innerHTML = `
            <span>AI is generating your cover letter</span>

            <span class="cover-letter-dots">
                <span></span>
                <span></span>
                <span></span>
            </span>
        `;


        output.appendChild(
            indicator
        );
    }


    // HIDE AI GENERATING INDICATOR

    function hideGeneratingIndicator() {

        const indicator =
            document.getElementById(
                "cover-letter-generating-indicator"
            );


        if (indicator) {
            indicator.remove();
        }
    }


    // DISPLAY COVER LETTER

    function displayCoverLetter(result) {

        hideGeneratingIndicator();


        if (typeof result === "string") {

            output.textContent =
                result;

            return;
        }


        if (
            result &&
            typeof result === "object"
        ) {

            output.textContent =
                JSON.stringify(
                    result,
                    null,
                    2
                );

            return;
        }


        output.textContent =
            "Cover letter generated successfully.";
    }


    // COPY COVER LETTER

    if (copyButton) {

        copyButton.addEventListener(
            "click",
            async () => {

                const text =
                    output.innerText.trim();


                if (!text) {
                    return;
                }


                try {

                    await navigator.clipboard.writeText(
                        text
                    );


                    copyButton.textContent =
                        "Copied!";


                    setTimeout(() => {

                        copyButton.textContent =
                            "Copy";

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


    // LOAD STATE WHEN PAGE OPENS

    loadCoverLetterState();

});