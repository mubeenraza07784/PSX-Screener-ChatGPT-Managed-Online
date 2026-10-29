# Instructions for ChatGPT when managing this screener

You are assisting with a **private, GitHub-hosted** Pakistan Stock Exchange research dashboard formerly managed through Claude. This repo is the source of truth. Preserve existing source code and calculations unless the user requests changes; make focused fixes with tests and explain any change to ranking/signal behavior.

1. Review `README.md`, `docs/METHOD.md`, `docs/STRATEGIES.md`, and `docs/KNOWN_ISSUES.md` before changing the model.
2. Distinguish display snapshots from verified current PSX prices. State `data/current/market.json` `as_of` and each stock's `last_price_date`. Do not invent intraday candles, volume, trading signals or return metrics.
3. Honor the user's preferred timeframes: 1D for trend/analysis; 4H execution only when verified OHLCV exists. Daily prices are not a substitute for 4H signals.
4. Keep 33-ratio fundamental scoring, strategies, valuations, and historical alerts unless the user approves revised logic. Test rule changes and summarize their market impacts.
5. Do not automatically trade, place orders, send messages, publish personal data, or silently change holdings. Confirm separately before high-impact actions.
6. Treat all holdings data as private. Reconcile old hard-coded holdings with new `config/holdings.json` only using verified user updates.
7. The GitHub Actions workflow refreshes data where legally and technically accessible. If a provider blocks or rate-limits, stop and report; do not bypass anti-bot measures.
8. For code changes, explain the issue, tests, and deployment impact. Prefer reviewed PRs rather than directly changing live `main` for high-risk changes.
9. ChatGPT subscription != OpenAI API quota: do not promise an embedded 24/7 AI agent without a separate approved API integration and hosting.
