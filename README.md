# Browser Agent

An agent that operates a real web browser the way a person would: it looks at the page, decides what to click or type, performs the action, and checks what happened. It works on sites that have no API, such as booking flows, form filling, and data collection.

Playwright controls the browser. A vision-capable LLM (Claude) interprets what is on screen and chooses the next action.

---

## How it works

```
Observe  ->  Decide  ->  Resolve  ->  Classify  ->  Approve  ->  Execute  ->  Verify  ->  repeat
```

1. **Task intake:** you give a goal, e.g. *"Find the cheapest direct flight from X to Y next Friday and fill the booking form up to payment."*
2. **Browser session:** Playwright launches Chromium with a persistent profile, a fixed viewport, and optional saved login state.
3. **Observation:** the agent captures a screenshot plus a compact page representation (accessibility tree or filtered DOM listing interactive elements with IDs).
4. **Decision:** the LLM returns exactly one structured action per step.
5. **Resolve:** the element ID, selector, or coordinates are turned into a Playwright locator.
6. **Classify and approve:** the resolved element (text, role, target form) is checked for irreversible or sensitive actions. Risky actions pause for user approval.
7. **Execute:** Playwright performs the action, waiting for navigation, network idle, or element visibility.
8. **Verify:** before and after state are compared (URL changed, element appeared, field filled).
9. **Recover:** on failure, the agent re-observes, retries with a different strategy, dismisses overlays, or backtracks.
10. **Output:** extracted data (JSON/CSV), a completion report, and a replayable trace with screenshots.

### Grounding strategies

The hard part is grounding: turning "click the Search button" into the exact element on a messy real page.

| Strategy | How the LLM refers to elements | Strengths | Weaknesses |
|---|---|---|---|
| DOM / accessibility | "click element 14" | Reliable, cheap | Fails on canvas and custom widgets |
| Vision | Pixel coordinates from the screenshot | Works on anything | Less precise |
| Set-of-marks (default) | Numbered boxes overlaid on the screenshot | Hybrid: sees and references both | Slightly higher image cost |

---

## Actions

The model returns one action per step:

`click` · `type` · `select` · `scroll` · `press_key` · `navigate` · `wait` · `extract` · `done`

The schema starts small (click, type, scroll, navigate, done) and grows as failures demand it.

---

## Safety

Browsing the open web with an LLM is risky, so safety is built in rather than bolted on. No single layer is sufficient; they work together.

- **Domain allowlist:** every navigation is checked against the allowed domains.
- **Approval gate:** irreversible actions (payments, sending messages, deleting data) pause for human confirmation.
- **Action classifier:** flags risky actions using the *resolved* element, not just the model's description.
- **Injection guard:** page text is wrapped and treated as untrusted data, never as instructions. This is one layer only; prompt injection cannot be fully solved with filtering.
- **Credential vault:** secrets are injected into the page without ever being shown to the LLM.

---

## Project structure

