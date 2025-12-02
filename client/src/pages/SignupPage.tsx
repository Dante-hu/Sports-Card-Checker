// client/src/pages/SignupPage.tsx
import { useState, type FormEvent } from "react";
import { signup } from "../api/auth";
import { useNavigate, Link } from "react-router-dom";

export default function SignupPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  // NEW: security question + answer
  const [securityQuestion, setSecurityQuestion] = useState<string>("");
  const [securityAnswer, setSecurityAnswer] = useState<string>("");

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // extended signup still works even if sec Q/A are empty strings
      const user = await signup(email, password, securityQuestion, securityAnswer);
      console.log("Signed up:", user);
      navigate("/cards");
    } catch (err: any) {
      // you can refine this if backend sends { error: "..." }
      setError(err?.response?.data?.error || err?.message || "Sign up failed");
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

        {/* NEW: security question + answer block */}
        <div className="pt-2 border-t border-slate-800 space-y-3">
          <p className="text-xs text-slate-400">
            Set a security question so you can reset your password later.
          </p>

          <div className="space-y-1">
            <label className="text-sm text-slate-200">Security Question</label>
            <input
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-slate-50 text-sm"
              value={securityQuestion}
              onChange={(e) => setSecurityQuestion(e.target.value)}
              type="text"
              placeholder="e.g. What is your favourite team?"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-slate-200">Security Answer</label>
            <input
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-slate-50 text-sm"
              value={securityAnswer}
              onChange={(e) => setSecurityAnswer(e.target.value)}
              type="text"
              placeholder="Answer to your question"
            />
          </div>
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
