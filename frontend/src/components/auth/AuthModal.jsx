import React, { useState } from "react";
import { X, Lock, Mail, User, Film, Loader2, Sparkles, AlertCircle, CheckCircle2 } from "lucide-react";
import { C } from "../../constants/theme";
import { loginUser, registerUser } from "../../api/client";

export default function AuthModal({ isOpen, onClose, onAuthSuccess, initialMode = "login" }) {
  const [mode, setMode] = useState(initialMode); // "login" | "register"
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!email || !password) {
      setError("Please fill in all required fields.");
      return;
    }

    if (mode === "register") {
      if (!username || username.length < 3) {
        setError("Username must be at least 3 characters.");
        return;
      }
      if (password.length < 10) {
        setError("Password must be at least 10 characters.");
        return;
      }
    }

    setLoading(true);
    try {
      let data;
      if (mode === "register") {
        data = await registerUser(email.trim(), username.trim(), password);
        setSuccessMsg("Account created! Welcome to CineSense.");
      } else {
        data = await loginUser(email.trim(), password);
        setSuccessMsg("Welcome back, cinephile!");
      }

      setTimeout(() => {
        if (onAuthSuccess) onAuthSuccess(data.user, data.access_token);
        onClose();
      }, 600);
    } catch (err) {
      setError(err.message || "Authentication failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
        background: "rgba(10, 6, 14, 0.82)",
        backdropFilter: "blur(12px)",
        animation: "fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
      }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 440,
          background: C.surface,
          borderRadius: 16,
          border: `1px solid ${C.border}`,
          boxShadow: "0 25px 60px -15px rgba(0, 0, 0, 0.7), 0 0 40px rgba(227, 163, 78, 0.08)",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* Film perforation top strip */}
        <div
          className="perf-strip"
          style={{
            height: 14,
            background: "#15101A",
            borderBottom: `1px solid ${C.border}`,
            opacity: 0.6,
          }}
        />

        {/* Modal Header */}
        <div
          style={{
            padding: "24px 28px 18px",
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            borderBottom: `1px solid ${C.border}`,
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <Film size={18} color={C.accent} />
              <span
                style={{
                  fontSize: "0.75rem",
                  letterSpacing: "0.15em",
                  textTransform: "uppercase",
                  color: C.accent,
                  fontWeight: 600,
                  fontFamily: "var(--font-display, inherit)",
                }}
              >
                CineSense Cloud Pass
              </span>
            </div>
            <h2
              style={{
                margin: 0,
                fontSize: "1.75rem",
                color: C.text,
                fontFamily: "var(--font-display, inherit)",
                fontWeight: 700,
                letterSpacing: "-0.01em",
              }}
            >
              {mode === "login" ? "Sign In to Your Lounge" : "Claim Your Seat"}
            </h2>
            <p style={{ margin: "4px 0 0", fontSize: "0.85rem", color: C.muted }}>
              {mode === "login"
                ? "Sync your personalized ratings, watchlist, and AI taste profile."
                : "Create a cinema profile with cloud-synced recommendations."}
            </p>
          </div>

          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: `1px solid ${C.border}`,
              borderRadius: "50%",
              width: 32,
              height: 32,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              color: C.muted,
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = C.text)}
            onMouseLeave={(e) => (e.currentTarget.style.color = C.muted)}
          >
            <X size={16} />
          </button>
        </div>

        {/* Tab Toggle */}
        <div
          style={{
            display: "flex",
            borderBottom: `1px solid ${C.border}`,
            background: "#18131C",
          }}
        >
          <button
            type="button"
            onClick={() => {
              setMode("login");
              setError(null);
            }}
            style={{
              flex: 1,
              padding: "12px 0",
              background: mode === "login" ? C.surface : "transparent",
              border: "none",
              borderBottom: mode === "login" ? `2px solid ${C.accent}` : "2px solid transparent",
              color: mode === "login" ? C.accent : C.muted,
              fontWeight: 600,
              fontSize: "0.85rem",
              letterSpacing: "0.05em",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            style={{
              flex: 1,
              padding: "12px 0",
              background: mode === "register" ? C.surface : "transparent",
              border: "none",
              borderBottom: mode === "register" ? `2px solid ${C.accent}` : "2px solid transparent",
              color: mode === "register" ? C.accent : C.muted,
              fontWeight: 600,
              fontSize: "0.85rem",
              letterSpacing: "0.05em",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            Register
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: "24px 28px 28px" }}>
          {error && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 14px",
                background: "rgba(220, 53, 69, 0.12)",
                border: "1px solid rgba(220, 53, 69, 0.35)",
                borderRadius: 8,
                color: "#ff8282",
                fontSize: "0.82rem",
                marginBottom: 18,
              }}
            >
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 14px",
                background: "rgba(79, 124, 116, 0.15)",
                border: "1px solid rgba(79, 124, 116, 0.4)",
                borderRadius: 8,
                color: "#77d8c6",
                fontSize: "0.82rem",
                marginBottom: 18,
              }}
            >
              <CheckCircle2 size={16} style={{ flexShrink: 0 }} />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Email input */}
          <div style={{ marginBottom: 16 }}>
            <label
              style={{
                display: "block",
                fontSize: "0.75rem",
                fontWeight: 600,
                color: C.muted,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: 6,
              }}
            >
              Email Address
            </label>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 14px",
                background: "#16111A",
                border: `1px solid ${C.border}`,
                borderRadius: 8,
                transition: "border 0.2s",
              }}
            >
              <Mail size={16} color={C.muted} />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@cinema.com"
                style={{
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: C.text,
                  width: "100%",
                  fontSize: "0.9rem",
                }}
              />
            </div>
          </div>

          {/* Username input (register only) */}
          {mode === "register" && (
            <div style={{ marginBottom: 16 }}>
              <label
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  color: C.muted,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  marginBottom: 6,
                }}
              >
                Username
              </label>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "10px 14px",
                  background: "#16111A",
                  border: `1px solid ${C.border}`,
                  borderRadius: 8,
                }}
              >
                <User size={16} color={C.muted} />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="cinephile_007"
                  style={{
                    background: "transparent",
                    border: "none",
                    outline: "none",
                    color: C.text,
                    width: "100%",
                    fontSize: "0.9rem",
                  }}
                />
              </div>
            </div>
          )}

          {/* Password input */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <label
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  color: C.muted,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                }}
              >
                Password
              </label>
              {mode === "register" && (
                <span style={{ fontSize: "0.72rem", color: C.muted }}>min. 10 chars</span>
              )}
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 14px",
                background: "#16111A",
                border: `1px solid ${C.border}`,
                borderRadius: 8,
              }}
            >
              <Lock size={16} color={C.muted} />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                style={{
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: C.text,
                  width: "100%",
                  fontSize: "0.9rem",
                }}
              />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px 16px",
              background: `linear-gradient(135deg, ${C.accent} 0%, #C48735 100%)`,
              color: "#16111A",
              border: "none",
              borderRadius: 8,
              fontSize: "0.95rem",
              fontWeight: 700,
              letterSpacing: "0.05em",
              cursor: loading ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              boxShadow: "0 4px 15px rgba(227, 163, 78, 0.25)",
              transition: "transform 0.15s, filter 0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.filter = "brightness(1.08)")}
            onMouseLeave={(e) => (e.currentTarget.style.filter = "none")}
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                <span>Authorizing...</span>
              </>
            ) : mode === "login" ? (
              <>
                <span>Sign In</span>
                <Sparkles size={16} />
              </>
            ) : (
              <>
                <span>Create Cloud Account</span>
                <Film size={16} />
              </>
            )}
          </button>

          {/* Guest notice */}
          <p
            style={{
              margin: "18px 0 0",
              fontSize: "0.75rem",
              color: C.muted,
              textAlign: "center",
              lineHeight: 1.4,
            }}
          >
            All your local guest likes will automatically merge into your cloud account upon signing in.
          </p>
        </form>
      </div>
    </div>
  );
}
