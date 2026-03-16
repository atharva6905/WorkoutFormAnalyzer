import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { createAnalysis } from '../api/api';

function formatFileSize(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }

  return `${size.toFixed(size >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

function UploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [exerciseType, setExerciseType] = useState('squat');
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleFileSelection = (file) => {
    if (!file) return;

    if (!file.type.startsWith('video/')) {
      setErrorMessage('Please choose a valid video file.');
      return;
    }

    setSelectedFile(file);
    setErrorMessage('');
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    handleFileSelection(event.dataTransfer.files?.[0] || null);
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setErrorMessage('');

    try {
      const analysis = await createAnalysis(selectedFile, exerciseType);
      navigate(`/results/${analysis.id}`);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-12 text-slate-900">
      <div className="mx-auto max-w-3xl">
        <div className="mb-8 text-center text-white">
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.35em] text-blue-300">
            Workout Form Analyzer
          </p>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">Upload a lift. Get form feedback.</h1>
          <p className="mx-auto mt-4 max-w-2xl text-base text-slate-300 sm:text-lg">
            Start with a short exercise clip and we&apos;ll process it into rep metrics, annotated video, and angle
            reports.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="rounded-3xl bg-white p-6 shadow-2xl shadow-slate-950/30 sm:p-8">
          <div className="space-y-6">
            <div>
              <label className="mb-3 block text-sm font-semibold text-slate-700">Video Upload</label>
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={handleBrowseClick}
                className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-colors ${
                  isDragging
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-slate-300 bg-slate-50 hover:border-indigo-400 hover:bg-indigo-50/50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*"
                  className="hidden"
                  onChange={(event) => handleFileSelection(event.target.files?.[0] || null)}
                />
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-slate-900 text-lg font-semibold text-white">
                  MP4
                </div>
                <p className="mt-4 text-lg font-semibold text-slate-900">Drag and drop a video here</p>
                <p className="mt-2 text-sm text-slate-500">or click to browse your device</p>
                <p className="mt-2 text-xs uppercase tracking-[0.25em] text-slate-400">Accepted: video/*</p>
              </div>

              {selectedFile && (
                <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <p className="text-sm font-semibold text-slate-900">{selectedFile.name}</p>
                  <p className="mt-1 text-sm text-slate-500">{formatFileSize(selectedFile.size)}</p>
                </div>
              )}
            </div>

            <div>
              <label htmlFor="exercise-type" className="mb-3 block text-sm font-semibold text-slate-700">
                Exercise Type
              </label>
              <select
                id="exercise-type"
                value={exerciseType}
                onChange={(event) => setExerciseType(event.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none ring-0 transition focus:border-indigo-500"
              >
                <option value="squat">Squat</option>
              </select>
            </div>

            {errorMessage && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {errorMessage}
              </div>
            )}

            <button
              type="submit"
              disabled={!selectedFile || isUploading}
              className="inline-flex w-full items-center justify-center rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {isUploading ? (
                <span className="flex items-center gap-3">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                  Uploading...
                </span>
              ) : (
                'Analyze'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default UploadPage;
