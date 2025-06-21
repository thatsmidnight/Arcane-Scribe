document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    const loginView = document.getElementById("login-view");
    const appView = document.getElementById("app-view");
    const loginError = document.getElementById("login-error");

    // Replace with your actual API Gateway URL
    const API_BASE_URL = "https://arcane-scribe.thatsmidnight.com/api/v1"; 

    // --- LOGIN LOGIC ---
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        loginError.textContent = "";

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Login failed");
            }

            // Store tokens securely. localStorage is simple for now.
            localStorage.setItem("idToken", data.IdToken);
            localStorage.setItem("accessToken", data.AccessToken);
            localStorage.setItem("refreshToken", data.RefreshToken);

            // Switch views
            loginView.classList.add("d-none");
            appView.classList.remove("d-none");

        } catch (error) {
            console.error("Login Error:", error);
            loginError.textContent = `Error: ${error.message}`;
        }
    });

    // --- EXAMPLE RAG QUERY LOGIC ---
    const queryButton = document.getElementById("query-button");
    const queryInput = document.getElementById("query-input");
    const srdIdInput = document.getElementById("srd-id-input");
    const responseArea = document.getElementById("response-area");

    queryButton.addEventListener("click", async () => {
        const query = queryInput.value;
        const srdId = srdIdInput.value;
        if (!query) return;
        if (!srdId) return;

        responseArea.textContent = "Getting answer...";
        
        // This function would make the authenticated API call
        const response = await makeAuthenticatedRequest("/query", "POST", {
            query_text: query,
            srd_id: srdId
        });
        
        responseArea.textContent = JSON.stringify(response, null, 2);
    });

    // --- AUTHENTICATED API REQUEST HELPER ---
    async function makeAuthenticatedRequest(endpoint, method, body = null) {
        const idToken = localStorage.getItem("idToken");

        if (!idToken) {
            // Handle not being logged in
            console.error("No ID Token found. Please log in.");
            // Here you would redirect to login or show the login form
            return;
        }
        
        const headers = {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${idToken}`
        };

        const config = {
            method: method,
            headers: headers,
        };
        
        if (body) {
            config.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

            // TODO: Add logic here to check for 401 Unauthorized and use the
            // RefreshToken to get a new IdToken.

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error("Authenticated request failed:", error);
            responseArea.textContent = `API Error: ${error.message}`;
        }
    }
});