CRUSH.md — Quick Commands & Code Style for trc_platform

Build/Lint/Test Commands
- Root JS workspace (flow/ monorepo)
  - Install: pnpm install
  - Build: pnpm -C flow build
  - Dev (extension): pnpm -C flow dev
  - Zip + E2E: pnpm -C flow e2e
  - Lint: pnpm -C flow lint   | Fix: pnpm -C flow lint:fix
  - Typecheck: pnpm -C flow type-check
  - Format: pnpm -C flow format
- Frontend (Vite React app)
  - Dev: pnpm -C frontend dev
  - Build: pnpm -C frontend build
  - Lint: pnpm -C frontend lint
  - Format: pnpm -C frontend format  | Check: pnpm -C frontend format:check
- Backend (Django + pytest)
  - Install deps: make -C backend install  (uses uv; Python 3.12)
  - Run dev server: make -C backend dev
  - Test all: make -C backend test  (uv run pytest)
  - Test single file/node: uv run -C backend pytest backend/test_math_solver.py::test_solver  (adapt path/test as needed)
  - Typecheck: make -C backend typecheck
  - Lint: make -C backend lint  | Format: make -C backend format

Code Style Guidelines
- Languages/Tooling: TypeScript (strict), React 19, Vite 6/7; Python 3.12 with Django, pytest, mypy, Ruff, Black.
- Imports (TS): enforce import-x order (builtin→external→internal→parent→sibling→index, alphabetized, no blank lines). Use type-only imports/exports (consistent-type-imports/exports). Avoid type-fest; prefer @extension/shared types. No unresolved/duplicate imports.
- ESLint: flow/eslint.config.ts and frontend/eslint.config.js are authoritative. Follow React Hooks rules, no prop-types, prefer const, arrow functions, newline-after-import, no deprecated imports. Prettier is final stylistic pass.
- Formatting: Prettier (JS/TS); Black (Python). Tailwind class sorting via prettier-plugin-tailwindcss in flow.
- Types & Naming (TS): explicit types on public APIs; camelCase for vars/functions, PascalCase for components/types; interfaces/types in singular nouns; avoid any; prefer generics and zod schemas where applicable.
- Python Style: Ruff (E,W,F,I,B,C4,UP), 100-char lines; Black 100; mypy strict with Django stubs. Use dataclasses/TypedDict as needed. Snake_case for functions/vars, PascalCase for classes.
- Error Handling: never swallow errors; in TS, surface via Result-like returns or throw with contextual message; in React, use error boundaries (shared/hoc/with-error-boundary). In Python, raise DRF APIException subclasses with clear messages; log with request IDs.
- Env/Secrets: never hardcode; use backend/.env and flow bash-scripts/copy_env.sh; respect .gitignore.

Editor/Agent Notes
- Node: >=22.15.1; package manager: pnpm@10.11.0. Run commands from repo root with -C to target subprojects.
- Tests discovery (pytest): backend/pyproject.toml config; run specific test with -k or node selection (file::TestClass::test_name).
- Husky/lint-staged (flow): Prettier + ESLint run on staged files.

Cursor/Copilot Rules
- No .cursor or Copilot rules detected in this repo at time of writing. If added later (e.g., .cursor/rules/, .cursorrules, .github/copilot-instructions.md), mirror their key points here.