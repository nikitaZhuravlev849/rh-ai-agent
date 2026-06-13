import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

export const dashboard = {
  getSummary: () => api.get("/dashboard/summary"),
};

export const industry = {
  getStats: () => api.get("/industry/stats"),
  getGapReport: () => api.get("/industry/gap-report"),
  getCompetencies: (params) => api.get("/industry/competencies", { params }),
  parseVacancies: (keywords, area) =>
    api.post("/industry/parse-vacancies", null, { params: { keywords, area } }),
  approvePriority: (industry, competencies) =>
    api.post("/industry/approve-priority", null, {
      params: { industry, priority_competencies: competencies },
    }),
};

export const companies = {
  list: (params) => api.get("/companies/", { params }),
  getTop: (limit = 10) => api.get("/companies/top", { params: { limit } }),
  get: (id) => api.get(`/companies/${id}`),
  create: (data) => api.post("/companies/", data),
  update: (id, data) => api.patch(`/companies/${id}`, data),
  verify: (data) => api.post("/companies/verify-batch", data),
  rescore: (id) => api.post(`/companies/${id}/rescore`),
  getContacts: (id) => api.get(`/companies/${id}/contacts`),
  addContact: (id, data) => api.post(`/companies/${id}/contacts`, data),
};

export const communications = {
  list: (params) => api.get("/communications/", { params }),
  getStats: () => api.get("/communications/stats"),
  generate: (data) => api.post("/communications/generate", data),
  generateBatch: (companyIds, tone) =>
    api.post("/communications/generate-batch", companyIds, { params: { tone } }),
  approve: (data) => api.post("/communications/approve", data),
  send: (id) => api.post(`/communications/${id}/send`),
  handleReply: (data) => api.post("/communications/reply", data),
  autoClassify: (id, replyText) =>
    api.post(`/communications/${id}/auto-classify-reply`, null, {
      params: { reply_text: replyText },
    }),
};

export const projects = {
  catalog: (params) => api.get("/projects/catalog", { params }),
  get: (id) => api.get(`/projects/${id}`),
  generate: (data) => api.post("/projects/generate", data),
  updateStatus: (id, status) =>
    api.patch(`/projects/${id}/status`, null, { params: { status } }),
  getRoles: (id) => api.get(`/projects/${id}/roles`),
};

export default api;
