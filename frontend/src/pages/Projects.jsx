import { useEffect, useState } from "react";
import { FolderKanban, Users, Clock, ChevronDown } from "lucide-react";
import { projects } from "../api/client";

const DIFFICULTY_LABELS = {
  beginner: { label: "Начальный", color: "text-green-600 bg-green-50" },
  intermediate: { label: "Средний", color: "text-yellow-600 bg-yellow-50" },
  advanced: { label: "Продвинутый", color: "text-red-600 bg-red-50" },
};

const STATUS_LABELS = {
  draft: "Черновик",
  active: "Активен",
  matching: "Подбор",
  in_progress: "В работе",
  completed: "Завершён",
  cancelled: "Отменён",
};

export default function Projects() {
  const [catalog, setCatalog] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    projects.catalog()
      .then(r => setCatalog(r.data || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 text-gray-400">Загрузка...</div>;

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Каталог проектов</h1>
          <p className="text-sm text-gray-500 mt-1">{catalog.length} проектов</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {catalog.map(project => {
          const diff = DIFFICULTY_LABELS[project.difficulty] || { label: project.difficulty, color: "text-gray-600 bg-gray-50" };
          return (
            <div key={project.id} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${diff.color}`}>
                  {diff.label}
                </span>
                <span className="text-xs text-gray-400">{STATUS_LABELS[project.status] || project.status}</span>
              </div>
              <h3 className="font-semibold text-gray-800 mb-1 leading-snug">{project.title}</h3>
              <p className="text-xs text-gray-500 mb-3">{project.company_name}</p>

              <div className="flex gap-4 text-xs text-gray-500 mb-3">
                {project.duration_weeks && (
                  <span className="flex items-center gap-1">
                    <Clock size={11} /> {project.duration_weeks} нед.
                  </span>
                )}
                {project.max_students && (
                  <span className="flex items-center gap-1">
                    <Users size={11} /> до {project.max_students} ст.
                  </span>
                )}
                {project.roles_count > 0 && (
                  <span className="flex items-center gap-1">
                    <FolderKanban size={11} /> {project.roles_count} ролей
                  </span>
                )}
              </div>

              {project.competencies?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {project.competencies.slice(0, 4).map(c => (
                    <span key={c} className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{c}</span>
                  ))}
                  {project.competencies.length > 4 && (
                    <span className="text-xs text-gray-400">+{project.competencies.length - 4}</span>
                  )}
                </div>
              )}

              <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between text-xs text-gray-400">
                <span>{project.enrolled_students} / {project.max_students || "?"} зачислено</span>
              </div>
            </div>
          );
        })}
        {catalog.length === 0 && (
          <div className="col-span-3 text-center text-gray-400 py-16">
            Каталог пуст. Заключите партнёрские соглашения и сгенерируйте ТЗ.
          </div>
        )}
      </div>
    </div>
  );
}
