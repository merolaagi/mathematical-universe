# Mathematical Universe

An independent web app for exploring mathematical research, proof passages, and shared learning foundations.

**Live app:** https://mathuni.fueldeskpro.com

- 373 result families and 721 manuscripts from the OpenAI math repository.
- Click graph nodes for summaries and original source details.
- Follow extracted references, proof passages, and formalization-scope links.
- Explore 30 shared learning concepts with elementary examples and 893 learning connections.
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
