import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { logout } from "../api/auth";

export default function AppLayout() {
  const navigate = useNavigate();

  async function handleLogout() {
    try {
      await logout();
    } catch (err) {
      console.error("Logout failed:", err);
    } finally {
      navigate("/login");
    }
  }

  const linkBaseClasses =
    "px-3 py-2 text-sm rounded-xl transition-colors";
  const inactiveClasses =
    "text-slate-300 hover:text-white hover:bg-slate-800";
  const activeClasses =
    "text-emerald-300 bg-slate-900 border border-emerald-500/40";

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      {/* Navbar */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
          {/* Left: logo/title */}
          <div
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => navigate("/cards")}
          >
            <div className="w-8 h-8 rounded-xl bg-emerald-500 flex items-center justify-center text-slate-950 text-xs font-bold">
              SC
            </div>
            <span className="font-semibold text-sm sm:text-base">
              Sports Card Checker
            </span>
          </div>

          {/* Middle: nav links */}
          <nav className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm">
            <NavLink
              to="/cards"
              className={({ isActive }) =>
                `${linkBaseClasses} ${
                  isActive ? activeClasses : inactiveClasses
                }`
              }
            >
              Cards
            </NavLink>

            {/* These two will be useful once you build the pages */}
            <NavLink
              to="/owned"
              className={({ isActive }) =>
                `${linkBaseClasses} ${
                  isActive ? activeClasses : inactiveClasses
                }`
              }
            >
              Owned
            </NavLink>

            <NavLink
              to="/wantlist"
              className={({ isActive }) =>
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
            className="text-xs sm:text-sm px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-emerald-400 hover:text-emerald-300"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Page content */}
      <main className="max-w-6xl mx-auto px-4 py-4">
        <Outlet />
      </main>
    </div>
  );
}
