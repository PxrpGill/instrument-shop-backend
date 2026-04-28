# Instrument Shop Backend - Agent Guidelines

## Project Overview
Django 6.0.4 backend with Django Ninja API. Modular structure with apps in `apps/`.
Application runs in Docker.

## Documentation Index
- [Development Commands](.opencode/docs/development.md) - Docker, setup, server, database, testing, linting
- [Code Conventions](.opencode/docs/conventions.md) - Style, naming, Django/Ninja specifics, database guidelines
- [Common Pitfalls](.opencode/docs/pitfalls.md) - Lessons learned, frequent mistakes and solutions
- [Task Summary](.opencode/docs/task-summary.md) - Completed tasks, migrations, known issues

## Agent Usage Guidelines
To use agents effectively in this repository:

### Task Approach
1. **Read first, act second**: Always read relevant files before making changes
2. **Follow the todo list pattern**: Break complex tasks into specific, actionable items
3. **One task at a time**: Only mark one todo as `in_progress` at any moment
4. **Verify changes**: Run tests and linting after modifications

### Tool Selection
- Use `read`/`glob`/`grep` to understand code before editing
- Use `edit` for precise changes, `write` only when creating new files
- Use `bash` for running commands (tests, linting, server)
- Use `task` for complex multi-step operations requiring specialized agents

### Plan Management
- All plans should be written to `.opencode/plans/` directory (relative to project root)
- Plan files should be named according to the task (e.g., `10-tests.md` for task 10)
- Agents MUST write plans to `.opencode/plans/` before implementing tasks
- Use `bash` with `cat > .opencode/plans/<task-name>.md << 'EOF'` to write plans
- Plans should follow: Task Overview, Current Coverage Analysis, Detailed Plan, Implementation Order, Files to Modify, Completion Criteria

### Best Practices
- Follow project's code style guidelines (see [Code Conventions](.opencode/docs/conventions.md))
- Run `python -m black --check .` and `python -m isort --check-only .` before completing work
- Test changes with appropriate test commands
- Keep changes focused and minimal
- Never hardcode secrets; use environment variables
- Check `conftest.py` for available pytest fixtures before creating new ones

## Automatic Agent Invocation for Backlog Tasks
When working on backlog tasks, automatically determine and invoke the appropriate subagent:

1. **Read the task file** from `backlog/mvp/tasks/` directory
2. **Analyze content** to determine task type:
   - `model`, `migration`, `schema`, `field`, `database` → `database-normalization-architect`
   - `controller`, `api`, `endpoint`, `service`, `view` → `senior-backend-django-ninja`
   - `test`, `pytest`, `testing`, `coverage` → `senior-python-tester`
   - `docker`, `ci`, `cd`, `deployment`, `infrastructure` → `senior-devops`
   - `commit`, `git`, `pr`, `pull request` → `git-commit`
   - Code exploration/research (no code changes) → `explore`

3. **Invoke the agent** with detailed prompt containing:
   - Full task content from the backlog file
   - Expected deliverable
   - Reference to project code style from this file

4. **Execute and verify** when agent completes

## Common Workflows
**Adding a new feature:**
1. Read relevant models, services, and API files
2. Create/update models (if needed) and run migrations
3. Update service layer with business logic
4. Create/update API endpoints with proper validation and permissions
5. Add tests covering the new functionality (unit and API tests)
6. Run full test suite to ensure no regressions

**Fixing a bug:**
1. Reproduce the bug and locate relevant code
2. Read the problematic code and related tests
3. Create a failing test that reproduces the issue
4. Fix the bug with minimal changes
5. Verify the fix resolves the issue and doesn't break other tests

**Refactoring:**
1. Identify the code to refactor and its usage
2. Ensure adequate test coverage exists
3. Make small, incremental changes
4. Run tests frequently to ensure behavior is preserved
5. Update any affected documentation
