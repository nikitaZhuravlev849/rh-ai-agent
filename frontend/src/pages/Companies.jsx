import { useEffect, useState } from "react";
import { Building2, Star, MapPin, Globe, CheckCircle } from "lucide-react";
import { companies } from "../api/client";

export default function Companies() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [shortlistOnly, setShortlistOnly] = useState(false);
  const [selected, setSelected] = useState([]);

  const load = () => {
    setLoading(true);
    companies.list({ page, per_page: 20, shortlisted_only: shortlistOnly })
      .then(r => {
        setList(r.data.companies || []);
        setTotal(r.data.total || 0);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [page, shortlistOnly]);

  const handleShortlist = async (ids) => {
    await companies.verify({ company_ids: ids, action: "shortlist" });
    load();
    setSelected([]);
  };

  const toggle = (id) =>
    setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Компании</h1>
          <p className="text-sm text-gray-500 mt-1">Всего: {total}</p>
        </div>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={shortlistOnly}
              onChange={e => setShortlistOnly(e.target.checked)}
              className="rounded"
            />
            Только шорт-лист
          </label>
          {selected.length > 0 && (
            <button
              onClick={() => handleShortlist(selected)}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
            >
              Шорт-лист ({selected.length})
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="text-gray-400 text-center py-12">Загрузка...</div>
      ) : (
        <div className="space-y-3">
          {list.map(company => (
            <div
              key={company.id}
              className={`bg-white border rounded-xl p-4 shadow-sm transition-colors ${
                selected.includes(company.id) ? "border-blue-400 bg-blue-50" : "border-gray-200"
              }`}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={selected.includes(company.id)}
                  onChange={() => toggle(company.id)}
                  className="mt-1 rounded"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Building2 size={16} className="text-gray-400 shrink-0" />
                    <span className="font-semibold text-gray-800 truncate">{company.name}</span>
                    {company.is_shortlisted && (
                      <CheckCircle size={14} className="text-green-500 shrink-0" />
                    )}
                  </div>
                  <div className="flex flex-wrap gap-3 mt-1 text-xs text-gray-500">
                    {company.industry && <span>{company.industry}</span>}
                    {company.region && (
                      <span className="flex items-center gap-1">
                        <MapPin size={11} /> {company.region}
                      </span>
                    )}
                    {company.website && (
                      <a href={company.website} target="_blank" rel="noreferrer"
                        className="flex items-center gap-1 text-blue-500 hover:underline">
                        <Globe size={11} /> сайт
                      </a>
                    )}
                  </div>
                  {company.tech_stack?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {company.tech_stack.slice(0, 6).map(t => (
                        <span key={t} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{t}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <div className="flex items-center gap-1 text-yellow-500">
                    <Star size={14} fill="currentColor" />
                    <span className="font-bold text-gray-800">{company.score?.toFixed(1)}</span>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">{company.source}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-between items-center">
        <button
          disabled={page === 1}
          onClick={() => setPage(p => p - 1)}
          className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40"
        >
          ← Назад
        </button>
        <span className="text-sm text-gray-500">Стр. {page}</span>
        <button
          disabled={list.length < 20}
          onClick={() => setPage(p => p + 1)}
          className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40"
        >
          Вперёд →
        </button>
      </div>
    </div>
  );
}
