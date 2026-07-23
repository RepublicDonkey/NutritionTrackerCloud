const validatedFields = "input[required], select[required], textarea[required]";

function hasAValue(field) {
    return field.value.trim() !== "";
}
// updates the field's state based on its validity and whether the user has interacted with it
function updateFieldState(field, showState) {
    const isValid = field.validity.valid;

    field.classList.toggle("field-invalid", showState && !isValid);
    field.classList.toggle("field-valid", showState && isValid && hasAValue(field));

    if (showState && !isValid) {
        field.setAttribute("aria-invalid", "true");
    } else {
        field.removeAttribute("aria-invalid");
    }
}
// form validation logic
document.querySelectorAll("form").forEach((form) => {
    const fields = form.querySelectorAll(validatedFields);

    form.addEventListener(
        "invalid",
        (event) => {
            if (event.target.matches(validatedFields)) {
                event.target.dataset.validationTouched = "true";
                updateFieldState(event.target, true);
            }
        },
        true,
    );

    fields.forEach((field) => {
        field.addEventListener("blur", () => {
            field.dataset.validationTouched = "true";
            updateFieldState(field, true);
        });

        field.addEventListener("input", () => {
            const showState = field.dataset.validationTouched === "true";
            updateFieldState(field, showState);
        });

        field.addEventListener("change", () => {
            const showState = field.dataset.validationTouched === "true";
            updateFieldState(field, showState);
        });
    });
});
// password policy logic
const password = document.querySelector("#password[autocomplete='new-password']");
const confirmation = document.querySelector("#confirm_password");
const passwordPolicy = document.querySelector("#password-policy");

if (password && confirmation && passwordPolicy) {
    const passwordFields = [password, confirmation];
    const requirements = {
        length: passwordPolicy.querySelector("[data-password-requirement='length']"),
        letter: passwordPolicy.querySelector("[data-password-requirement='letter']"),
        number: passwordPolicy.querySelector("[data-password-requirement='number']"),
        match: passwordPolicy.querySelector("[data-password-requirement='match']"),
    };
    
    function setPasswordPolicyVisibility(isVisible) {
        passwordPolicy.hidden = !isVisible;
        passwordFields.forEach((field) => {
            field.setAttribute("aria-expanded", String(isVisible));
        });
    }

    function updateRequirement(element, isMet, isActive) {
        element.classList.toggle("is-met", isActive && isMet);
        element.classList.toggle("is-unmet", isActive && !isMet);

        const status = !isActive ? "not checked" : isMet ? "met" : "not met";
        element.setAttribute("aria-label", `${element.textContent.trim()}: ${status}`);
    }

    function updatePasswordPolicy() {
        const passwordValue = password.value;
        const confirmationValue = confirmation.value;
        const passwordIsActive = passwordValue.length > 0;
        const confirmationIsActive =
            confirmationValue.length > 0 || passwordIsActive;

        const policy = {
            length: passwordValue.length >= 8,
            letter: /\p{L}/u.test(passwordValue),
            number: /\p{N}/u.test(passwordValue),
            match:
                confirmationValue.length > 0 &&
                passwordValue === confirmationValue,
        };

        updateRequirement(
            requirements.length,
            policy.length,
            passwordIsActive,
        );
        updateRequirement(
            requirements.letter,
            policy.letter,
            passwordIsActive,
        );
        updateRequirement(
            requirements.number,
            policy.number,
            passwordIsActive,
        );
        updateRequirement(
            requirements.match,
            policy.match,
            confirmationIsActive,
        );

        if (
            passwordValue &&
            (!policy.length || !policy.letter || !policy.number)
        ) {
            password.setCustomValidity(
                "Use at least 8 characters with at least one letter and one number.",
            );
        } else {
            password.setCustomValidity("");
        }

        if (confirmationValue && !policy.match) {
            confirmation.setCustomValidity("Passwords do not match.");
        } else {
            confirmation.setCustomValidity("");
        }

        updateFieldState(password, passwordIsActive);
        updateFieldState(confirmation, confirmationValue.length > 0);
    }

    password.addEventListener("input", updatePasswordPolicy);
    confirmation.addEventListener("input", updatePasswordPolicy);

    passwordFields.forEach((field) => {
        field.addEventListener("focus", () => {
            setPasswordPolicyVisibility(true);
        });

        field.addEventListener("blur", () => {
            window.setTimeout(() => {
                if (!passwordFields.includes(document.activeElement)) {
                    setPasswordPolicyVisibility(false);
                }
            }, 0);
        });
    });

    updatePasswordPolicy();
}
