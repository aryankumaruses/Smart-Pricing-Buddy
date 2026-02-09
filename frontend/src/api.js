import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

/** POST /api/search */
export async function postSearch(payload) {
  const { data } = await api.post("/search/", payload);
  return data;
}

/** GET /api/search/quick */
export async function quickSearch(params) {
  const { data } = await api.get("/search/quick", { params });
  return data;
}

/** GET /api/deals */
export async function getDeals(category) {
  const { data } = await api.get("/deals/", { params: { category } });
  return data;
}

/** GET /api/health */
export async function getHealth() {
  const { data } = await api.get("/health");
  return data;
}

/** GET /api/platforms */
export async function getPlatforms() {
  const { data } = await api.get("/platforms");
  return data;
}

export default api;
