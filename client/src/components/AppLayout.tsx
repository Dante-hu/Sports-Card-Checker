import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { logout } from "../api/auth";

export default function AppLayout() {
  const navigate = useNavigate();

  async function handleLogout(): Promise<void> {
    try {
      await logout();
    } catch (err) {
      console.error("Logout failed:", err);
    } finally {
      navigate("/login");
    }
  }

  // same idea, just slightly nicer styling
  const linkBaseClasses =
    "px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-200";
  const inactiveClasses =
    "text-slate-300 hover:text-emerald-300 hover:bg-slate-800/70";
  const activeClasses =
    "text-emerald-300 bg-slate-900 border-b-2 border-emerald-400";

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 to-slate-900 text-slate-50">
      {/* Navbar */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur shadow-sm">
        <div className="max-w-6xl mx-auto px-5 h-16 flex items-center justify-between gap-4">
          {/* Left: logo/title */}
          <div
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => navigate("/cards")}
          >
            <div className="w-9 h-9 rounded-xl bg-emerald-500 flex items-center justify-center text-slate-950 text-sm font-bold shadow-sm transition-transform group-hover:scale-105">
              SC
            </div>
            <span className="font-semibold text-base tracking-tight">
              <span className="text-emerald-400">Sports</span> Card Checker
            </span>
          </div>

          {/* Middle: nav links */}
          <nav className="flex items-center gap-2 text-sm">
            <NavLink
              to="/cards"
              className={({ isActive }: { isActive: boolean }) =>
                `${linkBaseClasses} ${
                  isActive ? activeClasses : inactiveClasses
                }`
              }
            >
              Cards
            </NavLink>

            <NavLink
              to="/owned"
              className={({ isActive }: { isActive: boolean }) =>
                `${linkBaseClasses} ${
                  isActive ? activeClasses : inactiveClasses
                }`
              }
            >
              Owned
            </NavLink>

            <NavLink
              to="/wantlist"
              className={({ isActive }: { isActive: boolean }) =>
                `${linkBaseClasses} ${
                  isActive ? activeClasses : inactiveClasses
                }`
              }
            >
              Wantlist
            </NavLink>
          </nav>

          {/* Right: logout */}
          <button
            onClick={handleLogout}
            className="text-sm px-4 py-2 rounded-xl bg-slate-900 border border-slate-700 hover:border-emerald-400 hover:text-emerald-300 hover:bg-slate-800/80 shadow-sm transition-colors duration-200"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Page content */}
      <main className="max-w-6xl mx-auto px-5 py-5">
        <Outlet />
      </main>
    </div>
  );
}
