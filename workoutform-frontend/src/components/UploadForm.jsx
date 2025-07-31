import { useState } from 'react';
import API from '../api'; // axios instance

function UploadForm() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleUpload = async () => {
    if (!file) return alert("Please select a video first.");

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setResult(null);

    try {
      const res = await API.post('/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(res.data);
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center p-6 bg-gray-100 min-h-screen">
      <div className="bg-white rounded-xl shadow-lg p-6 w-full max-w-md">
        <h1 className="text-2xl font-bold mb-4 text-center">Workout Form Analyzer</h1>
        <div className="flex gap-2 mb-4">
          <input
            type="file"
            onChange={handleFileChange}
            className="border border-gray-300 rounded p-2 w-full"
            accept="video/*"
          />
          <button
            onClick={handleUpload}
            disabled={loading}
            className={`px-4 py-2 rounded text-white ${loading ? 'bg-blue-300' : 'bg-blue-500 hover:bg-blue-600'}`}
          >
            {loading ? "Analyzing..." : "Upload & Analyze"}
          </button>
        </div>

        {result && (
          <div className="space-y-4">
            <p className="text-gray-700 font-medium">Reps Detected: <span className="font-bold">{result.reps}</span></p>

            {result.video_url && (
              <div>
                <p className="text-gray-700 font-medium mb-1">Annotated Video:</p>
                <video
                  src={`http://127.0.0.1:8000${result.video_url}`}
                  controls
                  className="rounded w-full border border-gray-300"
                />
              </div>
            )}

            {result.plot_url && (
              <div>
                <p className="text-gray-700 font-medium mb-1">Knee Angle Plot:</p>
                <img
                  src={`http://127.0.0.1:8000${result.plot_url}`}
                  alt="Knee Angle Plot"
                  className="rounded w-full border border-gray-300"
                />
              </div>
            )}

            {result.csv_url && (
              <a
                href={`http://127.0.0.1:8000${result.csv_url}`}
                download
                className="text-blue-500 hover:underline"
              >
                Download CSV
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default UploadForm;
