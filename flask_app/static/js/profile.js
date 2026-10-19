document.addEventListener("DOMContentLoaded", () => {

    // Elements
    const editNameBtn =
        document.getElementById("editNameBtn");

    const saveNameBtn =
        document.getElementById("saveNameBtn");

    const cancelNameBtn =
        document.getElementById("cancelNameBtn");

    const nameEditContainer =
        document.getElementById("nameEditContainer");

    const nameInput =
        document.getElementById("nameInput");

    const profileName =
        document.getElementById("profileName");

    const profileInfoName =
        document.getElementById("profileInfoName");


    // Edit username
    if (editNameBtn) {
        editNameBtn.addEventListener("click", () => {
            nameEditContainer.classList.add("active");
            nameInput.focus();
            nameInput.select();
        });
    }


    // Cancel username edit

    if (cancelNameBtn) {

        cancelNameBtn.addEventListener("click", () => {

            nameEditContainer.classList.remove("active");

            nameInput.value =
                profileName.textContent.trim();

        });

    }


    // Save username

    if (saveNameBtn) {

        saveNameBtn.addEventListener(
            "click",
            async () => {

                const userName =
                    nameInput.value.trim();


                if (!userName) {

                    alert(
                        "Name cannot be empty."
                    );

                    return;

                }


                try {

                    const response =
                        await fetch(
                            "/profile/update-name",
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },

                                body: JSON.stringify({
                                    user_name:
                                        userName
                                })

                            }
                        );


                    const data =
                        await response.json();


                    if (!response.ok) {

                        alert(
                            data.message ||
                            "Unable to update name."
                        );

                        return;

                    }


                    // Update Profile Name

                    profileName.textContent =
                        data.user_name;


                    // Update Profile Information

                    profileInfoName.textContent =
                        data.user_name;


                    // Close Edit Section

                    nameEditContainer.classList.remove(
                        "active"
                    );

                } catch (error) {

                    console.error(
                        "Name update error:",
                        error
                    );

                    alert(
                        "Something went wrong. Please try again."
                    );

                }

            }
        );

    }


    // Profile image

    const editImageBtn =
        document.getElementById("editImageBtn");

    const profileImageInput =
        document.getElementById(
            "profileImageInput"
        );

    const profileAvatar =
        document.getElementById(
            "profileAvatar"
        );


    // Open File Selector

    if (editImageBtn) {

        editImageBtn.addEventListener(
            "click",
            () => {

                profileImageInput.click();

            }
        );

    }


    // Upload profile image

    if (profileImageInput) {

        profileImageInput.addEventListener(
            "change",
            async () => {

                const file =
                    profileImageInput.files[0];


                if (!file) {

                    return;

                }


                // Check File Type

                if (
                    !file.type.startsWith(
                        "image/"
                    )
                ) {

                    alert(
                        "Please select a valid image file."
                    );

                    return;

                }


                const formData =
                    new FormData();


                formData.append(
                    "profile_image",
                    file
                );


                try {

                    const response =
                        await fetch(
                            "/profile/upload-image",
                            {
                                method: "POST",

                                body: formData
                            }
                        );


                    const data =
                        await response.json();


                    if (!response.ok) {

                        alert(
                            data.message ||
                            "Unable to upload image."
                        );

                        return;

                    }


                    // Create Profile Image

                    profileAvatar.innerHTML = `
                        <img
                            src="${data.profile_image}"
                            alt="Profile Image"
                            id="profileImage"
                        >
                    `;

                } catch (error) {

                    console.error(
                        "Image upload error:",
                        error
                    );

                    alert(
                        "Unable to upload image."
                    );

                }

            }
        );

    }

});