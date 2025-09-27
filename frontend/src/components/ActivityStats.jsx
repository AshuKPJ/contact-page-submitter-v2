// src/components/ActivityStats.jsx
import React, { useEffect, useState } from 'react';
import api from '../services/api';

const StatCard = ({ label, value, onClick }) => (
  <button
    onClick={onClick}
    className="flex-1 bg-white rounded-xl shadow p-4 text-left hover:shadow-md transition"
  >
    <div className="text-xs uppercase text-gray-500">{label}</div>
    <div className="text-2xl font-semibold">{value}</div>
  </button>
);

const ActivityStats = ({ scopeParams = {}, onQuickFilter }) => {
  const [data, setData] = useState({ by_source: {}, by_level: {} });
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get('/activity/stats', { params: scopeParams });
      setData(r.data || { by_source: {}, by_level: {} });
    } catch (e) {
      console.error('Stats fetch failed', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [JSON.stringify(scopeParams)]);

  const { by_source = {}, by_level = {} } = data;

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      <StatCard label="All System" value={by_source.system ?? 0} onClick={() => onQuickFilter({ source: 'system' })} />
      <StatCard label="All App" value={by_source.app ?? 0} onClick={() => onQuickFilter({ source: 'app' })} />
      <StatCard label="All Submissions" value={by_source.submission ?? 0} onClick={() => onQuickFilter({ source: 'submission' })} />
      <StatCard label="Warnings" value={by_level.WARN ?? 0} onClick={() => onQuickFilter({ source: 'app', level: 'WARN' })} />
      <StatCard label="Errors" value={by_level.ERROR ?? 0} onClick={() => onQuickFilter({ source: 'app', level: 'ERROR' })} />
    </div>
  );
};

export default ActivityStats;
