# 0014. Authentication: in-app sessions with Argon2id

- **Status:** Accepted
- **Date:** 2026-08-31

## Context

US-13 (FR-15) requires a user to authenticate before reaching their portfolio. Until now the
application has had a single implicit portfolio and no notion of a user, so this decision
introduces identity to the system.

Three families of solution were considered: build authentication into the application, adopt
a hosted identity provider (Clerk, Auth0, Supabase Auth), or run a self-hosted identity
server (Keycloak, Authentik, SuperTokens, Ory).

The shape of this product matters to the choice. Orbit is a solo capstone with essentially
one real user plus graders. It has no requirement for social login, SSO, SAML, MFA, or
organisation management — the features hosted and self-hosted identity platforms exist to
provide. It is graded on software-engineering rigor, and it is deliberately
provider-agnostic (see [ADR 0003](0003-docker-compose-provider-agnostic.md)).

## Decision

We will implement authentication **in the application**, using **server-side sessions
carried in an HTTP-only cookie**, with passwords hashed using **Argon2id**.

**Identity.** A user is identified by **email address** — stored lower-cased and unique.
There is no separate username: it would add a second uniqueness namespace to police while
providing nothing, and email is what any future password-reset flow needs regardless.

**Password storage.** Argon2id via `argon2-cffi`, at the parameters OWASP currently
recommends for interactive logins (time cost 3, memory 64 MiB, parallelism 1). OWASP's
Password Storage guidance now lists Argon2id ahead of scrypt and bcrypt; bcrypt at cost 12+
remains acceptable, so this is a choice for a new build rather than an urgent migration.
The salt and cost parameters are encoded inside the hash string, so there is deliberately
**no separate salt column** — a standalone `salt` column is a signature of a hand-rolled
scheme.

**Sessions.** On login the server generates a 256-bit random token and returns it in a
cookie marked `HttpOnly`, `SameSite=Lax`, and `Secure` outside development. Only a **SHA-256
hash of the token** is stored, so a database disclosure does not hand over live sessions.
Sessions carry an expiry and can be deleted, which makes logout and revocation real rather
than advisory.

**Scope for this story.** Registration, login, logout, and identifying the current user.
Email verification and password reset are deliberately excluded: both require outbound email,
which is a separate dependency and a separate decision. They are tracked as follow-up issues.

## Consequences

- **Positive:** No vendor dependency and no additional service, consistent with the
  provider-agnostic stance. The application continues to run entirely offline, which matters
  for a graded live demo — an outage at a hosted identity provider cannot prevent logging in.
- **Positive:** `HttpOnly` cookies are not readable from JavaScript, so a cross-site scripting
  bug cannot exfiltrate the session. This is the concrete advantage over the common pattern of
  storing a JWT in `localStorage`.
- **Positive:** Server-side sessions are revocable. A stateless JWT is valid until it expires
  regardless of logout, which makes real revocation awkward.
- **Positive:** The security-relevant work — modern hashing, cookie flags, constant-time
  comparison, session lifetime — is visible in the codebase rather than delegated.
- **Cost:** We own this code, including its correctness. Mitigated by using well-reviewed
  primitives (`argon2-cffi`, `secrets`) and never inventing cryptography.
- **Cost:** No social login, MFA, or SSO. None is in scope; adding any later would be a
  significant change and should supersede this ADR.
- **Cost:** Sessions require a database read per authenticated request. At this scale that is
  a single indexed lookup and not a concern.

## Alternatives Considered

- **Hosted identity (Clerk, Auth0, Supabase Auth):** generous free tiers and a polished
  sign-in experience for very little work. Rejected because it introduces a vendor and an
  internet dependency for logging in, conflicts with ADR 0003, and outsources precisely the
  part of this story that demonstrates engineering.
- **Self-hosted identity (Keycloak, Authentik, SuperTokens):** no vendor, and genuinely the
  right answer at organisational scale. Rejected as far too much operational surface — an
  additional service to run, upgrade and configure — for a single-user application.
- **JWT access tokens instead of sessions:** stateless and widely used. Rejected because the
  token must live somewhere in the browser (`localStorage` is readable by any injected
  script; a cookie recreates the session model without its revocability), and logout becomes
  a matter of the client agreeing to forget the token.
- **bcrypt instead of Argon2id:** still perfectly acceptable at cost 12+, and simpler. Argon2id
  was preferred because it is memory-hard — which is what resists GPU-accelerated cracking —
  and it is OWASP's first recommendation for new applications.
