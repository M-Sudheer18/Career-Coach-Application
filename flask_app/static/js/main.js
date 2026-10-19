// Dark Mode
document.addEventListener("DOMContentLoaded", () => {

    const themeToggle =
        document.getElementById("themeToggle");

    if (!themeToggle) {
        return;
    }

    // Check previously selected theme
    const savedTheme =
        localStorage.getItem("theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
        themeToggle.textContent = "☀";
    }

    themeToggle.addEventListener("click", () => {

        document.body.classList.toggle("dark-mode");

        const isDarkMode =
            document.body.classList.contains("dark-mode");

        if (isDarkMode) {

            themeToggle.textContent = "☀";

            localStorage.setItem(
                "theme",
                "dark"
            );

        } else {

            themeToggle.textContent = "☾";

            localStorage.setItem(
                "theme",
                "light"
            );
        }

    });

});

document.addEventListener("DOMContentLoaded", async () => {

    let resumeUploaded = false;


    try {

        const response = await fetch(
            "/resume/status"
        );

        const data =
            await response.json();

        resumeUploaded =
            data.resume_uploaded === true;

    } catch (error) {

        console.error(
            "Unable to check resume status:",
            error
        );

    }


    if (!resumeUploaded) {

        disableResumeFeatures();

    } else {

        enableResumeFeatures();

    }

});


function disableResumeFeatures() {


    // RESUME SCORER

    const scoreButton =
        document.getElementById(
            "scoreResumeBtn"
        );

    const scoreInput =
        document.getElementById(
            "scoreJobDescription"
        );


    if (scoreButton) {

        scoreButton.disabled = true;

        scoreButton.title =
            "Please upload and analyze your resume first.";

    }


    if (scoreInput) {

        scoreInput.disabled = true;

        scoreInput.placeholder =
            "Upload and analyze your resume first.";

    }


    // CAREER COACH

    const careerButton =
        document.getElementById(
            "career-send-btn"
        );

    const careerInput =
        document.getElementById(
            "career-question"
        );


    if (careerButton) {

        careerButton.disabled = true;

        careerButton.title =
            "Please upload and analyze your resume first.";

    }


    if (careerInput) {

        careerInput.disabled = true;

        careerInput.placeholder =
            "Upload and analyze your resume first.";

    }


    // COVER LETTER

    const coverLetterButton =
        document.getElementById(
            "generateCoverLetterBtn"
        );

    const coverLetterInput =
        document.getElementById(
            "jobDescription"
        );


    if (coverLetterButton) {

        coverLetterButton.disabled = true;

        coverLetterButton.title =
            "Please upload and analyze your resume first.";

    }


    if (coverLetterInput) {

        coverLetterInput.disabled = true;

        coverLetterInput.placeholder =
            "Upload and analyze your resume first.";

    }


    // RECOMMENDATIONS

    const recommendationsButton =
        document.getElementById(
            "getRecommendationsBtn"
        );

    const recommendationsInput =
        document.getElementById(
            "targetRole"
        );


    if (recommendationsButton) {

        recommendationsButton.disabled = true;

        recommendationsButton.title =
            "Please upload and analyze your resume first.";

    }


    if (recommendationsInput) {

        recommendationsInput.disabled = true;

        recommendationsInput.placeholder =
            "Upload and analyze your resume first.";

    }


    // AI INTERVIEW

    const interviewInput =
        document.getElementById(
            "candidate-answer"
        );

    const interviewButton =
        document.getElementById(
            "interview-send-btn"
        );


    if (interviewInput) {

        interviewInput.disabled = true;

        interviewInput.placeholder =
            "Please upload and analyze your resume first.";

    }


    if (interviewButton) {

        interviewButton.disabled = true;

        interviewButton.title =
            "Please upload and analyze your resume first.";

    }

}


function enableResumeFeatures() {


    const elements = [

        "scoreResumeBtn",
        "scoreJobDescription",

        "career-send-btn",
        "career-question",

        "generateCoverLetterBtn",
        "jobDescription",

        "getRecommendationsBtn",
        "targetRole",

        "candidate-answer",
        "interview-send-btn"

    ];


    elements.forEach((id) => {

        const element =
            document.getElementById(id);


        if (element) {

            element.disabled = false;

            element.title = "";

        }

    });

}