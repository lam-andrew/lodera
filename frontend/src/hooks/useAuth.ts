import { useCallback, useEffect, useState } from "react";

import { getCurrentUser, logout as logoutRequest, type User } from "@/api/client";

export type AuthState =
  { kind: "checking" } | { kind: "signedIn"; user: User } | { kind: "signedOut" };

/** Tracks who is signed in.
 *
 *  The session lives in an HTTP-only cookie the page cannot read, so the only way to know
 *  whether one is valid is to ask the server. That check runs once on load and again after
 *  any sign-in or sign-out. */
export function useAuth(): {
  state: AuthState;
  onSignedIn: (user: User) => void;
  signOut: () => Promise<void>;
} {
  const [state, setState] = useState<AuthState>({ kind: "checking" });

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const user = await getCurrentUser();
        if (active) setState(user === null ? { kind: "signedOut" } : { kind: "signedIn", user });
      } catch {
        // A backend that cannot be reached is treated as signed out rather than left
        // spinning, so the user gets the sign-in screen and a chance to retry.
        if (active) setState({ kind: "signedOut" });
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const onSignedIn = useCallback((user: User) => setState({ kind: "signedIn", user }), []);

  const signOut = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      setState({ kind: "signedOut" });
    }
  }, []);

  return { state, onSignedIn, signOut };
}
