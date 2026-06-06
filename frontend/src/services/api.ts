// Use relative URLs so Vite's dev proxy forwards requests to the backend.
// This eliminates all CORS issues during development.
const API_BASE_URL = "";

interface RequestOptions extends RequestInit {
  auth?: boolean;
}

async function request(path: string, options: RequestOptions = {}) {
  const { auth = true, headers = {}, ...rest } = options;
  const finalHeaders = new Headers(headers);

  if (auth) {
    const token = localStorage.getItem("gr_token");
    if (token) {
      finalHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  // Fetch API does not automatically set Content-Type for JSON objects, but we must not set it for FormData
  if (!(options.body instanceof FormData) && !finalHeaders.has("Content-Type")) {
    finalHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: finalHeaders,
    ...rest,
  });

  if (!response.ok) {
    let errorMessage = "Request failed";
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // Ignored
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

export const api = {
  // Auth
  async signup(email: string, password: string) {
    return request("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      auth: false,
    });
  },

  async login(email: string, password: string) {
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    const data = await request("/api/auth/token", {
      method: "POST",
      body: formData,
      auth: false,
    });
    if (data.access_token) {
      localStorage.setItem("gr_token", data.access_token);
    }
    return data;
  },

  logout() {
    localStorage.removeItem("gr_token");
    localStorage.removeItem("gr_active_project");
  },

  isLoggedIn() {
    return !!localStorage.getItem("gr_token");
  },

  // Projects
  async getProjects() {
    return request("/api/projects/");
  },

  async createProject(name: string) {
    return request("/api/projects/", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  },

  // API Keys
  async getApiKeys(projectId: string) {
    return request(`/api/projects/${projectId}/keys`);
  },

  async createApiKey(projectId: string, name: string) {
    return request(`/api/projects/${projectId}/keys`, {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  },

  // Sessions
  async getSessions(projectId: string, skip = 0, limit = 100) {
    return request(`/api/sessions/?project_id=${projectId}&skip=${skip}&limit=${limit}`);
  },

  async getSessionDetail(sessionId: string) {
    return request(`/api/sessions/${sessionId}`);
  },

  // Analytics
  async getAnalytics(projectId: string) {
    return request(`/api/projects/${projectId}/analytics`);
  },

  // Delete
  async deleteProject(projectId: string) {
    const token = localStorage.getItem("gr_token");
    const res = await fetch(`/api/projects/${projectId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to delete project");
    }
  },

  async deleteApiKey(projectId: string, keyId: string) {
    const token = localStorage.getItem("gr_token");
    const res = await fetch(`/api/projects/${projectId}/keys/${keyId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to delete API key");
    }
  },

  async deleteSession(sessionId: string) {
    const token = localStorage.getItem("gr_token");
    const res = await fetch(`/api/sessions/${sessionId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to delete session");
    }
  },

  async getMe() {
    return request("/api/auth/me");
  },

  async searchSessions(projectId: string, search: string, skip = 0, limit = 50) {
    const params = new URLSearchParams({
      project_id: projectId,
      skip: String(skip),
      limit: String(limit),
    });
    if (search) params.set("search", search);
    return request(`/api/sessions/?${params.toString()}`);
  },

  async getAnalyticsWithPeriod(projectId: string, periodDays = 30) {
    return request(`/api/projects/${projectId}/analytics?period_days=${periodDays}`);
  },
};
