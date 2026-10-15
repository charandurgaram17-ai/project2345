/**
 * FarmDirect AI — Frontend Interactions
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Initialize Bootstrap Tooltips if available
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 2. Dynamic Order Total Calculation
  const quantityInput = document.getElementById("orderQuantityInput");
  const unitPriceAttr = document.getElementById("orderUnitPrice");
  const orderSubtotalDisplay = document.getElementById("orderSubtotalDisplay");
  const orderTotalDisplay = document.getElementById("orderTotalDisplay");

  if (quantityInput && unitPriceAttr) {
    const unitPrice = parseFloat(unitPriceAttr.dataset.price || "0");
    const maxQty = parseFloat(quantityInput.getAttribute("max") || "999999");

    function updateCalculations() {
      let qty = parseFloat(quantityInput.value || "0");
      if (qty < 0) qty = 0;
      if (qty > maxQty) {
        quantityInput.value = maxQty;
        qty = maxQty;
      }
      const total = qty * unitPrice;
      const formatted = "₹" + total.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      
      if (orderSubtotalDisplay) orderSubtotalDisplay.textContent = formatted;
      if (orderTotalDisplay) orderTotalDisplay.textContent = formatted;
    }

    quantityInput.addEventListener("input", updateCalculations);
    quantityInput.addEventListener("change", updateCalculations);
    updateCalculations();
  }

  // 3. AI Fair Price Assistant interactive calculator in Add/Edit Product forms
  const aiPriceBtn = document.getElementById("btnFetchAiPrice");
  if (aiPriceBtn) {
    aiPriceBtn.addEventListener("click", function () {
      const nameField = document.getElementById("productNameInput");
      const categoryField = document.getElementById("productCategorySelect");
      const qtyField = document.getElementById("productQuantityInput");
      const unitField = document.getElementById("productUnitSelect");
      const harvestField = document.getElementById("productHarvestDateInput");
      const districtField = document.getElementById("productDistrictInput");
      const priceTargetInput = document.getElementById("productPriceInput");

      const resultContainer = document.getElementById("aiPriceResultContainer");
      const spinner = document.getElementById("aiPriceSpinner");

      if (!nameField || !nameField.value.trim()) {
        alert("Please enter a product name first to calculate the fair price recommendation.");
        nameField.focus();
        return;
      }

      if (spinner) spinner.classList.remove("d-none");
      aiPriceBtn.disabled = true;

      const payload = {
        product_name: nameField.value.trim(),
        category: categoryField ? categoryField.value : "Vegetables",
        quantity: qtyField ? parseFloat(qtyField.value || "100") : 100,
        unit: unitField ? unitField.value : "kg",
        district: districtField ? districtField.value.trim() : "",
        harvest_date: harvestField ? harvestField.value : ""
      };

      // Retrieve CSRF token from page
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                        document.querySelector('input[name="csrf_token"]')?.value;

      fetch("/api/ai/estimate-price", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken
        },
        body: JSON.stringify(payload)
      })
      .then(response => response.json())
      .then(data => {
        if (spinner) spinner.classList.add("d-none");
        aiPriceBtn.disabled = false;

        if (resultContainer) {
          resultContainer.classList.remove("d-none");
          resultContainer.innerHTML = `
            <div class="card border-success bg-light mt-3">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <h6 class="text-success mb-0 fw-bold">
                    <i class="bi bi-robot"></i> AI Fair Price Recommendation
                  </h6>
                  <span class="badge bg-success">${data.confidence_percentage}% Confidence</span>
                </div>
                <div class="d-flex align-items-baseline gap-2 mb-2">
                  <span class="h3 fw-bold text-dark">₹${data.recommended_price}</span>
                  <span class="text-muted">/ ${data.unit}</span>
                  <span class="badge bg-light text-dark border ms-2">Range: ₹${data.price_range.min} - ₹${data.price_range.max}</span>
                </div>
                <p class="small text-muted mb-2">
                  <strong>Source:</strong> ${data.data_source}
                </p>
                <div class="small mb-3">
                  <div class="row g-2">
                    ${data.factors.map(f => `
                      <div class="col-6">
                        <div class="p-1 bg-white border rounded">
                          <strong>${f.name}:</strong> ${f.impact}<br>
                          <span class="text-muted" style="font-size:0.75rem;">${f.explanation}</span>
                        </div>
                      </div>
                    `).join("")}
                  </div>
                </div>
                <button type="button" class="btn btn-sm btn-success w-100" id="btnApplyAiPrice">
                  <i class="bi bi-check-circle"></i> Apply ₹${data.recommended_price} to Price Field
                </button>
              </div>
            </div>
          `;

          const applyBtn = document.getElementById("btnApplyAiPrice");
          if (applyBtn && priceTargetInput) {
            applyBtn.addEventListener("click", function () {
              priceTargetInput.value = data.recommended_price;
              priceTargetInput.classList.add("is-valid");
              setTimeout(() => priceTargetInput.classList.remove("is-valid"), 2000);
            });
          }
        }
      })
      .catch(err => {
        console.error("AI Price error:", err);
        if (spinner) spinner.classList.add("d-none");
        aiPriceBtn.disabled = false;
        alert("Failed to compute AI price estimate. Please ensure server is running.");
      });
    });
  }

  // 4. Quick Demo Login Autofill buttons in login.html
  const demoButtons = document.querySelectorAll(".btn-demo-login");
  demoButtons.forEach(btn => {
    btn.addEventListener("click", function () {
      const email = this.dataset.email;
      const pass = this.dataset.pass || "Password@123";
      const emailInput = document.getElementById("loginEmail");
      const passInput = document.getElementById("loginPassword");
      if (emailInput && passInput) {
        emailInput.value = email;
        passInput.value = pass;
        const form = emailInput.closest("form");
        if (form) form.submit();
      }
    });
  });

  // 5. Auto dismiss flash alerts after 6 seconds
  const autoAlerts = document.querySelectorAll(".alert-dismissible");
  autoAlerts.forEach(alertEl => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
      if (bsAlert) bsAlert.close();
    }, 6000);
  });
});
