# Team checkpoints

Use a small number of meaningful commits: an implemented phase, a verified fix, or a finished evidence/documentation update. Record actual work when it is ready; do not backdate commits or split a completed snapshot to simulate earlier development.

The first implementation checkpoint is authored by Silveroger (`eshans444@gmail.com`), as requested by Eshan. LakshGargG (`lakshgargg@gmail.com`) can author a later checkpoint for work he implements or substantively reviews and owns. For a genuine joint contribution, use a `Co-authored-by` footer with the contributor's agreement.

Local commit authorship uses this repository's Git identity. It does not require signing out of GitHub. The credentials used to push are separate; GitHub associates commits with accounts through verified email addresses. Never include credentials, `.env`, runtime data, installed dependencies or reference checkouts in commits.

This project was developed with Codex assistance. Dependency provenance, measured results and unfinished validation are documented openly. Before a checkpoint, inspect the staged diff and run checks appropriate to its changes.
