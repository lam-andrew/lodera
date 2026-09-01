import { useState, type FormEvent } from "react";

import { login, register, toErrorMessage, type User } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { APP_NAME, APP_TAGLINE } from "@/config/branding";

const MIN_PASSWORD_LENGTH = 12;

/** Sign in or create an account (US-13).
 *
 *  One screen with two modes rather than two routes: the fields are identical and the user
 *  is usually one click from realising they wanted the other one. */
export function SignInPage({ onSignedIn }: { onSignedIn: (user: User) => void }) {
  const [mode, setMode] = useState<"signIn" | "register">("signIn");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const registering = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = registering
        ? await register(email.trim(), password)
        : await login(email.trim(), password);
      onSignedIn(user);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const tooShort = registering && password.length > 0 && password.length < MIN_PASSWORD_LENGTH;
  const canSubmit = email.trim() !== "" && password !== "" && !tooShort && !busy;

  return (
    <div className="flex min-h-screen items-center justify-center px-5 py-12">
      <div className="flex w-full max-w-sm flex-col gap-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <span
            className="grid h-11 w-11 place-items-center rounded-xl text-white"
            style={{ background: "linear-gradient(150deg, var(--accent), #7c5cff)" }}
            aria-hidden="true"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              className="h-6 w-6"
            >
              <path d="M4 19V5M4 15l4-4 3 3 5-6 4 4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <h1 className="text-2xl font-semibold tracking-tight">{APP_NAME}</h1>
          <p className="text-sm text-muted-foreground">{APP_TAGLINE}</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{registering ? "Create your account" : "Sign in"}</CardTitle>
            <CardDescription>
              {registering
                ? "Your portfolio is private to your account."
                : "Sign in to see your portfolio and risk analysis."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  aria-invalid={error !== null}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete={registering ? "new-password" : "current-password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  aria-invalid={error !== null || tooShort}
                  aria-describedby={registering ? "password-hint" : undefined}
                />
                {registering && (
                  <p
                    id="password-hint"
                    className={`text-xs ${tooShort ? "text-down" : "text-faint"}`}
                  >
                    At least {MIN_PASSWORD_LENGTH} characters. Length matters more than symbols.
                  </p>
                )}
              </div>

              {error !== null && (
                <p role="alert" className="text-sm text-down">
                  {error}
                </p>
              )}

              <Button type="submit" disabled={!canSubmit}>
                {busy
                  ? registering
                    ? "Creating account…"
                    : "Signing in…"
                  : registering
                    ? "Create account"
                    : "Sign in"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-muted-foreground">
          {registering ? "Already have an account?" : "New to Orbit?"}{" "}
          <button
            type="button"
            className="text-accent underline-offset-4 hover:underline"
            onClick={() => {
              setMode(registering ? "signIn" : "register");
              setError(null);
            }}
          >
            {registering ? "Sign in" : "Create an account"}
          </button>
        </p>
      </div>
    </div>
  );
}
