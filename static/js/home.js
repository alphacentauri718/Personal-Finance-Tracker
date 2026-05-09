
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

async function applyFilter() {

    // Prevent empty selection
    if (selectedAccounts.size === 0) {
        alert("Select at least one account");
        return;
    }

    const response = await fetch("/dashboard-data", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            account_ids: Array.from(selectedAccounts)
        })
    });

    const data = await response.json();

    // Update dashboard UI
    updateDashboard(data);

    // Close modal
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