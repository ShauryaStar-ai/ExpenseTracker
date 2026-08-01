---
description: End-to-end feature push — commit, push branch, open a PR via GitHub MCP, switch back to main, and optionally clean up after merge. Usage: /push-feature "PR title" or /push-feature (title inferred from branch name).
allowed-tools: Bash(git status), Bash(git diff), Bash(git log), Bash(git add), Bash(git commit), Bash(git push), Bash(git checkout), Bash(git pull), Bash(git branch), mcp__github__create_pull_request, mcp__github__list_pull_requests, mcp__github__merge_pull_request, mcp__github__get_me
---

Automate the full feature-push workflow for the Spendly project.
The optional `$ARGUMENTS` value is the PR title. If omitted, derive
a title from the current branch name (replace hyphens/underscores
with spaces, title-case each word, strip any leading `feature/`
or `fix/` prefix).

---

## Step 0 — Safety guards (run ALL checks before proceeding)

1. Run `git status` to capture the current state.
2. **Branch guard:** Read the active branch name.
   - If the branch is `main` or `master`, stop immediately and say:
     "You're on `main`. Create a feature branch first, then re-run
     /push-feature."
3. **Clean-tree guard:** If `git status` shows nothing staged and
   nothing modified (working tree is already clean), stop and say:
   "Nothing to commit — your working tree is clean. If your changes
   are already pushed, check the PR on GitHub."

Record: `BRANCH_NAME` = active branch, `REPO` = `ShauryaStar-ai/python-expense-tracker`.

---

## Step 1 — Stage and commit

1. Run `git diff --stat` so the user can see what will be staged.
2. Run `git add -A` to stage all untracked and modified files.
   - Exception: warn (but don't abort) if files matching `*.env`,
     `*.key`, `*secret*`, or `*.db` are about to be staged.
3. Build a commit message:
   - If `$ARGUMENTS` was given, use it as the subject line.
   - Otherwise, derive from `BRANCH_NAME`:
     strip `feature/` or `fix/` prefix → replace `-`/`_` with
     spaces → title-case → prepend `feat:` or `fix:` accordingly.
   - Append the co-author trailer:
     `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
4. Run the commit using a heredoc so the message is passed verbatim:
   ```
   git commit -m "$(cat <<'EOF'
   <subject line>

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
   EOF
   )"
   ```
5. If the commit exits non-zero (pre-commit hook or other failure),
   stop and report the exact error. Do NOT use `--no-verify`.

---

## Step 2 — Push branch to remote

Run:
```
git push -u origin <BRANCH_NAME>
```

If push is rejected because the remote branch already has newer
commits, stop and say:
"Push rejected — the remote branch has commits your local copy
doesn't. Run `git pull --rebase` to reconcile, then re-run
/push-feature."

---

## Step 3 — Open Pull Request via GitHub MCP

1. Call `mcp__github__get_me` to confirm the authenticated GitHub
   user (sanity check; proceed regardless of result).
2. Build the PR body using this template:

   ```
   ## Summary
   - <one-line summary of what this branch implements>
   - Implements spec: `.claude/specs/<spec-name>.md` (if a matching spec exists)

   ## Test plan
   - [ ] App starts without errors (`python app.py`)
   - [ ] Feature works end-to-end in the browser
   - [ ] No regressions on existing routes

   🤖 Generated with [Claude Code](https://claude.ai/code)
   ```

   Fill in the summary line from the branch name or `$ARGUMENTS`.

3. Call `mcp__github__create_pull_request` with:
   - `owner`: `ShauryaStar-ai`
   - `repo`: `python-expense-tracker`
   - `title`: the PR title (from `$ARGUMENTS` or derived in Step 1)
   - `head`: `BRANCH_NAME`
   - `base`: `main`
   - `body`: the template above

4. Print the returned PR URL prominently so the user can open it.

---

## Step 4 — Switch back to main

Run in sequence:
```
git checkout main
git pull origin main
```

Confirm to the user that `main` is now checked out and up-to-date.

---

## Step 5 — Offer post-merge cleanup (do NOT auto-merge)

After switching to main, ask the user ONE question:

> "PR is open. After your reviewer merges it on GitHub, run
> `/push-feature cleanup <BRANCH_NAME>` and I'll delete the local
> branch for you."

If `$ARGUMENTS` starts with `cleanup `, treat the rest as
`CLEANUP_BRANCH` and jump directly to the cleanup sub-flow:

### Cleanup sub-flow

1. Check that `CLEANUP_BRANCH` is NOT the currently active branch.
   If it is, `git checkout main` first.
2. Call `mcp__github__list_pull_requests` with `state: closed` and
   look for a PR whose `head.ref` matches `CLEANUP_BRANCH`.
   - If no closed PR is found, warn: "No closed PR found for
     `CLEANUP_BRANCH>`. Is it merged yet?" and stop.
3. Delete the local branch:
   ```
   git branch -d <CLEANUP_BRANCH>
   ```
   Use `-d` (safe delete) — not `-D`. If it fails because the
   branch is not fully merged, report it and stop; do NOT force-delete.
4. Confirm: "Local branch `<CLEANUP_BRANCH>` deleted. You're clean."

---

## Final output

At the end of the main flow (Steps 0–4) print a short summary:

```
✅ Feature pushed

  Branch : <BRANCH_NAME>
  Commit : <short SHA>
  PR     : <PR URL>
  Now on : main
```

If any step fails, print which step failed, the exact error, and
a one-line remediation hint. Do not silently swallow errors.
