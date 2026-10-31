# Mathematical Universe

An independent web app for exploring mathematical research, proof passages, and shared learning foundations.

**Live app:** https://mathuni.fueldeskpro.com

- 373 result families and 721 manuscripts from the OpenAI math repository.
- Click graph nodes for summaries and original source details.
- Follow extracted references, proof passages, and formalization-scope links.
- Explore 30 shared learning concepts with elementary examples and 893 learning connections.
- Proof workshop: 12 curated assumptions/conclusion contracts, alternative proof routes, and a declared-dependency omission check.
- Drag, resize, float, or dock the inspector on desktop.
- Use bundled compressed data alone, or connect to local Neo4j.

## Install on a Mac

Install Python 3.10 or newer and Git. For Neo4j mode, also install and open Docker Desktop.

```sh
git clone https://github.com/merolaagi/mathematical-universe.git
cd mathematical-universe
python3 scripts/launch.py --snapshot
```

Open http://127.0.0.1:18765 if the browser does not open automatically. Keep the terminal open; Control-C stops the app. Snapshot mode needs no account, Docker, or API key.

For the full Neo4j graph:

```sh
python3 scripts/launch.py
```

The first run creates a random database password in ignored `local/.env`, starts Neo4j, and imports the bundled graph. Import can take several minutes. Neo4j listens only on localhost: HTTP 18474 and Bolt 18687. The web app listens on localhost:18765. An existing installation using those ports should be stopped before starting another copy.

To stop the database:

```sh
docker compose --env-file local/.env -p mathematical-universe-standalone down
```

This preserves the database volume. Keep `local/.env` with the installation so the saved database remains accessible.

## Develop and publish changes

Edit the vanilla JavaScript, HTML, and CSS in `dist/`. No Node build or pip dependencies are required.

```sh
python3 scripts/build_foundations.py
python3 scripts/import_foundations.py  # only when Neo4j is running
python3 scripts/release.py
```

The release command versions assets and updates `version.json`. Visible app tabs check for new releases every 30 seconds. A running server serves frontend changes directly; restart it for Python backend changes.

The live custom domain uses a separately configured Cloudflare Tunnel to localhost:18765. Tunnel credentials and machine-specific installation scripts are deliberately excluded. GitHub is a source repository: pushing changes does not itself deploy to the Mac. For another checkout, pull the changes, run the release command, and restart the server if backend code changed.

## Data and interpretation

Source: https://github.com/openai/math at commit `7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a`.

The bundled data is a transformed extraction of that repository, not a new verification of its research claims. Original text and LaTeX retain source links. Proof-passage nodes are paragraphs, not certified logical deductions. Formalization links describe source-reported scope; this app does not recheck Lean proofs.

`LEARNING_PREREQUISITE` represents a curated teaching sequence. `SUGGESTED_BACKGROUND` is based on a family's subject classification. These edges are not verified proof dependencies. Incoming counts measure learning links, not mathematical importance. The 30 concepts are an initial foundation layer, not a complete reduction of each research proof to elementary steps.

To regenerate the corpus, check out the pinned upstream repository with its manuscript text sources, then run:

```sh
python3 scripts/extract.py /path/to/openai-math
python3 scripts/validate.py
python3 scripts/build_foundations.py
python3 scripts/release.py
```

## License and attribution

Apache License 2.0; see `LICENSE`. The upstream OpenAI math material is distributed under Apache 2.0; its license is also retained at `dist/LICENSE-source.txt`. This project adds the explorer, extraction/import tooling, and curated learning notes. It is an independent project, not an official OpenAI product.

## Proof workshop

Select **Proof workshop · assumptions & routes** in the sidebar, or open the workshop from Catalan’s constant. Every contract states assumptions, a conclusion, a justification, and its status. The finite-sum example compares induction with reversing and pairing the sum. The Catalan example reconstructs the final contradiction conditional on four source propositions; those propositions remain unverified. This is not a new solution.

**Try removing a premise** traverses only `USES_RESULT` edges. It reports missing declared dependencies and cycles, not mathematical validity, completeness of assumptions, or discoveries. `ALTERNATIVE_PROOF` edges represent separate routes; `SOURCE_SUPPORT` links to the pinned manuscript. Candidate edges never become proof dependencies automatically.

