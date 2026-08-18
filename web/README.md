# My osyd App

A modern web application built with the osyd framework.

This starter keeps the application structure minimal.

## Getting Started

### Prerequisites

- Package manager: pnpm (npm also works)
- A GitHub token with the `read:packages` scope. The osyd packages are published
  privately to GitHub Packages under the `@creatureshoppe` scope, and this project
  ships an `.npmrc` that points that scope at `https://npm.pkg.github.com`.

### Authentication

This project's `.npmrc` only routes the `@creatureshoppe` scope to GitHub Packages.
Your token must go in your **user-level, untracked** `~/.npmrc` (pnpm/npm will not
expand secrets from a committed project file). Store it once with:

```bash
npm config set "//npm.pkg.github.com/:_authToken" your_github_token_with_read_packages
```

### Installation

```bash
pnpm install
```

### Development

Start the development server:

```bash
pnpm dev
```

The application will be available at `http://localhost:5173` (or the next available port).

## Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm preview` - Preview production build locally
- `pnpm test` - Run tests with Vitest
- `pnpm lint` - Run ESLint code linting
- `pnpm lint:fix` - Auto-fix ESLint issues where possible
- `pnpm skill:sync` - Refresh the osyd agent guidance (`AGENTS.md` + `.claude/skills/osyd/SKILL.md`) from the installed osyd version

## AI agent guidance

This project ships the osyd "house style" so AI coding agents work in osyd
idioms out of the box:

- `AGENTS.md` (repo root) — read by most agents (Claude Code, Cursor, Copilot, …).
- `.claude/skills/osyd/SKILL.md` — Claude Code's native skill format.

Both are generated from the canonical skill bundled in the `osyd` package. After
upgrading osyd, run `pnpm skill:sync` to pull the matching guidance. The osyd
content in `AGENTS.md` lives in a managed block (between the `BEGIN/END osyd
house style` markers) — anything you add outside that block is preserved on sync.

## Project Structure

```
src/
├── app.ts           # Root app component
├── main.ts          # Application entry point
├── style.css        # Global styles
└── vite-env.d.ts    # Vite type declarations
```
