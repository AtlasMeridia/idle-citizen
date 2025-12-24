# Headless Atlas Activity

Develop and improve Kenny's personal website.

## Project Location

**Codebase:** `/Users/ellis/Projects/headless-atlas`

**Live site:** https://atlas.kennypliu.com/

## Tech Stack

- Next.js 16 (App Router, React 19)
- Tailwind CSS v4 with CSS custom properties
- Ghost Content API (headless CMS)
- TypeScript
- Deployed on Vercel

## How to Execute

1. Read the project's `CLAUDE.md` for detailed architecture and patterns
2. Check for any open issues or TODOs in the codebase
3. Pick a task:
   - Bug fixes
   - Design system refinements
   - Performance improvements
   - New components or features
   - Code cleanup and refactoring
4. Make changes following the project's established patterns
5. Run `npm run type-check` to verify no TypeScript errors
6. Commit changes to the headless-atlas repo

## What Makes Good Contributions

- **Follow the design system** — All styling via `styles/tokens.css` tokens
- **Respect existing patterns** — Read existing components before creating new ones
- **Keep it minimal** — Don't over-engineer or add unnecessary complexity
- **Test your changes** — At minimum, type-check passes

## Constraints

- Don't modify environment variables or deployment config
- Don't push to main (Kenny will review and deploy)
- Keep commits atomic and well-described

## Common Tasks

### Design refinements
Check `dev/` folder for design notes and references. Update tokens.css + style guide together.

### New components
Follow patterns in `components/`. Use TypeScript interfaces, semantic HTML, mobile-first responsive.

### Content/API changes
Ghost API client is in `lib/ghost.ts`. Types in `types/ghost.ts`.

## Success Criteria

- Code follows project patterns
- Type-check passes
- Changes are committed with clear messages
- No breaking changes to existing functionality
