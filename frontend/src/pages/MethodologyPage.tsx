import { useEffect } from "react";
import { useLocation } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import {
  Caveat,
  Formula,
  Prose,
  Section,
  TradeOff,
  YourFigure,
} from "@/features/methodology/prose";
import type { PortfolioData } from "@/hooks/usePortfolio";

function pct(value: string | null | undefined): string | null {
  if (value === null || value === undefined) return null;
  const n = Number(value);
  return Number.isNaN(n) ? null : `${n.toFixed(1)}%`;
}

const CONTENTS = [
  ["prices", "The price series"],
  ["returns", "From prices to returns"],
  ["volatility", "Volatility of one holding"],
  ["portfolio-volatility", "Volatility of the whole portfolio"],
  ["correlation", "Correlation between holdings"],
  ["concentration", "Concentration and overlap"],
  ["drawdown", "Drawdown"],
  ["limitations", "What to scrutinize"],
] as const;

/** How the risk figures are calculated (US-19).
 *
 *  Written for a reader deciding whether to trust the numbers, so every metric states its
 *  formula, the judgement behind it, and what it does not model. Where the reader has a
 *  portfolio, their own figures are used as the worked examples. */
export function MethodologyPage({ data }: { data: PortfolioData }) {
  const { risk, correlation, concentration, drawdown } = data;
  const { hash } = useLocation();

  // React Router does not scroll to hash targets itself, and on a client-side navigation
  // the target section is laid out a beat after this effect first runs. Poll briefly for
  // the element instead of assuming it is there, and jump instantly rather than smoothly —
  // arriving from another page can mean scrolling tens of thousands of pixels, which is
  // slow to animate and disorienting.
  useEffect(() => {
    if (hash === "") return;
    const id = hash.slice(1);

    let attempts = 0;
    let timer = 0;
    const tryScroll = () => {
      const target = document.getElementById(id);
      if (target !== null && target.getBoundingClientRect().height > 0) {
        target.scrollIntoView({ behavior: "auto", block: "start" });
        return;
      }
      if (attempts < 10) {
        attempts += 1;
        timer = window.setTimeout(tryScroll, 50);
      }
    };
    timer = window.setTimeout(tryScroll, 0);

    return () => window.clearTimeout(timer);
  }, [hash]);

  const portfolioVol = pct(risk?.portfolio_volatility_pct);
  const undiversified = pct(risk?.undiversified_volatility_pct);
  const benefit = pct(risk?.diversification_benefit_pct);
  const effective = concentration?.effective_holdings ?? null;
  const holdingsCount = concentration?.holdings_count ?? 0;
  const topPair = correlation?.most_correlated[0];
  const maxDd = pct(drawdown?.max_drawdown_pct);
  const observations = risk?.observations ?? 0;

  return (
    <div className="flex flex-col gap-8 pb-8">
      <Card>
        <CardContent className="flex flex-col gap-4 p-6">
          <Prose>
            <p>
              Every risk figure in Orbit comes from one pipeline: adjusted closing prices become
              daily returns, and those returns become volatility, correlation, concentration and
              drawdown. This page explains each step, the judgement behind it, and — at the end —
              what the analysis does not model.
            </p>
            <p className="text-foreground">
              Nothing here is a forecast or a recommendation. Every number describes what has
              already happened over a measured window.
            </p>
          </Prose>
          <nav
            aria-label="Contents"
            className="flex flex-wrap gap-x-4 gap-y-1.5 border-t border-border pt-4"
          >
            {CONTENTS.map(([id, label], i) => (
              <a
                key={id}
                href={`#${id}`}
                className="font-mono text-xs text-muted-foreground underline-offset-4 hover:text-accent hover:underline"
              >
                <span className="text-faint">{String(i + 1).padStart(2, "0")}</span> {label}
              </a>
            ))}
          </nav>
        </CardContent>
      </Card>

      <Section id="prices" index="01" title="The price series">
        <Prose>
          <p>
            Everything starts from one number per holding per day: the{" "}
            <strong className="text-foreground">adjusted close</strong> — the closing price
            corrected for stock splits and dividend payments.
          </p>
          <p>
            This is not cosmetic. If a stock does a 4-for-1 split, its raw closing price drops about
            75% overnight while shareholders lose nothing. Feed raw closes into the math and that
            appears as a −75% daily return: one fabricated event that would dominate a whole year of
            volatility.
          </p>
        </Prose>
        <TradeOff
          chosenLabel="adjusted close"
          chosen="Corporate actions are already accounted for, so a return reflects only market movement."
          rejectedLabel="raw close"
          rejected="Splits and dividends register as enormous fake price moves and inflate every figure downstream."
        />
      </Section>

      <Section id="returns" index="02" title="From prices to returns">
        <Prose>
          <p>
            Risk is about movement, not price level — a $700 ETF is not riskier than a $16 stock
            because its number is bigger. So prices become proportional daily changes, which are
            comparable across holdings.
          </p>
        </Prose>
        <Formula
          lines={["r(t) = P(t) / P(t−1) − 1"]}
          where={
            <>
              <span>
                <strong className="font-mono text-foreground">P(t)</strong> — adjusted close on day
                t
              </span>
              <span>
                <strong className="font-mono text-foreground">r(t)</strong> — that day&apos;s return
                (0.0165 = +1.65%)
              </span>
            </>
          }
        />
        <Prose>
          <p>
            Note that <em>n</em> prices give <em>n−1</em> returns
            {observations > 0 && (
              <>
                {" "}
                — your figures are built on{" "}
                <YourFigure label="observations" value={String(observations)} /> daily returns
              </>
            )}
            .
          </p>
        </Prose>
        <TradeOff
          chosenLabel="simple returns"
          chosen={
            <>
              A portfolio&apos;s return is <em>exactly</em> the weighted sum of its holdings&apos;
              returns. That identity is what makes the portfolio covariance math valid.
            </>
          }
          rejectedLabel="log returns"
          rejected={
            <>
              Neatly additive across <em>time</em> and common in academic work, but only
              approximately additive across <em>holdings</em> — the direction that matters here.
            </>
          }
        />
      </Section>

      <Section id="volatility" index="03" title="Volatility of one holding">
        <Prose>
          <p>
            Volatility is the annualized standard deviation of daily returns — how far returns
            typically land from their own average.
          </p>
        </Prose>
        <Formula
          lines={["σ_daily = √( Σ (r(i) − r̄)² / (n − 1) )", "σ_annual = σ_daily × √252"]}
          where={
            <>
              <span>
                <strong className="font-mono text-foreground">n − 1</strong> — sample correction,
                because we hold a sample of history rather than all of it
              </span>
              <span>
                <strong className="font-mono text-foreground">252</strong> — conventional US trading
                days per year
              </span>
            </>
          }
        />
        <Prose>
          <p>
            The square root matters. <em>Variance</em> scales linearly with time, and volatility is
            the square root of variance — so 25 days of returns have 25× the variance but only √25 =
            5× the standard deviation. A holding with a 1% daily standard deviation is reported at
            roughly 15.9% annualized. Multiplying by 252 instead would overstate risk about
            sixteenfold.
          </p>
        </Prose>
        <Caveat>
          <strong className="text-foreground">The assumption.</strong> √252 scaling assumes daily
          returns are independent of each other. Real markets show volatility clustering — turbulent
          days follow turbulent days — so a single annualized number understates how bad a bad
          stretch gets. It is the standard convention, not a guarantee.
        </Caveat>
      </Section>

      <Section id="portfolio-volatility" index="04" title="Volatility of the whole portfolio">
        <Prose>
          <p>
            The obvious approach — weight each holding&apos;s volatility by position size and
            average them — is wrong, and systematically so. It assumes every holding moves in
            lockstep. When one falls on a day another rises, the moves partially cancel and the
            portfolio swings less than its parts. A weighted average cannot see that.
          </p>
        </Prose>
        <Formula
          lines={["σₚ = √( wᵀ Σ w ) × √252"]}
          where={
            <>
              <span>
                <strong className="font-mono text-foreground">w</strong> — position weights (market
                value ÷ total)
              </span>
              <span>
                <strong className="font-mono text-foreground">Σ</strong> — covariance matrix of the
                aligned daily returns
              </span>
            </>
          }
        />
        <TradeOff
          chosenLabel="covariance matrix"
          chosen="Every pairwise co-movement enters the calculation, so offsetting moves reduce the result exactly as they do in reality."
          rejectedLabel="weighted average"
          rejected="Simple, and always higher than the truth. It would also make correlation pointless — diversification could never show up in the numbers."
        />
        {portfolioVol !== null && undiversified !== null && (
          <Prose>
            <p className="text-foreground">
              In your portfolio: <YourFigure label="if all moved together" value={undiversified} />{" "}
              versus <YourFigure label="actual" value={portfolioVol} />
              {benefit !== null && (
                <>
                  {" "}
                  — <span className="text-up">{benefit}</span> of risk that does not exist, because
                  your holdings do not move in unison.
                </>
              )}
            </p>
          </Prose>
        )}
        <Caveat>
          <strong className="text-foreground">Why alignment matters.</strong> A covariance between
          two holdings is only meaningful when each pair of observations comes from the same trading
          day. Before any of this runs, the engine restricts every holding to the days they all
          share. Comparing Monday&apos;s move in one stock against Tuesday&apos;s in another would
          produce a number that looks fine and means nothing.
        </Caveat>
      </Section>

      <Section id="correlation" index="05" title="Correlation between holdings">
        <Prose>
          <p>
            Covariance already captures co-movement, but its size depends on how volatile the two
            holdings are, so raw values are not comparable across pairs. Correlation divides out
            both standard deviations.
          </p>
        </Prose>
        <Formula
          lines={["ρ(i,j) = Cov(i,j) / ( σᵢ × σⱼ )"]}
          where={
            <span>
              Always between <strong className="font-mono text-foreground">−1</strong> and{" "}
              <strong className="font-mono text-foreground">+1</strong>: +1 identical, 0 unrelated,
              −1 exactly opposite.
            </span>
          }
        />
        <Prose>
          <p>
            That normalization is what lets a low-volatility bond fund and a high-volatility growth
            stock be compared on one scale. Correlation is deliberately{" "}
            <strong className="text-foreground">not annualized</strong>: scaling the covariance and
            both standard deviations by the same √252 cancels out entirely, so daily and annualized
            correlation are the same number.
          </p>
          {topPair !== undefined && (
            <p className="text-foreground">
              Your closest pair is{" "}
              <YourFigure label={`${topPair.a} / ${topPair.b}`} value={topPair.correlation} />
              {Number(topPair.correlation) >= 0.9 &&
                " — at this level the two behave as a single position under two names."}
            </p>
          )}
        </Prose>
      </Section>

      <Section id="concentration" index="06" title="Concentration and overlap">
        <Prose>
          <p>
            Concentration asks how much of the portfolio depends on any single thing. The base
            measure is the Herfindahl-Hirschman Index — the sum of squared weights, the standard
            concentration measure in economics. Squaring punishes large weights disproportionately,
            so one dominant position moves it far more than several modest ones.
          </p>
        </Prose>
        <Formula
          lines={["HHI = Σ wᵢ²", "effective holdings = 1 / HHI"]}
          where={
            <span>
              HHI runs from <strong className="font-mono text-foreground">1/n</strong> (perfectly
              equal) to <strong className="font-mono text-foreground">1</strong> (everything in one
              holding).
            </span>
          }
        />
        <Prose>
          <p>
            The reciprocal turns an abstract index into a count:{" "}
            <em>
              the number of equally-weighted positions that would be exactly this concentrated
            </em>
            .
          </p>
          {effective !== null && holdingsCount > 0 && (
            <p className="text-foreground">
              Your portfolio: <YourFigure label="holdings" value={String(holdingsCount)} />{" "}
              <YourFigure label="effective" value={Number(effective).toFixed(2)} /> — behaving like
              far fewer positions than you hold.
            </p>
          )}
          <p>
            A position is flagged overweight above{" "}
            <strong className="text-foreground">twice an equal-weight share</strong>, a baseline
            chosen to scale with portfolio size: a flat &ldquo;10%&rdquo; rule is meaningless for a
            three-holding portfolio, where nothing can be under 10%, and far too permissive for a
            fifty-holding one.
          </p>
          <p>
            The second kind of concentration is harder to see. Several holdings can each be modest
            while moving as one, so their combined weight behaves like a single much larger
            position. Orbit detects this by reusing the correlation matrix: holdings are grouped
            when each correlates at or above 0.75 with <em>every</em> member already in the group.
          </p>
        </Prose>
        <Caveat>
          <strong className="text-foreground">Why agreement with the whole group.</strong> If
          membership only required matching one member, a chain would form: A matches B, B matches
          C, so A, B and C get reported as one tight cluster even when A and C are unrelated.
          Requiring every pair to clear the threshold keeps a reported group honest.
        </Caveat>
      </Section>

      <Section id="drawdown" index="07" title="Drawdown">
        <Prose>
          <p>
            Volatility describes movement in both directions, which is not what investors actually
            feel. Drawdown describes the part they do: how far the portfolio fell from a high, how
            long it took, and whether it came back.
          </p>
        </Prose>
        <Formula
          lines={["drawdown(t) = value(t) / running_peak(t) − 1"]}
          where={
            <span>
              <strong className="font-mono text-foreground">running_peak(t)</strong> — the highest
              value reached <em>up to</em> time t. Always ≤ 0.
            </span>
          }
        />
        <Prose>
          <p>
            The reference must be the running peak, not the highest value overall. Consider 100 →
            150 → 120. Measured against the global maximum of 150, the first point would be reported
            as 33% underwater — at a moment when the portfolio had never been worth more. Against
            the running peak it is correctly 0%.
          </p>
          <p>
            Orbit also identifies discrete <strong className="text-foreground">episodes</strong>:
            each opens when value drops below its running peak and closes when that peak is
            regained, carrying peak and trough dates and both durations.
            {maxDd !== null && (
              <>
                {" "}
                Your deepest is <YourFigure label="worst decline" value={maxDd} />.
              </>
            )}
          </p>
        </Prose>
        <Caveat>
          <strong className="text-foreground">
            An unrecovered decline is reported, not dropped.
          </strong>{" "}
          If the portfolio is still below a prior peak when the window ends, that episode has no
          recovery date. It would be easy to skip it as incomplete — but an ongoing drawdown is
          precisely the one worth seeing.
        </Caveat>
      </Section>

      <Section id="limitations" index="08" title="What to scrutinize">
        <Prose>
          <p>
            Each metric is implemented correctly against its own definition. Whether those
            definitions are <em>sufficient</em> for your decisions is a separate question, and
            answering it means knowing what the analysis leaves out.
          </p>
        </Prose>

        <div className="flex max-w-[66ch] flex-col gap-5">
          {(
            [
              [
                "Volatility",
                [
                  "Treats upside and downside identically — a holding that jumps +8% scores as risky as one that falls −8%.",
                  "Invites normal-distribution intuitions under which large daily moves look nearly impossible. Real markets produce them far more often.",
                  "Uses one fixed window, weighting a day eleven months ago exactly as heavily as yesterday.",
                ],
              ],
              [
                "Correlation",
                [
                  "Correlations rise in crises. Holdings that look independent in calm markets tend to fall together in a selloff, so measured diversification is largest exactly when it is least reliable.",
                  "Captures linear relationships only. Two holdings related non-linearly can show near-zero correlation while being far from independent.",
                ],
              ],
              [
                "Concentration",
                [
                  "HHI knows only weights — it has no concept of sector, geography or currency. Ten equally-weighted semiconductor stocks score as perfectly diversified.",
                  "Overlap is inferred from price co-movement, not from what the funds actually hold. It is a good proxy, not a holdings-level comparison.",
                  "The 0.75 overlap cut-off and the 2× overweight multiple are framing conventions, not derived optima.",
                ],
              ],
              [
                "Drawdown",
                [
                  "It is a backtest of today's holdings, not your history. Share quantities are held constant across the whole window, so it answers “how would this portfolio have behaved”, not “what happened to me”.",
                  "No contributions, withdrawals or rebalancing, so it is not a performance record.",
                  "The window truncates: a one-year view cannot show a decline that began before it.",
                ],
              ],
            ] as const
          ).map(([title, points]) => (
            <div key={title} className="flex flex-col gap-2">
              <h3 className="text-sm font-semibold">{title}</h3>
              <ul className="flex list-disc flex-col gap-1.5 pl-5 text-[14px] leading-relaxed text-muted-foreground">
                {points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>
          ))}

          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold">Not implemented</h3>
            <ul className="flex list-disc flex-col gap-1.5 pl-5 text-[14px] leading-relaxed text-muted-foreground">
              <li>Stress testing under defined adverse scenarios.</li>
              <li>Risk-adjusted return — no Sharpe or Sortino ratio.</li>
              <li>Value at Risk or expected shortfall.</li>
              <li>Factor, sector or benchmark-relative decomposition.</li>
            </ul>
          </div>
        </div>

        <Caveat>
          <strong className="text-foreground">The standing constraint.</strong> Every figure
          describes the past. Orbit measures, contextualizes and explains risk — it does not predict
          prices, and nothing it reports is investment advice.
        </Caveat>
      </Section>
    </div>
  );
}
