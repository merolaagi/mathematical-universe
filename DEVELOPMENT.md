# Live app and future iterations

The user's primary app is now https://mathuni.fueldeskpro.com, hosted directly from this directory on the Mac. Continue edits here, not in the older Sites snapshot or package staging directory. The user has requested that iterations update this public domain automatically.

Frontend source and served files are in `dist/`. After editing and verifying a frontend change, run `python3 scripts/release.py`. This adds versioned asset URLs, updates the HTML build marker, and writes `dist/version.json` last. The running server serves files directly, so frontend changes do not need a process restart, sudo, or a tunnel restart. Active visible tabs check every 30 seconds; returning to a background tab also checks. The first version with update detection needs one manual reload in older tabs.

Validate via the public domain. It should return the same build marker as `dist/version.json`. Panel preferences are saved in browser local storage under `mathuni.inspector`. On screens up to 800 pixels wide, the inspector uses a full-width stacked layout.

The app server is a user LaunchAgent named `com.mathuni.web`, serving localhost:18765. Cloudflare tunnel `3fd5e34a-b4ff-4229-b11d-24116875483f` routes the hostname to this port. Neo4j runs via Docker on localhost:18474 (HTTP) and 18687 (Bolt). Keep the Mac awake and Docker running.

For backend Python changes, restart the user LaunchAgent after verification. Do not rerun the root-owned tunnel installer for normal application edits. Do not expose credentials in `local/.env` or package runtime logs. The older ChatGPT Sites URL and previously downloaded ZIP are separate snapshots and are not automatically synchronized by the local release command.

## Curated learning layer
`dist/foundations.json` contains original teaching notes, elementary worked examples, and shared learning links. Regenerate with `python3 scripts/build_foundations.py`, then run `python3 scripts/import_foundations.py` to update Neo4j and `python3 scripts/release.py` to publish. The normal full import also includes this layer.

`LEARNING_PREREQUISITE` connects concepts in a chosen teaching sequence. `SUGGESTED_BACKGROUND` connects families to concepts solely by catalogue subject. Neither is an extracted or certified proof dependency. Counts measure incoming learning edges, not mathematical importance. The initial 30 concepts are a starting map; intermediate research-specific lemmas and simplified manuscript proofs still need individual curation.
