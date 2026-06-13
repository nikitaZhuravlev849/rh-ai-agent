export default function PhaseCard({ phase }) {
  const statusColors = {
    pending: "bg-gray-100 text-gray-500",
    active: "bg-green-100 text-green-700",
    completed: "bg-blue-100 text-blue-700",
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Фаза {phase.phase}
          </span>
          <h3 className="font-semibold text-gray-800 mt-0.5">{phase.name}</h3>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColors[phase.status]}`}>
          {phase.status === "active" ? "Активна" : phase.status === "completed" ? "Завершена" : "Ожидание"}
        </span>
      </div>
      <div className="space-y-1">
        {Object.entries(phase.metrics || {}).map(([key, val]) => (
          <div key={key} className="flex justify-between text-sm">
            <span className="text-gray-500">{key.replace(/_/g, " ")}</span>
            <span className="font-medium text-gray-800">{val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
