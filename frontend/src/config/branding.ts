/**
 * Single source of truth for user-facing product naming.
 *
 * To rebrand the app's display name, either:
 *   - set `VITE_APP_NAME` in the environment (no code change), or
 *   - change the fallback string below.
 *
 * Everything the user sees (page title, header, etc.) reads from here, so the visible
 * name changes in exactly one place. Technical identifiers (package names, DB name,
 * container tags, repo name) are intentionally NOT wired to this
 * — those are a separate, mechanical rename (see docs/renaming.md if present). The
 * backend env prefix is intentionally brand-neutral (APP_), so env var names survive a
 * rename too.
 */
export const APP_NAME = import.meta.env.VITE_APP_NAME ?? "Orbit";

export const APP_TAGLINE =
  "Portfolio risk intelligence — measure, contextualize, and explain risk.";

/** Full document/tab title. */
export const APP_TITLE = `${APP_NAME} — Portfolio Risk Intelligence`;
