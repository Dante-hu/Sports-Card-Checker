import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import CardsPage from "./pages/CardsPage";
import OwnedPage from "./pages/OwnedPage";
import WantlistPage from "./pages/WantlistPage";
import AppLayout from "./components/AppLayout";
import SetsPage from "./pages/SetsPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Protected-ish routes with navbar */}
        <Route element={<AppLayout />}>
          <Route path="/cards" element={<CardsPage />} />
          <Route path="/owned" element={<OwnedPage />} />
          <Route path="/sets" element={<SetsPage />} />
          <Route path="/wantlist" element={<WantlistPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
