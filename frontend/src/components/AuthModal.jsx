import { useState } from "react";
import { login, register } from "../services/api";

export default function AuthModal({ onClose, onAuth }) {
  const [mode, setMode] = useState("login"); // login | register
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const data =
        mode === "login"
          ? await login(username, password)
          : await register(username, email, password);
      // Token is now set as httpOnly cookie by the server — no localStorage needed.
      localStorage.setItem("user", JSON.stringify({ id: data.user_id, username: data.username }));
      onAuth(data);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  function switchMode() {
    setMode(mode === "login" ? "register" : "login");
    setError(null);
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{mode === "login" ? "Login" : "Register"}</h2>
        <form onSubmit={handleSubmit}>
          <label>Username</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength={2}
            autoFocus
          />
          {mode === "register" && (
            <>
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </>
          )}
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
          {error && <div className="form-error">{error}</div>}
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? "Please wait..." : mode === "login" ? "Login" : "Register"}
          </button>
        </form>
        <p className="switch-mode" onClick={switchMode}>
          {mode === "login"
            ? "Don't have an account? Register"
            : "Already have an account? Login"}
        </p>
      </div>
    </div>
  );
}
