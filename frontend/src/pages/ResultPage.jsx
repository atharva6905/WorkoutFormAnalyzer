import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { getAnalysis, getAnalysisStatus, getArtifactUrl } from '../api/api';
import RepMetricsTable from '../components/RepMetricsTable';

function StatusBadge({ status }) {
  const styles = {
    queued: 'border-slate-300 bg-slate-100 text-slate-700',
    processing: 'border-amber-300 bg-amber-100 text-amber-700',
    completed: 'border-emerald-300 bg-emerald-100 text-emerald-700',
    failed: 'border-red-300 bg-red-100 text-red-700',
  };

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-semibold ${
        styles[status] || styles.queued
      }`}
    >
      {status === 'processing' && (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current/30 border-t-current" />
      )}
      {status || 'unknown'}
    </span>
  );
}

function useAnalysisPolling(analysisId) {
  const [status, setStatus] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!analysisId) {
      setError('Analysis not found');
      return undefined;
    }

    let isMounted = true;
    let intervalId = null;

    const loadAnalysisDetail = async () => {
      try {
        const detail = await getAnalysis(analysisId);
        if (!isMounted) return;
        setAnalysis(detail);
      } catch (detailError) {
        if (!isMounted) return;
        setError(detailError instanceof Error ? detailError.message : 'Unable to load analysis details.');
      }
    };

    const checkStatus = async () => {
      try {
        const response = await getAnalysisStatus(analysisId);
        if (!isMounted) return;

        setStatus(response.status);
        setError('');

        if (response.status === 'completed' || response.status === 'failed') {
          if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
          }
          await loadAnalysisDetail();
        }
      } catch (statusError) {
        if (!isMounted) return;
        if (intervalId) {
          clearInterval(intervalId);
          intervalId = null;
        }
        setError(statusError instanceof Error ? statusError.message : 'Analysis not found');
      }
    };

    checkStatus();
    intervalId = setInterval(checkStatus, 2500);

    return () => {
      isMounted = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [analysisId]);

  return { status, analysis, error };
}

function ResultPage() {
  const { analysisId } = useParams();
  const { status, analysis, error } = useAnalysisPolling(analysisId);

  const repCount = analysis?.summary?.rep_count ?? analysis?.rep_metrics?.length ?? 0;

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-12">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex flex-col gap-4 rounded-3xl bg-white p-6 shadow-2xl shadow-slate-950/30 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-blue-500">Analysis Result</p>
            <h1 className="mt-2 text-3xl font-bold text-slate-900">Video Processing Status</h1>
            <p className="mt-2 text-sm text-slate-500">
              Analysis ID: <span className="font-mono">{analysisId || 'unknown'}</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={status} />
            <Link
              to="/"
              className="inline-flex items-center rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              New Upload
            </Link>
          </div>
        </div>

        {error && (
          <div className="rounded-2xl border border-red-300 bg-red-50 px-5 py-4 text-red-700">
            {error.includes('404') ? 'Analysis not found' : error}
          </div>
        )}

        {!error && (status === 'queued' || status === 'processing' || status === null) && (
          <div className="rounded-3xl bg-white p-8 text-center shadow-2xl shadow-slate-950/30">
            <div className="mx-auto flex h-16 w-16 animate-spin items-center justify-center rounded-full border-4 border-indigo-100 border-t-indigo-600" />
            <h2 className="mt-6 text-2xl font-semibold text-slate-900">
              Analyzing your video... this takes 15-30 seconds
            </h2>
            <p className="mt-3 text-slate-500">
              We&apos;re extracting landmarks, detecting reps, and generating your report artifacts.
            </p>
          </div>
        )}

        {!error && status === 'failed' && analysis && (
          <div className="rounded-3xl border border-red-200 bg-white p-8 shadow-2xl shadow-slate-950/30">
            <h2 className="text-2xl font-semibold text-slate-900">Processing failed</h2>
            <p className="mt-3 text-red-700">{analysis.error_message || 'Something went wrong during analysis.'}</p>
          </div>
        )}

        {!error && status === 'completed' && analysis && (
          <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-3">
              <div className="rounded-3xl bg-white p-6 shadow-2xl shadow-slate-950/20">
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Rep Count</p>
                <p className="mt-3 text-4xl font-bold text-slate-900">{repCount}</p>
              </div>
              <div className="rounded-3xl bg-white p-6 shadow-2xl shadow-slate-950/20">
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Exercise</p>
                <p className="mt-3 text-2xl font-bold capitalize text-slate-900">{analysis.exercise_type}</p>
              </div>
              <div className="rounded-3xl bg-white p-6 shadow-2xl shadow-slate-950/20">
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Average Confidence</p>
                <p className="mt-3 text-2xl font-bold text-slate-900">
                  {analysis.summary?.avg_confidence != null ? analysis.summary.avg_confidence.toFixed(2) : '-'}
                </p>
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
              <div className="rounded-3xl bg-white p-6 shadow-2xl shadow-slate-950/20">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-slate-900">Annotated Video</h2>
                  <a
                    href={getArtifactUrl(analysis.id, 'video')}
                    download
                    className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
                  >
                    Download Video
                  </a>
                </div>
                <video
                  controls
                  src={getArtifactUrl(analysis.id, 'video')}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-950"
                />
              </div>

              <div className="rounded-3xl bg-white p-6 shadow-2xl shadow-slate-950/20">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-slate-900">Knee Angle Plot</h2>
                  <a
                    href={getArtifactUrl(analysis.id, 'csv')}
                    download
                    className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    Download CSV
                  </a>
                </div>
                <img
                  src={getArtifactUrl(analysis.id, 'plot')}
                  alt="Knee angle plot"
                  className="w-full rounded-2xl border border-slate-200"
                />
              </div>
            </div>

            <RepMetricsTable repMetrics={analysis.rep_metrics} />
          </div>
        )}
      </div>
    </div>
  );
}

export { useAnalysisPolling };
export default ResultPage;
