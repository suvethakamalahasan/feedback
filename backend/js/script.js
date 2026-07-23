/* =====================================================================
   Sundae Social — script.js
   ---------------------------------------------------------------------
   Shared configuration + customer feedback form logic:
     - Client-side validation
     - Star rating widget wiring
     - Image upload preview + drag/drop
     - Submission via Fetch API (multipart/form-data)
     - Success / error banners
   This file is loaded on BOTH index.html and admin.html, so form-specific
   code is guarded to only run when the relevant elements exist.
   ===================================================================== */

/**
 * Shared API configuration used by both the feedback form and the
 * admin dashboard. Update API_BASE_URL if the backend runs on a
 * different host/port.
 */
const API_CONFIG = {
  BASE_URL: "http://localhost:8000",
  FEEDBACK_ENDPOINT: "/feedback",
};

// =======================================================================
// Feedback form logic (index.html)
// =======================================================================
(function initFeedbackForm() {
  const form = document.getElementById("feedbackForm");
  if (!form) return; // Not on the feedback form page — skip.

  const successBanner = document.getElementById("successBanner");
  const errorBanner = document.getElementById("errorBanner");
  const submitBtn = document.getElementById("submitBtn");
  const submitSpinner = document.getElementById("submitSpinner");
  const submitLabel = submitBtn.querySelector(".submit-label");
  const ratingsError = document.getElementById("ratingsError");
  const commentsField = document.getElementById("comments");
  const commentsCount = document.getElementById("commentsCount");

  const RATING_FIELDS = [
    "taste_rating",
    "quality_rating",
    "staff_rating",
    "cleanliness_rating",
    "overall_rating",
  ];

  // ---------------------------------------------------------------------
  // Star rating: update the small text readout next to each star group
  // ---------------------------------------------------------------------
  RATING_FIELDS.forEach((fieldName) => {
    const radios = form.querySelectorAll(`input[name="${fieldName}"]`);
    const display = form.querySelector(`[data-rating-display="${fieldName}"]`);
    radios.forEach((radio) => {
      radio.addEventListener("change", () => {
        if (display) {
          display.textContent = `${radio.value} / 5`;
        }
        ratingsError.classList.add("d-none");
      });
    });
  });

  // ---------------------------------------------------------------------
  // Comments character counter
  // ---------------------------------------------------------------------
  if (commentsField && commentsCount) {
    commentsField.addEventListener("input", () => {
      commentsCount.textContent = commentsField.value.length;
    });
  }

  // ---------------------------------------------------------------------
  // Image upload: dropzone click, drag & drop, and preview
  // ---------------------------------------------------------------------
  const dropzone = document.getElementById("uploadDropzone");
  const imageInput = document.getElementById("imageUpload");
  const imagePreview = document.getElementById("imagePreview");
  const imageError = document.getElementById("imageError");

  const MAX_IMAGE_BYTES = 5 * 1024 * 1024; // 5MB
  const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

  function handleSelectedFile(file) {
    imageError.classList.add("d-none");
    imageError.textContent = "";

    if (!file) return;

    if (!ALLOWED_TYPES.includes(file.type)) {
      imageError.textContent = "Unsupported file type. Please upload a JPEG, PNG, WEBP, or GIF image.";
      imageError.classList.remove("d-none");
      imageInput.value = "";
      imagePreview.style.display = "none";
      return;
    }

    if (file.size > MAX_IMAGE_BYTES) {
      imageError.textContent = "Image is too large. Please upload a file under 5MB.";
      imageError.classList.remove("d-none");
      imageInput.value = "";
      imagePreview.style.display = "none";
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      imagePreview.style.display = "block";
    };
    reader.readAsDataURL(file);
  }

  if (dropzone && imageInput) {
    dropzone.addEventListener("click", () => imageInput.click());

    dropzone.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        imageInput.click();
      }
    });

    imageInput.addEventListener("change", () => {
      handleSelectedFile(imageInput.files[0]);
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("dragover");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      const file = e.dataTransfer.files[0];
      if (file) {
        imageInput.files = e.dataTransfer.files;
        handleSelectedFile(file);
      }
    });
  }

  // ---------------------------------------------------------------------
  // Validation helpers
  // ---------------------------------------------------------------------
  function ratingsAreComplete() {
    return RATING_FIELDS.every((fieldName) => {
      return form.querySelector(`input[name="${fieldName}"]:checked`) !== null;
    });
  }

  function validateForm() {
    let isValid = true;

    // Bootstrap's built-in constraint validation for standard inputs
    if (!form.checkValidity()) {
      isValid = false;
    }

    // Apply Bootstrap validation styling to each standard field
    Array.from(form.querySelectorAll("input, select, textarea")).forEach((field) => {
      if (field.hasAttribute("required") || field.value) {
        if (field.willValidate) {
          field.classList.toggle("is-invalid", !field.checkValidity());
          field.classList.toggle("is-valid", field.checkValidity());
        }
      }
    });

    // Custom validation: all five star ratings must be selected
    if (!ratingsAreComplete()) {
      ratingsError.classList.remove("d-none");
      isValid = false;
    } else {
      ratingsError.classList.add("d-none");
    }

    // Custom validation: visit_again and recommend_shop pill toggles
    const visitAgainChecked = form.querySelector('input[name="visit_again"]:checked');
    const recommendChecked = form.querySelector('input[name="recommend_shop"]:checked');
    if (!visitAgainChecked || !recommendChecked) {
      isValid = false;
    }

    return isValid;
  }

  function setLoadingState(isLoading) {
    submitBtn.disabled = isLoading;
    submitSpinner.classList.toggle("d-none", !isLoading);
    submitLabel.classList.toggle("d-none", isLoading);
  }

  function showError(message) {
    errorBanner.textContent = message;
    errorBanner.classList.remove("d-none");
    errorBanner.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function clearBanners() {
    errorBanner.classList.add("d-none");
    errorBanner.textContent = "";
  }

  // ---------------------------------------------------------------------
  // Form submission
  // ---------------------------------------------------------------------
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    event.stopPropagation();
    clearBanners();
    successBanner.classList.remove("show");

    if (!validateForm()) {
      form.classList.add("was-validated");
      return;
    }

    setLoadingState(true);

    try {
      const formData = new FormData(form);
      // FormData already captures the file input under the "image" key,
      // and every named field above (including checked radios).

      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.FEEDBACK_ENDPOINT}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        const detail =
          (errorBody && (errorBody.detail || errorBody.message)) ||
          `Something went wrong (status ${response.status}). Please try again.`;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }

      // Success: reset the form and show the success banner
      form.reset();
      form.classList.remove("was-validated");
      Array.from(form.querySelectorAll(".is-valid, .is-invalid")).forEach((el) => {
        el.classList.remove("is-valid", "is-invalid");
      });
      RATING_FIELDS.forEach((fieldName) => {
        const display = form.querySelector(`[data-rating-display="${fieldName}"]`);
        if (display) display.textContent = "Not rated";
      });
      if (commentsCount) commentsCount.textContent = "0";
      if (imagePreview) {
        imagePreview.style.display = "none";
        imagePreview.src = "";
      }

      successBanner.classList.add("show");
      successBanner.scrollIntoView({ behavior: "smooth", block: "center" });
    } catch (err) {
      showError(
        err instanceof Error
          ? `We couldn't submit your feedback: ${err.message}`
          : "We couldn't submit your feedback. Please check your connection and try again."
      );
    } finally {
      setLoadingState(false);
    }
  });

  // Reset button also clears custom widgets and validation state
  form.addEventListener("reset", () => {
    setTimeout(() => {
      form.classList.remove("was-validated");
      Array.from(form.querySelectorAll(".is-valid, .is-invalid")).forEach((el) => {
        el.classList.remove("is-valid", "is-invalid");
      });
      RATING_FIELDS.forEach((fieldName) => {
        const display = form.querySelector(`[data-rating-display="${fieldName}"]`);
        if (display) display.textContent = "Not rated";
      });
      ratingsError.classList.add("d-none");
      if (commentsCount) commentsCount.textContent = "0";
      if (imagePreview) {
        imagePreview.style.display = "none";
        imagePreview.src = "";
      }
      if (imageError) imageError.classList.add("d-none");
      successBanner.classList.remove("show");
      clearBanners();
    }, 0);
  });

  // Prevent selecting a future visit date
  const visitDateInput = document.getElementById("visitDate");
  if (visitDateInput) {
    const today = new Date().toISOString().split("T")[0];
    visitDateInput.max = today;
  }
})();
