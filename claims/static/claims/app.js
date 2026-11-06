document.addEventListener("DOMContentLoaded", () => {
    // CSRF helper function
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // --- ADD MEDICAL PROVIDER / BILL ---
    const billForm = document.getElementById("form-add-bill");
    if (billForm) {
        billForm.addEventListener("submit", (e) => {
            e.preventDefault();

            const caseId = billForm.dataset.caseId;
            const providerInput = document.getElementById("bill-provider");
            const amountInput = document.getElementById("bill-amount");
            const provider = providerInput.value.trim();
            const amount = amountInput.value.trim() || "0.00";

            if (!provider) {
                alert("Please enter a provider name.");
                return;
            }

            fetch(`/case/${caseId}/bill/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken
                },
                body: JSON.stringify({
                    provider: provider,
                    amount: amount
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const billList = document.getElementById("bill-list");
                    const noBillsRow = document.getElementById("no-bills-row");
                    if (noBillsRow) {
                        noBillsRow.remove();
                    }

                    // Format currency
                    const formattedAmount = parseFloat(data.amount).toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });

                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td class="fw-semibold text-dark">${data.provider}</td>
                        <td class="font-monospace">$ ${formattedAmount}</td>
                        <td><span class="badge bg-secondary bg-opacity-10 text-secondary border">Pending</span></td>
                    `;
                    billList.appendChild(tr);

                    // Update total sum on screen
                    const totalElem = document.getElementById("total-medical-amount");
                    if (totalElem) {
                        totalElem.innerText = `$ ${parseFloat(data.total_medical).toLocaleString('en-US', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        })}`;
                    }

                    // Reset form
                    providerInput.value = "";
                    amountInput.value = "";
                } else {
                    alert(data.error || "Failed to add medical bill.");
                }
            })
            .catch(err => {
                console.error("Error adding bill:", err);
                alert("An error occurred while assigning the medical provider.");
            });
        });
    }

    // --- ADD CASE NOTE ---
    const noteForm = document.getElementById("form-add-note");
    if (noteForm) {
        noteForm.addEventListener("submit", (e) => {
            e.preventDefault();

            const caseId = noteForm.dataset.caseId;
            const contentInput = document.getElementById("note-content");
            const content = contentInput.value.trim();

            if (!content) return;

            fetch(`/case/${caseId}/note/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken
                },
                body: JSON.stringify({ content: content })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const noteList = document.getElementById("case-notes-list");
                    const noNotes = document.getElementById("no-notes-message");
                    if (noNotes) noNotes.remove();

                    const noteCard = document.createElement("div");
                    noteCard.className = "card bg-light border-0 mb-2 p-3";
                    noteCard.innerHTML = `
                        <div class="d-flex justify-content-between text-muted small mb-1">
                            <span class="fw-bold text-dark">${data.author}</span>
                            <span>${data.created_at}</span>
                        </div>
                        <p class="mb-0 text-secondary">${data.content}</p>
                    `;
                    noteList.prepend(noteCard);
                    contentInput.value = "";
                } else {
                    alert(data.error || "Failed to add note.");
                }
            })
            .catch(err => console.error("Error adding note:", err));
        });
    }

    // --- UPDATE CASE STATUS ---
    const statusSelect = document.getElementById("case-status-select");
    if (statusSelect) {
        statusSelect.addEventListener("change", () => {
            const caseId = statusSelect.dataset.caseId;
            const newStatus = statusSelect.value;

            fetch(`/case/${caseId}/status/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken
                },
                body: JSON.stringify({ status: newStatus })
            })
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    alert("Error updating status: " + data.error);
                }
            })
            .catch(err => console.error("Error updating status:", err));
        });
    }
});