```
browser-agent/
├── pyproject.toml                  # Packaging + `browser-agent` CLI entry point
├── src/browser_agent/
│   ├── main.py                     # CLI: `browser-agent run "<task>"`
│   ├── config.py                   # pydantic-settings: model, viewport, budgets, domains
│   │
│   ├── core/
│   │   ├── agent_loop.py           # observe -> decide -> resolve -> classify -> act -> verify
│   │   ├── state.py                # Task, step history, current URL, progress notes
│   │   ├── action_schema.py        # Contract between the LLM and the browser
│   │   ├── planner.py              # Optional high-level subgoals (later)
│   │   ├── stopping_criteria.py    # Done, max steps, loop detection, cost cap
│   │   └── recovery.py             # Retry, backtrack, dismiss popups, re-plan
│   │
│   ├── browser/
│   │   ├── session_manager.py      # Launch/close Playwright, contexts, profiles
│   │   ├── executor.py             # click, type, select, scroll, press, navigate, wait
│   │   ├── waits.py                # Network idle, DOM stable, visibility
│   │   ├── tabs.py                 # New tabs/windows and iframes
│   │   └── auth_state.py           # Save/load cookies and login sessions
│   │
│   ├── perception/
│   │   ├── screenshotter.py        # Viewport/full-page screenshots, resizing
│   │   ├── dom_simplifier.py       # Strip DOM to interactive elements + text
│   │   ├── accessibility_tree.py   # Playwright accessibility snapshot
│   │   ├── element_registry.py     # Assigns IDs and resolves them back to locators
│   │   ├── set_of_marks.py         # Numbered box overlays
│   │   └── page_diff.py            # Detect what changed after an action
│   │
│   ├── grounding/
│   │   ├── selector_builder.py     # Resilient selectors (role, label, text) over brittle CSS
│   │   └── coordinate_click.py     # Vision-based fallback
│   │
│   ├── llm/
│   │   ├── llm_client.py           # Claude API with vision + native tool use
│   │   └── prompts.py              # System prompt, observation format, rules
│   │
│   ├── safety/
│   │   ├── action_classifier.py
│   │   ├── approval_gate.py
│   │   ├── domain_allowlist.py
│   │   ├── injection_guard.py
│   │   └── credential_vault.py
│   │
│   ├── extraction/
│   │   ├── data_extractor.py
│   │   └── output_writer.py
│   │
│   └── utils/
│       ├── logging_setup.py
│       ├── trace_recorder.py       # Screenshot + action + reasoning per step
│       ├── trace_replayer.py       # Replay a run for debugging
│       └── cost_tracker.py         # Tokens and image costs per run
│
├── evaluation/
│   ├── benchmark_runner.py
│   ├── local_test_sites/           # Self-hosted sites for deterministic tests
│   ├── webarena_adapter.py         # Optional: WebArena / MiniWoB++
│   ├── metrics.py                  # Success rate, steps, cost, recovery rate
│   └── failure_analyzer.py
│
├── data/                           # Git-ignored
│   ├── traces/
│   ├── browser_profiles/
│   └── outputs/
│
├── tests/
│   ├── fixtures/                   # Saved HTML pages for offline tests
│   ├── test_dom_simplifier.py
│   ├── test_element_registry.py
│   ├── test_action_classifier.py
│   ├── test_stopping_criteria.py
│   └── test_agent_loop.py
│
├── .env.example
├── .gitignore
├── Dockerfile
└── README.md
```

---

## Getting started

### Requirements

- Python 3.11+
- An Anthropic API key

### Install

```bash
git clone https://github.com/masudibnmusa/Computer-Use-Browser-Agent.git
cd browser-agent

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e .
playwright install chromium
```

### Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=your-key-here
MODEL=claude-sonnet-4-6
VIEWPORT_WIDTH=1280
VIEWPORT_HEIGHT=800
MAX_STEPS=30
MAX_COST_USD=1.00
ALLOWED_DOMAINS=example.com,localhost
```

### Run

```bash
browser-agent run "Go to the local test shop and add the cheapest item to the cart"
```

Useful flags:

```bash
browser-agent run "<task>" --headed            # watch the browser
browser-agent run "<task>" --max-steps 20      # override the step budget
browser-agent run "<task>" --observation dom   # dom | screenshot | marks
```

Replay a previous run:

```bash
browser-agent replay data/traces/<run-id>
```

### Docker

```bash
docker build -t browser-agent .
docker run --rm --env-file .env -v "$(pwd)/data:/app/data" browser-agent run "<task>"
```

---

## Output

Each run writes to `data/`:

- `outputs/<run-id>/result.json` (or `.csv`): extracted data
- `outputs/<run-id>/report.md`: completion report
- `traces/<run-id>/`: per-step screenshot, action, and the model's reasoning, replayable with `browser-agent replay`

---

## Evaluation

Runs are benchmarked on self-hosted test sites so results are deterministic.

```bash
python -m evaluation.benchmark_runner --suite local
```

Metrics: success rate, steps per task, cost per task, recovery rate. The failure analyzer groups failed runs by cause (element not found, popup, loop, timeout, wrong page).

Optional adapters for WebArena and MiniWoB++ are planned.

---

## Testing

```bash
pytest
```

DOM simplification and element registry tests run offline against saved HTML in `tests/fixtures/`.

---

## Known limitations

- Canvas elements, shadow DOM, and complex iframes are hard to ground reliably.
- CAPTCHAs and bot-detection are not handled, and the agent should not be used to bypass them.
- Screenshots on every step are expensive; the default observation uses DOM first and adds a screenshot on failure or at intervals.
- Prompt injection from web pages is reduced by structural defenses but not eliminated.

---

## Responsible use

Only automate sites you are permitted to automate, and respect each site's terms of service and robots rules. Keep the approval gate enabled for anything involving payments, messages, or deletions. Never commit `.env` or `data/browser_profiles/`, since they contain secrets and login sessions.

---

## License

MIT