import { useEffect, useState } from "react";
import { Mail, Send, CheckCircle, XCircle, Clock } from "lucide-react";
import { communications } from "../api/client";

const STATUS_LABELS = {
  draft: { label: "Черновик", color: "bg-gray-100 text-gray-600" },
  approved: { label: "Утверждено", color: "bg-blue-100 text-blue-700" },
  sent: { label: "Отправлено", color: "bg-yellow-100 text-yellow-700" },
  delivered: { label: "Доставлено", color: "bg-green-100 text-green-700" },
  read: { label: "Прочитано", color: "bg-green-200 text-green-800" },
  replied: { label: "Ответили", color: "bg-purple-100 text-purple-700" },
  bounced: { label: "Не доставлено", color: "bg-red-100 text-red-600" },
  rejected: { label: "Отказ", color: "bg-red-100 text-red-700" },
};

export default function Communications() {
  const [list, setList] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      communications.list({ limit: 50 }),
      communications.getStats(),
    ]).then(([listRes, statsRes]) => {
      setList(listRes.data || []);
      setStats(statsRes.data);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const sendComm = async (id) => {
    await communications.send(id);
    const r = await communications.list({ limit: 50 });
    setList(r.data || []);
  };

  if (loading) return <div className="p-6 text-gray-400">Загрузка...</div>;

  return (
    <div className="p-6 space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Коммуникации</h1>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: "Отправлено", value: stats.total_sent },
            { label: "Прочитано", value: stats.read },
            { label: "Ответили", value: stats.replied },
            { label: "Заинтересованы", value: stats.interested },
            { label: "Отклик", value: `${(stats.response_rate * 100).toFixed(1)}%` },
          ].map(s => (
            <div key={s.label} className="bg-white border border-gray-200 rounded-xl p-3 text-center">
              <div className="text-xl font-bold text-gray-800">{s.value}</div>
              <div className="text-xs text-gray-500 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-3">
        {list.map(comm => {
          const s = STATUS_LABELS[comm.status] || { label: comm.status, color: "bg-gray-100 text-gray-600" };
          return (
            <div key={comm.id} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Mail size={14} className="text-gray-400" />
                    <span className="font-medium text-gray-800 truncate">
                      {comm.subject || "Без темы"}
                    </span>
                    {comm.is_followup && (
                      <span className="text-xs bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded">
                        Follow-up #{comm.followup_number}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500">
                    Компания ID: {comm.company_id}
                    {comm.sent_at && ` • Отправлено: ${new Date(comm.sent_at).toLocaleDateString("ru")}`}
                    {comm.replied_at && ` • Ответ: ${new Date(comm.replied_at).toLocaleDateString("ru")}`}
                  </div>
                  {comm.value_proposition && (
                    <div className="text-xs text-blue-600 mt-1 italic">"{comm.value_proposition}"</div>
                  )}
                  {comm.reply_content && (
                    <div className="mt-2 text-xs bg-green-50 border border-green-200 rounded p-2 text-gray-700">
                      <strong>Ответ:</strong> {comm.reply_content.slice(0, 150)}...
                    </div>
                  )}
                </div>
                <div className="flex flex-col items-end gap-2 shrink-0">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${s.color}`}>{s.label}</span>
                  {comm.status === "approved" && (
                    <button
                      onClick={() => sendComm(comm.id)}
                      className="flex items-center gap-1 text-xs bg-blue-600 text-white px-2 py-1 rounded-lg hover:bg-blue-700"
                    >
                      <Send size={11} /> Отправить
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
        {list.length === 0 && (
          <div className="text-center text-gray-400 py-12">
            Нет коммуникаций. Сгенерируйте письма для компаний из шорт-листа.
          </div>
        )}
      </div>
    </div>
  );
}
