import { Navigate, Route, Routes } from "react-router-dom";
import Assistant from "./pages/Assistant";
import Login from "./pages/Login";
import { useAuth } from "./useAuth";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="loader-page">
        <div className="loader" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function LoginRoute() {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="loader-page">
        <div className="loader" />
      </div>
    );
  }
  if (user) return <Navigate to="/assistant" replace />;
  return <Login />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />
      <Route
        path="/assistant"
        element={
          <ProtectedRoute>
            <Assistant />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/assistant" replace />} />
    </Routes>
  );
}
