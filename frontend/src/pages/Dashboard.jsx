import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Building2, Mail, FolderKanban, TrendingUp, Users, CheckCircle } from "lucide-react";
import StatCard from "../components/StatCard";
import PhaseCard from "../components/PhaseCard";
import { dashboard } from "../api/client";

const KPI_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#6366f1"];

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboard.getSummary()
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-gray-400">Загрузка...</div>
  );
  if (!data) return (
    <div className="text-red-500 p-4">Не удалось загрузить данные. Проверьте, запущен ли бэкенд.</div>
  );

  const phases = data.phases || [];
  const kpis = Object.values(data.kpis || {});

  const phase2 = phases.find(p => p.phase === 2) || {};
  const phase4 = phases.find(p => p.phase === 4) || {};
  const phase5 = phases.find(p => p.phase === 5) || {};

  const kpiChartData = kpis.map(k => ({
    name: k.name.split(" ").slice(0, 2).join(" "),
    current: k.current,
    target: k.target,
  }));

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Дашборд</h1>
        <p className="text-gray-500 text-sm mt-1">RH AI Agent — прогресс по фазам</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Компаний найдено"
          value={phase2?.metrics?.companies_found ?? 0}
          subtitle={`Шорт-лист: ${phase2?.metrics?.shortlisted ?? 0}`}
          color="blue"
          icon={Building2}
        />
        <StatCard
          title="Писем отправлено"
          value={phase4?.metrics?.sent ?? 0}
          subtitle={`Ответов: ${phase4?.metrics?.replied ?? 0}`}
          color="purple"
          icon={Mail}
        />
        <StatCard
          title="Заинтересованы"
          value={phase4?.metrics?.interested ?? 0}
          subtitle={`Отклик: ${((phase4?.metrics?.response_rate ?? 0) * 100).toFixed(1)}%`}
          color="green"
          icon={TrendingUp}
        />
        <StatCard
          title="Проектов"
          value={phase5?.metrics?.total_projects ?? 0}
          subtitle={`Активных: ${phase5?.metrics?.active_projects ?? 0}`}
          color="yellow"
          icon={FolderKanban}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">KPI прогресс</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={kpiChartData} layout="vertical">
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="current" fill="#3b82f6" name="Текущее" radius={[0, 4, 4, 0]} />
              <Bar dataKey="target" fill="#e5e7eb" name="Цель" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">KPI статусы</h2>
          <div className="space-y-3">
            {kpis.map((kpi, i) => (
              <div key={i} className="flex items-center gap-3">
                <CheckCircle
                  size={18}
                  className={kpi.done ? "text-green-500" : "text-gray-300"}
                />
                <div className="flex-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-700">{kpi.name}</span>
                    <span className="font-medium">{kpi.current} / {kpi.target}</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-1.5 mt-1">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full transition-all"
                      style={{ width: `${Math.min((kpi.current / kpi.target) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div>
        <h2 className="font-semibold text-gray-800 mb-3">Фазы проекта</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {phases.map(phase => (
            <PhaseCard key={phase.phase} phase={phase} />
          ))}
        </div>
      </div>
    </div>
  );
}
