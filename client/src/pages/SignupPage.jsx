// client/src/pages/SignupPage.jsx
import { useState } from "react";
import { signup } from "../api/auth";
import { useNavigate, Link } from "react-router-dom";

export default function SignupPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await signup(email, password);
      console.log("Signed up:", user);
      navigate("/cards");
    } catch (err) {
      setError(err.message || "Sign up failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
      <form
        onSubmit={handleSubmit}
        className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl w-full max-w-sm space-y-4"
      >
        <h1 className="text-2xl font-semibold text-slate-50">Sign up</h1>
        <p className="text-sm text-slate-400">
          Create an account to track your sets and progress.
        </p>

        {error && (
          <p className="text-sm text-red-400 bg-red-950/40 px-3 py-2 rounded-lg">
            {error}
          </p>
        )}

        <div className="space-y-1">
          <label className="text-sm text-slate-200">Email</label>
          <input
            className="w-full rounded-lg bg-slate-800 px-3 py-2 text-slate-50 text-sm"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm text-slate-200">Password</label>
          <input
            className="w-full rounded-lg bg-slate-800 px-3 py-2 text-slate-50 text-sm"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg py-2 text-sm font-medium bg-emerald-500 disabled:bg-emerald-900 text-slate-950"
        >
          {loading ? "Creating account..." : "Sign up"}
        </button>

        <p className="text-xs text-slate-400 text-center">
          Already have an account?{" "}
          <Link className="text-emerald-400 hover:underline" to="/login">
            Log in
          </Link>
        </p>
      </form>
    </div>
  );
}
