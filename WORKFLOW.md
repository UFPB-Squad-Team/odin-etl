# WORKFLOW.md

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](#)
[![Coverage](https://img.shields.io/badge/Coverage-__%25-blue)](#)
[![License](https://img.shields.io/badge/License-MIT-blue)](#)

> Purpose: concise, modern, and professional developer workflow for contributing code. Designed to be clear, beautiful, and actionable.

---

## Table of contents

- [Principles](#principles)
- [Prerequisites & dev environment](#prerequisites--dev-environment)
- [Branching strategy](#branching-strategy)
- [Feature development flow (quick)](#feature-development-flow-quick)
- [Detailed steps](#detailed-steps)
  - [Create branch](#create-branch)
  - [Development & commits](#development--commits)
  - [Tests & pre-commit checks](#tests--pre-commit-checks)
  - [Push & open PR](#push--open-pr)
  - [Review & merge](#review--merge)
- [Pull Request template (recommended)](#pull-request-template-recommended)
- [Code review checklist](#code-review-checklist)
- [CI / CD expectations](#ci--cd-expectations)
- [Best practices & tips](#best-practices--tips)
- [Quick command cheatsheet](#quick-command-cheatsheet)
- [Appendix: examples](#appendix-examples)

---

## Principles

- Small, focused changes—one feature/bug per branch.
- Use readable, conventional commit messages.
- Tests and linters must pass before review.
- CI checks are required and enforced via branch protection.
- Be respectful, constructive, and precise in reviews.

---

## Prerequisites & dev environment

- Git (>=2.30), Node/Python/Go etc. as required by repo.
- Recommended: VS Code + Remote Containers (devcontainer.json) for consistent environment.
- Install tooling: linters, formatters, pre-commit, and test runners.
- Configure Git user/email and add SSH key to GitHub/GitLab.

Example devcontainer recommendation:

- Use Dockerfile or devcontainer to ensure reproducible builds and tests.

---

## Branching strategy

- main (protected): release-ready production code.
- development (optional): integration branch for ongoing work.
- feature/<short-descriptor> — new features
- fix/<issue-number>-<short> — bug fixes
- hotfix/<version> — urgent production fixes
- release/<version> — release prep

Naming style: kebab or slash-separated; be consistent.

---

## Feature development flow (quick)

1. git fetch && git checkout development && git pull
2. git checkout -b feature/<what-will-do>
3. Code → add tests → run linters/formatters
4. git add . && git commit -m "feat(scope): concise description"
5. git push origin feature/<...>
6. Open Pull Request, fill template, request reviewers
7. Address feedback → CI green → merge (squash/rebase as policy)

---

## Detailed steps

### Create branch

Always start from the latest development:

```
git fetch origin
git checkout development
git pull origin development
git checkout -b feature/<short-summary>
```

### Development & commits

- Make small commits. Prefer "logical commits" not mechanical ones.
- Use Conventional Commits:
  - feat(scope): add new payment adapter
  - fix(api): validate user input
  - docs(readme): update usage example
  - chore: update deps
- Include issue references: `feat(auth): refresh token logic (#123)`
- Keep commit bodies short but descriptive. Wrap lines at ~72 chars.

### Tests & pre-commit checks

- Run unit/integration tests locally: `npm test` / `pytest` / `go test ./...`
- Use pre-commit or Husky + lint-staged to run formatting and fast checks on staged files.
- Example tools: Prettier, ESLint, Black, isort, golangci-lint.

Recommended pre-commit actions:

- Run formatter
- Run linter
- Run tests (fast subset)
- Deny accidental secrets (detect with git-secrets or detect-secrets)

### Push & open PR

```
git push -u origin feature/<short-summary>
```

Open a Pull Request from your branch to main (or develop). Use the PR template below. Assign required reviewers and link related issue(s).

### Review & merge

- Wait for required approvals and green CI.
- Address review comments in commits or with force-push when rebasing. Prefer adding commits unless squashing before merge is the repository policy.
- Merge strategy (project policy):
  - Squash-and-merge: keeps main tidy with one logical commit per PR.
  - Rebase-and-merge: preserve linear history.
  - Merge commit: for large or complex merges if team prefers.

Enforce branch protection: require CI, required reviewers, and no force-push to main.

---

## Pull Request template (suggested)

Title: type(scope): short summary — closes #ISSUE

Description:

- Summary of changes
- Motivation and context
- How to test (manual steps)
- Checklist:
  - [ ] Tests added/updated
  - [ ] Linter/formatter run
  - [ ] Documentation updated
  - [ ] CI green

Include screenshots or logs if applicable.

---

## Code review checklist

- Functionality: implements the intended feature/bugfix
- Tests: adequate coverage and cases
- Style: follows style guide and linters pass
- Performance: no obvious regressions
- Security: no secrets, encoding issues, or injection paths
- Docs: public APIs documented
- Backward compatibility considered

Be kind: give actionable, specific feedback.

---

## CI / CD expectations

- Every PR triggers CI pipeline:
  - Lint → Test → Build → Integration/Smoke tests
- Required checks before merge: lint, tests, security scans
- Releases automated via semantic-release or GitHub Actions on tagged commits
- Artifacts stored in registry (npm/pypi/containers) with immutable tags

---

## Best practices & tips

- Rebase interactively to clean commit history before merge if policy allows.
- Keep PRs small and focused.
- Write tests for new behavior and regressions.
- Use feature flags for large or risky features.
- Use issue templates and link PRs to issues.
- Use CODEOWNERS to auto-request reviewers for directories.

---

## Quick command cheatsheet

- Start: git fetch && git checkout -b feature/name
- Stage & commit: git add -A && git commit -m "feat(scope): ..."
- Amend last commit: git commit --amend --no-edit
- Rebase interactive: git rebase -i HEAD~3
- Push branch: git push -u origin feature/name
- Delete local/remote branch: git branch -d feature/name && git push origin --delete feature/name

---

## Appendix: examples

Commit messages:

- feat(api): add user search endpoint
- fix(auth): prevent token reuse
- docs(contrib): add workflow guide

PR template (short):

```
## What
Brief summary

## Why
Why this change

## How to test
1. ...
2. ...

Closes: #123
```
