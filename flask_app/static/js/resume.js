document.addEventListener("DOMContentLoaded", () => {

    const resumeFile =
        document.getElementById("resumeFile");

    const uploadResumeBtn =
        document.getElementById("uploadResumeBtn");

    const resumeError =
        document.getElementById("resumeError");

    const resumeResult =
        document.getElementById("resumeResult");

    const resumeLoading =
        document.getElementById("resumeLoading");

    const selectedFile =
        document.getElementById("selectedFile");


    if (!resumeFile || !uploadResumeBtn) {
        return;
    }
    // INITIAL PAGE STATE

    uploadResumeBtn.style.display = "none";

    if (selectedFile) {
        selectedFile.style.display = "none";
    }


    // CHECK RESUME STATUS FROM SERVER

    fetch("/resume/status")
        .then(response => response.json())
        .then(data => {

            if (data.resume_uploaded === true) {

                // Resume was already processed

                uploadResumeBtn.style.display = "none";

                if (selectedFile) {
                    selectedFile.style.display = "none";
                }

                if (resumeResult) {

                    resumeResult.innerHTML = `
                        <div class="resume-success-message">

                            <h3>Resume Already Processed ✓</h3>

                            <p>
                                Your resume has already been uploaded
                                and analyzed successfully.
                            </p>
                            <p>
                                <strong>Resume:</strong>
                                ${data.resume_filename || "Unknown file"}
                            </p>

                        </div>
                    `;
                }

            }

        })
        .catch(error => {

            console.error(
                "Unable to check resume status:",
                error
            );

        });


    // FILE SELECTION

    resumeFile.addEventListener("change", () => {

        const file = resumeFile.files[0];

        /* No file selected */

        if (!file) {

            uploadResumeBtn.style.display = "none";

            if (selectedFile) {
                selectedFile.style.display = "none";
                selectedFile.textContent = "";
            }

            return;
        }


        /* Check PDF */

        if (file.type !== "application/pdf") {

            if (resumeError) {
                resumeError.textContent =
                    "Please select a PDF file.";
            }

            resumeFile.value = "";

            uploadResumeBtn.style.display = "none";

            if (selectedFile) {
                selectedFile.style.display = "none";
                selectedFile.textContent = "";
            }

            return;
        }


        /* Valid PDF */

        if (resumeError) {
            resumeError.textContent = "";
        }


        /* Show selected filename */

        if (selectedFile) {

            selectedFile.textContent =
                `Selected file: ${file.name}`;

            selectedFile.style.display = "block";
        }


        /* Show Analyze Resume button */

        uploadResumeBtn.style.display = "flex";
    });


    // ANALYZE RESUME

    uploadResumeBtn.addEventListener("click", async () => {

        const file = resumeFile.files[0];


        /* Clear previous messages */

        if (resumeError) {
            resumeError.textContent = "";
        }

        if (resumeResult) {
            resumeResult.innerHTML = "";
        }


        /* No file */

        if (!file) {

            if (resumeError) {
                resumeError.textContent =
                    "Please select a resume PDF.";
            }

            return;
        }


        /* PDF validation */

        if (file.type !== "application/pdf") {

            if (resumeError) {
                resumeError.textContent =
                    "Please upload a PDF file.";
            }

            return;
        }


        try {

            /* Disable button */

            uploadResumeBtn.disabled = true;


            /* Show loading */

            if (resumeLoading) {
                resumeLoading.style.display = "block";
            }


            /*
             * Current Flask API expects:
             *
             * {
             *     "file_path": "..."
             * }
             *
             * We will fix the actual PDF upload
             * separately.
             */

            const formData = new FormData();
            formData.append(
                "resume",
                file
            );

            const response = await fetch(
                "/resume/upload",
                {
                    method: "POST",
                    body: formData
                }
            );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.error ||
                    "Unable to process the resume."
                );
            }
            displayResumeResult(data);

            if (typeof enableResumeFeatures === "function") {

                enableResumeFeatures();

            }

        } catch (error) {
            console.error(
                "Resume upload failed:",
                error
            );


            if (resumeError) {

                resumeError.textContent =
                    error.message ||
                    "Unable to process the resume.";
            }


        } finally {

            uploadResumeBtn.disabled = false;


            if (resumeLoading) {
                resumeLoading.style.display = "none";
            }
        }
    });


    // DISPLAY RESULT

    function displayResumeResult(data) {

        if (!resumeResult) {
            return;
        }

        const chunksProcessed =
            data.chunks_processed || 0;

        const message =
            data.message ||
            "Resume processed successfully.";

        resumeResult.innerHTML = `
            <div class="resume-success-message">

                <h3>Resume Processed Successfully ✓</h3>

                <p>${message}</p>

                <p>
                    <strong>
                        Processed Chunks:
                    </strong>
                    ${chunksProcessed}
                </p>

            </div>
        `;
    }

});