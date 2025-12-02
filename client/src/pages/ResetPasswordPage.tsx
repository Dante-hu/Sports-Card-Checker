// client/src/pages/ResetPasswordPage.tsx
import { useState, type FormEvent } from "react";
import { useLocation, Link, Location } from "react-router-dom";
import { resetPasswordWithAnswer } from "../api/auth";

interface ResetLocationState {
  email: string;
  securityQuestion: string;
}

export default function ResetPasswordPage() {
  const location = useLocation() as Location & {
    state?: ResetLocationState;
  };

  const email = location.state?.email ?? "";
  const securityQuestion = location.state?.securityQuestion ?? "";

  const [answer, setAnswer] = useState<string>("");
  const [newPassword, setNewPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // If user navigated here directly without state, show a simple message
  if (!email || !securityQuestion) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl w-full max-w-sm space-y-4">
          <h1 className="text-2xl font-semibold text-slate-50">
            Reset password
          </h1>
          <p className="text-sm text-slate-400">
            This page needs reset info from the &quot;Forgot password&quot;
            step.
          </p>
          <Link
            to="/forgot-password"
            className="inline-flex justify-center rounded-lg py-2 px-4 text-sm font-medium bg-emerald-500 text-slate-950 hover:bg-emerald-400"
          >
            Go to Forgot password
          </Link>
        </div>
      </div>
    );
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await resetPasswordWithAnswer(email, answer, newPassword);
      setSuccess("Password reset! You can now log in with your new password.");
    } catch (err: any) {
      const msg =
        err?.response?.data?.error ||
        err?.message ||
        "Could not reset password.";
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
          Reset password
        </h1>

        <p className="text-xs text-slate-400">
          Email:{" "}
          <span className="font-mono text-slate-200 break-all">{email}</span>
        </p>

        <div className="rounded-lg bg-slate-800/60 px-3 py-2">
          <p className="text-xs text-slate-400 mb-1">Security question</p>
          <p className="text-sm text-slate-100">{securityQuestion}</p>
        </div>

        {error && (
          <p className="text-sm text-red-400 bg-red-950/40 px-3 py-2 rounded-lg">
            {error}
          </p>
        )}

        {success && (
          <p className="text-sm text-emerald-300 bg-emerald-950/40 px-3 py-2 rounded-lg">
            {success}
          </p>
        )}

        <div className="space-y-1">
          <label className="text-sm text-slate-200">Your answer</label>
          <input
            className="w-full rounded-lg bg-slate-800 px-3 py-2 text-slate-50 text-sm"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            type="text"
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm text-slate-200">New password</label>
          <input
            className="w-full rounded-lg bg-slate-800 px-3 py-2 text-slate-50 text-sm"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            type="password"
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm text-slate-200">Confirm new password</label>
          <input
            className="w-full rounded-lg bg-slate-800 px-3 py-2 text-slate-50 text-sm"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            type="password"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg py-2 text-sm font-medium bg-emerald-500 disabled:bg-emerald-900 text-slate-950"
        >
          {loading ? "Resetting..." : "Reset password"}
        </button>

        <p className="text-xs text-slate-400 text-center">
          Done here?{" "}
          <Link className="text-emerald-400 hover:underline" to="/login">
            Back to login
          </Link>
        </p>
      </form>
    </div>
  );
}
