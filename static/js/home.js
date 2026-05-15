
let selectedAccounts = new Set();

document.addEventListener("DOMContentLoaded", () => {

    // Get all account pills
    const pills = document.querySelectorAll(".pill");
    
    pills.forEach(pill => {

        // Read metadata from HTML
        const id = parseInt(pill.dataset.id);

        // Default behavior:
        // all accounts start selected
        selectedAccounts.add(id);

        // Toggle logic
        pill.addEventListener("click", () => {
            togglePill(pill);
        });
    });
});

// ==========================================
// Additional bank account button
// ==========================================
const addBankButton =
    document.getElementById("additional-accounts-button");

if (addBankButton) {

    addBankButton.onclick = async () => {

        // Get link token
        const res = await fetch("/plaid/link-token", {

            method: "POST"
        });

        const data = await res.json();

        // Open Plaid Link
        const handler = Plaid.create({

            token: data.link_token,

            onSuccess: async function(public_token) {

                // Exchange for NEW access token
                await fetch("/plaid/exchange-token", {

                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        public_token
                    })
                });

                // Refresh dashboard
                window.location.reload();
            }
        });

        handler.open();
    };
}


// ==========================================
// Toggle pill selection
// ==========================================

function togglePill(pill) {

    const id = parseInt(pill.dataset.id);

    // If selected -> deselect
    if (selectedAccounts.has(id)) {

        selectedAccounts.delete(id);

        // Gray styling
        pill.classList.remove(
            "bg-blue-600",
            "text-white",
            "border-blue-600"
        );

        pill.classList.add(
            "bg-gray-200",
            "text-gray-700",
            "border-gray-300"
        );

    }

    // If deselected -> select
    else {

        selectedAccounts.add(id);

        // Blue styling
        pill.classList.add(
            "bg-blue-600",
            "text-white",
            "border-blue-600"
        );

        pill.classList.remove(
            "bg-gray-200",
            "text-gray-700",
            "border-gray-300"
        );
    }

    // Show Apply / Save buttons
    document
        .getElementById("actionButtons")
        .classList.remove("hidden");
}


// ==========================================
// Open modal
// ==========================================

function openAccountModal() {

    document
        .getElementById("accountModal")
        .classList.remove("hidden");
}

// ==========================================
// Open views
// ==========================================

function openViews() {
    
    document
        .getElementById("accountsHeader")
        .classList.add("hidden");

    document
        .getElementById("hidden accountPills")
        .classList.add("hidden");

    document
        .getElementById("viewsHeader")
        .classList.remove("hidden");

    document
        .getElementById("viewButtons")
        .classList.remove("hidden");

    document
        .getElementById("savedViewButton")
        .classList.add("hidden");

    document
        .getElementById("backToAccountsButton")
        .classList.remove("hidden");

    document
        .getElementById("actionButtons")
        .classList.add("hidden");
}
// ==========================================
// Back to accounts
// ==========================================

function back2accounts() {

    document
        .getElementById("accountsHeader")
        .classList.remove("hidden");

    document
        .getElementById("hidden accountPills")
        .classList.remove("hidden");

    document
        .getElementById("viewButtons")
        .classList.add("hidden");

    document
        .getElementById("viewsHeader")
        .classList.add("hidden");

    document
        .getElementById("savedViewButton")
        .classList.remove("hidden");

    document
        .getElementById("backToAccountsButton")
        .classList.add("hidden");

}

// ==========================================
// Close modal
// ==========================================

function closeAccountModal() {

    document
        .getElementById("accountModal")
        .classList.add("hidden");
}


// ==========================================
// Apply filter
// ==========================================


async function deleteView(viewId) {

    if (!confirm("Delete this view?")) {
    return;
    }
    const response = await fetch(`/views/delete/${viewId}`, {

        method: "POST"
    });

    if (response.ok) {

        // Remove pill from page instantly
        document
            .getElementById(`view-pill-${viewId}`)
            .remove();
    }
}


async function applyFilter(savedViewIds = null) {

    // Decide where account IDs come from
    const accountIds = savedViewIds
        ? savedViewIds
        : Array.from(selectedAccounts);


    // Prevent empty selection
    if (accountIds.length === 0) {

        alert("Select at least one account");
        return;
    }


    const response = await fetch("/dashboard-data", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            account_ids: accountIds
        })
    });

    const data = await response.json();

    updateDashboard(data);

    closeAccountModal();
}


// ==========================================
// Update dashboard dynamically
// ==========================================

function updateDashboard(data) {

    // ============================
    // Totals
    // ============================
    
    const netWorthElement =
        document.getElementById("net-worth");

    netWorthElement.innerText =
        "$" + data.net_worth.toFixed(2);

    // Green if positive
    if (data.net_worth >= 0) {

        netWorthElement.classList.remove("text-red-500");
        netWorthElement.classList.add("text-green-500");

    }

    // Red if negative
    else {

        netWorthElement.classList.remove("text-green-500");
        netWorthElement.classList.add("text-red-500");
    }


    document.getElementById("total-assets").innerText =
        "$" + data.total_assets.toFixed(2);

    document.getElementById("total-expenses").innerText =
        "$" + data.total_expenses.toFixed(2);


}


// ==========================================
// Show Save View section
// ==========================================

function showSaveView() {

    document
        .getElementById("saveViewSection")
        .classList.remove("hidden");
}


// ==========================================
// Save view
// ==========================================

async function saveView() {

    const name =
        document.getElementById("viewName").value;

    if (!name.trim()) {
        alert("Enter a view name");
        return;
    }

    const response = await fetch("/views/save", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            name: name,

            account_ids:
                Array.from(selectedAccounts)
        })
    });

    const data = await response.json();

    // Reload page so new view button appears
    window.location.reload();
}