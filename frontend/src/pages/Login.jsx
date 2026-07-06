import { useSearchParams } from "react-router-dom";
import { loginUrl } from "../api";
import { GoogleIcon } from "../components/Icons";

const ERROR_MESSAGES = {
  access_denied: "Google sign-in was cancelled.",
  invalid_state: "Login session expired. Please try again.",
  token_exchange_failed: "Could not complete sign-in. Check Google credentials in .env.",
  userinfo_failed: "Could not load your Google profile.",
};

export default function Login() {
  const [params] = useSearchParams();
  const error = params.get("error");
  const message = error ? ERROR_MESSAGES[error] || `Login error: ${error}` : null;

  return (
    <div className="shell shell--center">
      <div className="card card--login">
        <div className="login-icon">🎙</div>
        <h1>Voice Agent</h1>
        <p className="subtitle">
          Sign in to talk with your AI assistant — book meetings, manage tasks, and check your day.
        </p>

        <a className="btn btn-google" href={loginUrl}>
          <GoogleIcon />
          Continue with Google
        </a>

        {message && <div className="error-banner">{message}</div>}

        <p className="hint">Secure sign-in via Google OAuth</p>
      </div>
    </div>
  );
}
