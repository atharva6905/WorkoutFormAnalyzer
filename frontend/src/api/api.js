/**
 * @typedef {Object} AnalysisCreateResponse
 * @property {string} id
 * @property {string} status
 * @property {string} exercise_type
 * @property {string} created_at
 */

/**
 * @typedef {Object} AnalysisStatusResponse
 * @property {string} id
 * @property {string} status
 */

/**
 * @typedef {Object} RepMetricResponse
 * @property {number} rep_index
 * @property {number | null | undefined} start_frame
 * @property {number | null | undefined} end_frame
 * @property {number | null | undefined} min_knee_angle
 * @property {number | null | undefined} max_knee_angle
 * @property {number | null | undefined} min_hip_angle
 * @property {number | null | undefined} max_hip_angle
 * @property {number | null | undefined} confidence_score
 * @property {string | null | undefined} notes
 */

/**
 * @typedef {Object} AnalysisSummary
 * @property {number | null | undefined} rep_count
 * @property {number | null | undefined} avg_confidence
 */

/**
 * @typedef {Object} ArtifactURLs
 * @property {string | null | undefined} annotated_video_url
 * @property {string | null | undefined} csv_url
 * @property {string | null | undefined} plot_url
 */

/**
 * @typedef {Object} AnalysisDetailResponse
 * @property {string} id
 * @property {string} status
 * @property {string} exercise_type
 * @property {AnalysisSummary | null | undefined} summary
 * @property {ArtifactURLs | null | undefined} artifacts
 * @property {RepMetricResponse[]} rep_metrics
 * @property {string | null | undefined} error_message
 * @property {string} created_at
 * @property {string} updated_at
 */

export const BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

/**
 * @template T
 * @param {string} path
 * @param {RequestInit} [options]
 * @returns {Promise<T>}
 */
async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, options);

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const errorBody = await response.json();
      message = errorBody.detail || errorBody.error || message;
    } catch {
      // Ignore parse failures and fall back to the status message.
    }
    throw new Error(message);
  }

  return response.json();
}

/**
 * @param {File} file
 * @param {string} [exerciseType="squat"]
 * @returns {Promise<AnalysisCreateResponse>}
 */
export async function createAnalysis(file, exerciseType = "squat") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("exercise_type", exerciseType);

  return request("/analyses", {
    method: "POST",
    body: formData,
  });
}

/**
 * @param {string} analysisId
 * @returns {Promise<AnalysisStatusResponse>}
 */
export async function getAnalysisStatus(analysisId) {
  return request(`/analyses/${analysisId}/status`);
}

/**
 * @param {string} analysisId
 * @returns {Promise<AnalysisDetailResponse>}
 */
export async function getAnalysis(analysisId) {
  return request(`/analyses/${analysisId}`);
}

/**
 * @param {string} analysisId
 * @param {"video" | "csv" | "plot"} type
 * @returns {string}
 */
export function getArtifactUrl(analysisId, type) {
  return `${BASE_URL}/analyses/${analysisId}/artifacts/${type}`;
}

const api = {
  BASE_URL,
  createAnalysis,
  getAnalysis,
  getAnalysisStatus,
  getArtifactUrl,
  /**
   * Compatibility wrapper for the existing UploadForm while the UI migrates
   * to the queued analysis flow.
   * @param {string} path
   * @param {FormData} body
   * @returns {Promise<{data: AnalysisCreateResponse}>}
   */
  async post(path, body) {
    if (path !== "/analyze" && path !== "/analyses") {
      throw new Error(`Unsupported API path: ${path}`);
    }

    const file = body.get("file");
    const exerciseType = body.get("exercise_type");
    if (!(file instanceof File)) {
      throw new Error("Expected a file in form data.");
    }

    const data = await createAnalysis(
      file,
      typeof exerciseType === "string" && exerciseType ? exerciseType : "squat"
    );
    return { data };
  },
};

export default api;
