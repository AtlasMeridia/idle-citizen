# Claude Skills Development Guide

*A practical guide to building Skills for Claude Code and Claude.ai. Focus: local development workflow.*

---

## Overview

Skills are filesystem-based modules that extend Claude's capabilities without modifying the core system prompt. They're loaded on-demand when contextually relevant, keeping the main context lean.

**Key insight:** Skills are "on-demand prompt expansion" — executable knowledge packages that teach Claude specialized workflows.

---

## Skill Structure

A skill is a folder containing a `SKILL.md` file plus optional resources:

```
my-skill/
├── SKILL.md          # Required: instructions + YAML frontmatter
├── scripts/          # Optional: Python/Bash scripts Claude can run
├── references/       # Optional: documentation loaded into context
└── assets/           # Optional: templates, binary files
```

### SKILL.md Format

Two parts: YAML frontmatter (metadata) + markdown content (instructions).

```yaml
---
name: my-skill
description: Clear description of what this skill does AND when to use it.
---

# My Skill

Instructions Claude will follow when this skill is active.

## Core Workflow
1. Step one
2. Step two
3. Step three

## Examples

### Example: Common use case
[Walkthrough of a typical invocation]

## Guidelines
- Preference one
- Preference two
```

**Required frontmatter fields:**
- `name` — Unique identifier (lowercase, hyphens for spaces)
- `description` — Must include both **what** the skill does AND **when** to use it

---

## Where Skills Live

### Claude Code (local development)

| Location | Scope |
|----------|-------|
| `~/.claude/skills/my-skill/` | User-scoped (available in all projects) |
| `.claude/skills/my-skill/` | Project-scoped (only this project) |
| Plugin skills subdirectory | Plugin-scoped |

### Claude.ai

- Built-in skills for paid plans
- Custom skills can be uploaded

### Claude API

- Skills API supports custom skill upload
- Same SKILL.md format

---

## How Skills Are Invoked

**Model-invoked, not user-invoked.**

Claude receives a `Skill` tool with all available skills listed in an `<available_skills>` section. When your request matches a skill's description, Claude autonomously decides to invoke it.

This is different from slash commands (user-invoked with `/command`).

**Invocation flow:**
1. Claude evaluates if a skill matches the current task
2. Claude calls the Skill tool with the skill name
3. Tool response returns the full SKILL.md content (without frontmatter)
4. Claude follows the skill's instructions in the current context

---

## Best Practices

### 1. Keep SKILL.md Concise

Under 5,000 words. Heavy documentation goes in `references/` for on-demand loading.

### 2. Progressive Disclosure

Structure like a well-organized manual:
- **SKILL.md** — Quick reference, core workflow
- **references/** — Detailed documentation Claude can load when needed
- **scripts/** — Automation that doesn't bloat context

### 3. Write Good Descriptions

The description determines whether Claude invokes the skill. Include:
- What the skill does
- When to use it (trigger conditions)

**Good:** `Extract and analyze text from PDF documents. Use when users ask to process or read PDFs.`

**Bad:** `PDF handling`

### 4. Bundle Scripts for Automation

Put Python/Bash scripts in `scripts/`. Claude can execute them without loading their code into context.

```python
# scripts/validate.py
#!/usr/bin/env python3
"""Validate output format."""
import sys
import json

# Script logic here
```

Reference in SKILL.md:
```markdown
## Validation
Run `scripts/validate.py` to check output format.
```

### 5. Use References for Context

Large documentation lives in `references/`. Claude loads these when needed.

```
references/
├── api-spec.md
├── examples/
│   ├── simple.json
│   └── complex.json
└── troubleshooting.md
```

Reference in SKILL.md:
```markdown
## Reference
For API details, load `references/api-spec.md`.
```

---

## Example: Simple Skill

A skill that helps write Git commit messages following a specific convention:

**~/.claude/skills/commit-style/SKILL.md**

```yaml
---
name: commit-style
description: Format commit messages following Kenny's conventions. Use when creating git commits.
---

# Commit Style Guide

Format all commit messages following these patterns.

## Format

```
<type>: <description>

[optional body]

🤖 Generated with Claude Code
```

## Types

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation only
- `refactor:` — Code change without feature/fix
- `chore:` — Maintenance tasks

## Rules

1. Description is imperative mood ("add feature" not "added feature")
2. No period at end of description
3. Body wraps at 72 characters
4. Always include the robot emoji signature

## Example

```
feat: add user authentication flow

Implement OAuth2 login with GitHub provider. Stores tokens
in encrypted local storage with 7-day expiration.

🤖 Generated with Claude Code
```
```

---

## Example: Skill with Scripts

A skill that generates database migrations:

**~/.claude/skills/db-migrate/SKILL.md**

```yaml
---
name: db-migrate
description: Generate and apply database migrations. Use when schema changes are needed.
---

# Database Migration Skill

Create migrations for schema changes.

## Workflow

1. Analyze current schema (`scripts/schema-diff.py`)
2. Generate migration file
3. Preview SQL with `scripts/preview-migration.py`
4. Apply with `scripts/apply-migration.py`

## Migration Naming

Format: `YYYYMMDD_HHMMSS_description.sql`

## Supported Operations

- CREATE TABLE
- ALTER TABLE (add/modify/drop columns)
- CREATE INDEX
- DROP TABLE (with confirmation)

## Safety

- Never drop production tables without explicit confirmation
- Always generate rollback SQL
- Validate foreign key references
```

**db-migrate/scripts/schema-diff.py**

```python
#!/usr/bin/env python3
"""Compare current schema against last known state."""
import sqlite3
import json
from pathlib import Path

def main():
    # Implementation here
    pass

if __name__ == '__main__':
    main()
```

---

## Developing Skills Locally

### Quick Start

```bash
# Create skill directory
mkdir -p ~/.claude/skills/my-skill

# Create minimal SKILL.md
cat > ~/.claude/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: Description of my skill. When to use it.
---

# My Skill

Instructions here.
EOF
```

### Testing Workflow

1. Create/edit skill in `~/.claude/skills/`
2. Start new Claude Code session (skills load on session start)
3. Ask Claude something that should trigger the skill
4. Iterate based on behavior

**Tip:** Skills are discovered at session start. If you modify a skill, you may need to restart the session to pick up changes.

### Debugging

If a skill isn't being invoked:
- Check the `description` — is it clear about when to use the skill?
- Verify the skill is in the correct location
- Look for YAML syntax errors in frontmatter
- Try explicitly mentioning the skill's domain in your prompt

---

## Official Resources

- [Agent Skills Documentation](https://code.claude.com/docs/en/skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills) — 26k+ stars, templates and examples
- [Building Skills for Claude Code](https://claude.com/blog/building-skills-for-claude-code)
- [Skills Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)

---

## Recommendations for Kenny

Given `~/Projects/agent-skills-exploration/` exists but is empty:

1. **Start with one practical skill** — e.g., a commit-style skill or project-specific workflow
2. **Use user-scoped location** — `~/.claude/skills/` for skills you want everywhere
3. **Keep them simple initially** — SKILL.md only, add scripts later
4. **Document what works** — The `notes/` folder in agent-skills-exploration is perfect for this

**Suggested first skill:** A "project-context" skill that summarizes project structure and conventions when starting work on a codebase. This is useful across all projects.

---

*Last updated: 2025-12-24*
