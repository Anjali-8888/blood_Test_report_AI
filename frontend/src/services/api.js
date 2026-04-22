import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Upload and analyze a blood test PDF report.
 * @param {File} file - The PDF file to upload
 * @param {string} gender - "male" | "female" | "unknown"
 * @returns {Promise<Object>} - Analysis result
 */
export async function analyzeReport(file, gender = "unknown") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("gender", gender);

  const response = await axios.post(`${API_BASE}/analyze`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    timeout: 120000, // 2 min timeout for Gemini processing
  });

  return response.data;
}

/**
 * Fetch all reference ranges from the API.
 * @returns {Promise<Object>}
 */
export async function getReferenceRanges() {
  const response = await axios.get(`${API_BASE}/reference-ranges`);
  return response.data;
}

/**
 * Check API health.
 * @returns {Promise<Object>}
 */
export async function checkHealth() {
  const response = await axios.get(`${API_BASE}/health`);
  return response.data;
}
