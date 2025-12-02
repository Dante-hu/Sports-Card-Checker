// client/src/pages/ForgotPasswordPage.tsx
import { useState, type FormEvent } from "react";
import { forgotPasswordGetQuestion } from "../api/auth";
import { useNavigate, Link } from "react-router-dom";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState<string>("");

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await forgotPasswordGetQuestion(email);
      console.log("forgot-password response:", data);

      navigate("/reset-password", {
        state: {
          email: data.email,
          securityQuestion: data.security_question,
        },
      });
    } catch (err: any) {
      const msg =
        err?.response?.data?.error ||
        "Could not find that account or security question.";
      setError(msg);
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
        <h1 className="text-2xl font-semibold text-slate-50">
          Forgot password
        </h1>
        <p className="text-sm text-slate-400">
          Enter your account email. We&apos;ll show your security question so
          you can reset your password.
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

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg py-2 text-sm font-medium bg-emerald-500 disabled:bg-emerald-900 text-slate-950"
        >
          {loading ? "Checking..." : "Next"}
        </button>

        <p className="text-xs text-slate-400 text-center">
          Remembered it?{" "}
          <Link className="text-emerald-400 hover:underline" to="/login">
            Back to login
          </Link>
        </p>
      </form>
    </div>
  );
}
