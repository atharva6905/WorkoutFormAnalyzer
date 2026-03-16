function formatAngle(value) {
  if (value === null || value === undefined) {
    return '—';
  }

  return `${value.toFixed(1)}°`;
}

function formatConfidence(value) {
  if (value === null || value === undefined) {
    return '—';
  }

  return `${Math.round(value * 100)}%`;
}

function getDepthClass(value) {
  if (value === null || value === undefined) {
    return 'text-slate-500';
  }

  return value > 110 ? 'text-red-600' : 'text-slate-800';
}

function getConfidenceClass(value) {
  if (value === null || value === undefined) {
    return 'text-slate-500';
  }

  if (value > 0.8) {
    return 'text-emerald-600';
  }

  if (value >= 0.6) {
    return 'text-amber-600';
  }

  return 'text-red-600';
}

function RepMetricsTable({ repMetrics }) {
  if (!repMetrics.length) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white px-6 py-10 text-center shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Per-Rep Metrics</h2>
        <p className="mt-3 text-sm text-slate-500">No reps detected</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-lg font-semibold text-slate-900">Per-Rep Metrics</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-semibold">Rep #</th>
              <th className="px-4 py-3 font-semibold">Depth</th>
              <th className="px-4 py-3 font-semibold">Peak</th>
              <th className="px-4 py-3 font-semibold">Hip Min</th>
              <th className="px-4 py-3 font-semibold">Confidence</th>
              <th className="px-4 py-3 font-semibold">Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {repMetrics.map((repMetric, index) => (
              <tr key={repMetric.rep_index} className={index % 2 === 0 ? 'bg-white' : 'bg-slate-50/70'}>
                <td className="px-4 py-3 font-semibold text-slate-900">{repMetric.rep_index}</td>
                <td className={`px-4 py-3 font-medium ${getDepthClass(repMetric.min_knee_angle)}`}>
                  {formatAngle(repMetric.min_knee_angle)}
                </td>
                <td className="px-4 py-3 text-slate-800">{formatAngle(repMetric.max_knee_angle)}</td>
                <td className="px-4 py-3 text-slate-800">{formatAngle(repMetric.min_hip_angle)}</td>
                <td className={`px-4 py-3 font-medium ${getConfidenceClass(repMetric.confidence_score)}`}>
                  {formatConfidence(repMetric.confidence_score)}
                </td>
                <td className="px-4 py-3 text-slate-600">{repMetric.notes || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default RepMetricsTable;