To maintain this layer:

```sh
python3 scripts/build_reasoning.py
python3 scripts/validate_reasoning.py
python3 scripts/import_reasoning.py  # with Neo4j running
python3 scripts/release.py
```

The elementary arguments and source reconstructions are curated teaching material, not machine-checked formal proofs. No claim is made that all corpus problems have structured contracts.

## Backward paths to college mathematics

Use **Trace a problem to college math** in the sidebar. The current routes cover Catalan’s constant (f005), matrix multiplication exponents (f107), and relativistic Vlasov–Maxwell smoothness (f362). Seventeen intermediate concept nodes connect these topics to college calculus, linear algebra, elementary number theory, and differential equations. Each node includes an approximate level, subject, explanation, and a worked example. The expanded route stops at college foundations; **Simpler foundations** continues below that level.

These are selected learning routes, not complete reductions of the research proofs. Examples from simpler equations explain methods without proving the full system’s claims. Course links provide background reading. Shared prerequisite IDs reuse existing nodes.

```sh
python3 scripts/build_paths.py
python3 scripts/validate_paths.py
python3 scripts/import_paths.py  # with local Neo4j running
python3 scripts/release.py
```

Validation checks endpoints and that every expanded advanced branch reaches a college-level node without a cycle. It does not certify pedagogical completeness or prove the research claims.

## Recursive argument decomposition

**Decompose an argument** opens six worked breakdowns: rational determinants, the rational product formula, source-dependent nonvanishing, matrix composition, constant-speed transport, and a basic Grönwall estimate. There are 37 new argument nodes and 51 connections.

Each step records assumptions, a conclusion, its justification, and required supporting results. **Break down this argument** expands the declared dependency graph. **Why does this step work?** follows one justification at a time. Shared rules use the same node IDs. **Where this explanation stops** lists definitions, foundational principles, accepted but unexpanded theorems, and unverified research premises separately.

The calculus route expands the mean value theorem through Rolle’s theorem and stationary extrema. It still stops at explicitly stated standard results such as the extreme-value theorem and exponential differentiation. A nonvanishing example separates the source’s difficult valuation estimate from its elementary logical consequence. None of these examples constitutes a new verification of a research claim, a universal complexity ordering, or a complete reduction of every corpus theorem to axioms.

```sh
python3 scripts/build_decomposition.py
python3 scripts/validate_decomposition.py
python3 scripts/import_decomposition.py
python3 scripts/release.py
```

Structural validation checks that derived steps have supporting nodes, every terminal node declares its boundary, the selected routes are acyclic, and the research uncertainty is retained. This is not a formal proof checker.

## Embedded Lean playground

Click **Lean playground** in the header, or **Explore Lean example** on supported nodes. The embedded official [Lean Web editor](https://live.lean-lang.org/) supports live editing and displays its own goals and diagnostics. It sends code to that external service and requires internet access. It is not a compiler endpoint on the hosting Mac. If embedding fails, use **Open full editor**.

Forty `.lean` files under `dist/lean/` cover logic, predicate-based sets, functions and inverses, divisibility, modular arithmetic, induction, finite lists, integer sequences, graph reachability, and small algebra models. The picker supports topic groups and search. They import only Std. The bundled files were checked with the compiler version recorded in `dist/lean-examples.json`; output includes `#print axioms`. An analogous or conditional example does not certify the connected research claim. The external editor may use a different Lean version.

Choose an example and click **Load example in editor** to replace the editor contents. Preserve edits with the external editor’s save/share controls before switching. Closing and reopening the panel in the same page retains the frame; page reloads do not guarantee retention. Automatic app reload is paused while the playground is open. MathUni does not read cross-origin compiler messages or automatically mark graph nodes verified.

To reproduce local checks with Lean on PATH:

```sh
python3 scripts/build_lean_library.py
python3 scripts/check_lean_examples.py
python3 scripts/release.py
```

The check script runs only the maintained repository examples, rejects admitted proofs in those examples, and tests that an intentionally invalid proof fails and a `sorry` proof exposes `sorryAx`. It is not an HTTP service for executing user input. To work offline, download an example and run `lean Example.lean` locally.
