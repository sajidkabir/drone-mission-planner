# Contributing

Contributions are welcome: bug reports, model corrections, new checks,
documentation, and example missions. This project aims to stay small,
readable, and honest about its assumptions.

## Getting set up

```bash
git clone https://github.com/sajidkabir/drone-mission-planner.git
cd drone-mission-planner
python -m venv .venv
source .venv/bin/activate
pip install -e . pytest
pytest -q
```

All 22 tests should pass before you change anything. The package has no
runtime dependencies; please keep it that way unless a change genuinely
cannot be done with the standard library.

## Making a change

1. Fork the repository and create a branch from `main`
   (`git checkout -b feature/short-name`).
2. Keep the change focused. One model, one fix, or one feature per pull
   request.
3. Add or update tests. Model changes need a sanity check against a
   hand-computed value or a published reference, and the test should say
   which.
4. Run `pytest -q` and make sure it is green.
5. Update the README, the docstrings, and `CHANGELOG.md` (Unreleased
   section) if behavior or numbers change.
6. Open a pull request against `main` describing what changed, why, and
   what it does to the verdict for the bundled Dhaka survey mission.

## Ground rules

- No silent changes to validated numbers. If a fix moves a result, say so
  in the pull request and in the changelog.
- Prefer explicit formulas over clever code. A reviewer should be able to
  check each relation against its source.
- New assumptions go in the README limitations list until they are modeled.

## Reporting issues

Open an issue with the mission file, the command or code you ran, the
output you got, and the output you expected. A minimal reproducing mission
(a few waypoints in JSON) is worth more than a long description.
