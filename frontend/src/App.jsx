import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { LayoutDashboard, Building2, Mail, FolderKanban, BarChart3 } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import Companies from "./pages/Companies";
import Communications from "./pages/Communications";
import Projects from "./pages/Projects";

const NAV = [
  { to: "/", label: "Дашборд", icon: LayoutDashboard },
  { to: "/companies", label: "Компании", icon: Building2 },
  { to: "/communications", label: "Письма", icon: Mail },
  { to: "/projects", label: "Проекты", icon: FolderKanban },
];

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50">
        <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
          <div className="p-5 border-b border-gray-100">
            <div className="font-bold text-gray-900 text-sm leading-tight">
              RH AI Agent
            </div>
            <div className="text-xs text-gray-400 mt-0.5">ПроКомпетенции</div>
          </div>
          <nav className="p-3 space-y-1 flex-1">
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive
                      ? "bg-blue-50 text-blue-700 font-medium"
                      : "text-gray-600 hover:bg-gray-100"
                  }`
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="p-4 border-t border-gray-100 text-xs text-gray-400">
            v1.0.0 — MVP
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="/communications" element={<Communications />} />
            <Route path="/projects" element={<Projects />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
