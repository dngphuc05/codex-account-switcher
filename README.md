# cx — Codex account switcher for Linux

`cx` is a small Python command-line tool for using multiple ChatGPT accounts with the Codex CLI on Linux. Each named account gets its own `CODEX_HOME`, so you can keep two Codex terminals open with different accounts without logging out. It also offers a shared-history mode for attempting to resume an existing local conversation ID with another signed-in account.

## Requirements

- Linux with Python 3.9 or newer
- [Codex CLI](https://developers.openai.com/codex/cli) installed and available as `codex`
- ChatGPT accounts you can sign in to

`cx` uses only the Python standard library.

## Install

```bash
git clone https://github.com/dngphuc05/codex-account-switcher.git
cd codex-account-switcher
mkdir -p ~/.local/bin
install -m 755 cx ~/.local/bin/cx
```

Make sure `~/.local/bin` is in your `PATH`. Many Linux distributions already add it. Check with `command -v cx`. If it is missing, add this line to your shell startup file (`~/.bashrc` or `~/.zshrc`), then open a new terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Set up accounts

If Codex is already signed in under `~/.codex`, import that login without signing in again:

```bash
cx import-current main
```

Sign in to another account. Profile names are your choice: letters, digits, `_` and `-`, up to 40 characters, beginning with a letter or digit.

```bash
cx login second --device-auth
cx status
cx list
```

You can omit `--device-auth` to use the normal browser login flow. Credentials are stored locally under `~/.local/share/cx/accounts/PROFILE/` with private permissions.

## Run accounts at the same time

Open two terminals:

```bash
cx run main
```

```bash
cx run second
```

Commands run from your current directory, so each terminal can use a different project. If both sessions will edit the same Git repository, separate worktrees help avoid conflicting edits.

Resume a session in the profile where it was created:

```bash
cx resume second SESSION_UUID
```

Arguments after the profile name are passed to Codex, for example `cx run second -C /path/to/project`.

## Resume an existing ID with another account

For a conversation stored in the normal `~/.codex` history:

```bash
cx switch SESSION_UUID --to second
```

This temporarily selects `second`'s credentials in `~/.codex`, runs `codex --no-daemon resume SESSION_UUID`, then saves any refreshed credentials and restores the original login. A lock prevents two `cx switch` sessions from running together. Close other Codex processes that use `~/.codex` before switching; the lock cannot control processes launched outside `cx`.

The CLI may reject a conversation under a different account. `cx` keeps the local UUID and does not change server-side conversation ownership. Cross-account resume depends on what the Codex service permits; it is not guaranteed. Isolated profiles started with `cx run` have separate histories and cannot be switched by copying their session files.

If the process or machine stops during a switch, run `cx recover` before opening normal Codex. A later `cx switch` also tries to recover automatically.

## Storage and configuration

- `~/.local/share/cx/accounts/PROFILE/`: credentials and session history for each isolated profile
- `~/.local/share/cx/shared-backup/`: temporary private credential backup during `cx switch`
- `~/.codex/`: existing Codex home used by shared-history switching

New profiles start with `model_context_window = 500000` in their `config.toml`. You can edit that value per profile. The actual usable window depends on the selected model and service.

Treat `auth.json` as a password. Do not commit or share it.
