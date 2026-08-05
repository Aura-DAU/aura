# Release process

The repository publishes GitHub Releases from `main` after the Aura CI workflow
finishes successfully. Release versions exist only as Git tags and GitHub
Releases; `aura/package.json` is not a release-version source.

## Versioning

Releases use Semantic Versioning and tags take the form `vMAJOR.MINOR.PATCH`.
The baseline release is `v1.0.0`. Later versions are calculated from commits
on `main` since the previous release.

| Commit form | Version bump |
| --- | --- |
| `feat(scope): description` | Minor |
| `fix(scope): description` or `perf(scope): description` | Patch |
| A `BREAKING CHANGE:` footer or `!` before the colon | Major |
| `docs`, `chore`, `refactor`, `test`, `ci`, `style` | No release |

Merge pull requests with a Conventional Commit title because the merged commit
is the release-note source. A release is created only when at least one commit
requires a version bump.

## Initial release

`v1.0.0` is created once from a known-good, deployed `main` commit. Its GitHub
Release notes are reviewed manually because there is no earlier tag to define
the change range.

## Deployment relationship

Production CD deploys validated changes to `main` before the release workflow
runs. A GitHub Release marks that deployed version; it does not initiate a
second deployment.
