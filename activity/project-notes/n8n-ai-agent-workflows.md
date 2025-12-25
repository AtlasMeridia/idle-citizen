# n8n AI Agent Workflows — Practical Guide

*Created: 2025-12-25 (Session 39)*
*Context: Supporting Kenny's Telegram LLM Hub project*

---

## Current Status (from memory)

Kenny has:
- n8n running via Docker on port 5678 with Cloudflare tunnel
- Telegram bot created
- n8n MCP server added
- Workflow JSON at `n8n/workflows/telegram-router.json`

**Blocker:** Workflow import failing, suspected issue with `@n8n/n8n-nodes-langchain.lmChatAnthropic` node using `__rl` (resource locator) format for `modelId`.

---

## The `__rl` Resource Locator Format

n8n uses an internal resource locator format (`__rl`) in workflow JSON for parameters that reference dynamic resources. This format changed in recent versions and can cause import failures when:

1. Workflow was exported from a different n8n version
2. The JSON was hand-crafted without matching the expected format
3. Node versions have changed internal parameter structures

### Solution: Recreate via MCP Instead of Import

Given the n8n MCP server is installed, the cleanest approach is to **build the workflow programmatically** rather than trying to fix the JSON import.

The n8n MCP tools available:
- `search_workflows` — list existing workflows
- `get_workflow_details` — inspect workflow structure
- `execute_workflow` — run a workflow

For creation, use the n8n REST API directly or the UI. The MCP is primarily for execution and inspection.

---

## Claude + n8n AI Agent Architecture

### Recommended Node Chain for Telegram Bot

```
[Telegram Trigger]
    → [AI Agent Node]
        ├── Chat Model: Anthropic (Claude)
        ├── Memory: Window Buffer Memory
        └── Tools: (as needed)
    → [Telegram Send Message]
```

### Key Configuration Points

**Anthropic Chat Model Node:**
- Model selection: Claude 3.5 Sonnet (haiku for speed, opus for complex)
- Temperature: 0.7 for conversational, lower for precision
- Max tokens: Set based on response needs (1024 typical for chat)

**Memory:**
- Window Buffer Memory: Keeps last N conversation turns
- Alternative: Conversation Chain for simpler use cases

**Known Issue:** Anthropic's "Enable Thinking" feature conflicts with tool use due to message formatting. Avoid combining thinking mode with tools for now (see [GitHub Issue #15715](https://github.com/n8n-io/n8n/issues/15715)).

---

## Workflow Templates to Reference

### Claude 3.7 Sonnet AI Chatbot
[n8n Template #4036](https://n8n.io/workflows/4036-claude-37-sonnet-ai-chatbot-agent-with-anthropic-web-search-and-think-functions/)

Features:
- Web search for factual queries
- "Think" function for internal reasoning
- Memory buffer for conversation history
- System prompt with ethics/formatting rules

### Claude Sonnet 4 / Opus 4 Router
[n8n Template #4399](https://n8n.io/workflows/4399-anthropic-ai-agent-claude-sonnet-4-and-opus-4-with-think-and-web-search-tool/)

Features:
- Dynamic model selection based on query complexity
- Routes routine → Sonnet, complex → Opus
- Cost optimization built-in

These templates can be imported and modified rather than building from scratch.

---

## Debugging Import Failures

If you need to fix a workflow JSON:

1. **Check node versions:** Ensure node types match your n8n version
   ```bash
   # In n8n container
   docker exec -it n8n n8n list:workflow
   ```

2. **Validate JSON structure:** n8n expects:
   ```json
   {
     "name": "Workflow Name",
     "nodes": [...],
     "connections": {...},
     "settings": {...}
   }
   ```

3. **Strip problematic fields:** If `__rl` format is wrong, try removing the entire parameter and reconfiguring in UI after import

4. **Use n8n CLI for import:**
   ```bash
   docker exec -it n8n n8n import:workflow --input=/path/to/workflow.json
   ```

---

## Quick Start: Building in UI Instead

Since import is problematic, here's a manual build path:

1. **Create Telegram credential:**
   - Settings → Credentials → Add New
   - Type: Telegram
   - Add Bot Token from BotFather

2. **Create Anthropic credential:**
   - Type: Anthropic
   - Add API Key

3. **Build the chain:**
   - Add Telegram Trigger node
   - Add AI Agent node
   - Connect Anthropic Chat Model sub-node
   - Add Memory sub-node
   - Add Telegram node for response
   - Wire: Trigger → Agent → Send Message

4. **Configure agent:**
   - System prompt: Define bot personality
   - Memory: Set context window size
   - Output parser: Text (for Telegram)

---

## References

- [n8n Anthropic Chat Model Docs](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatanthropic/)
- [n8n Workflow Import/Export Guide](https://docs.n8n.io/workflows/export-import/)
- [n8n-MCP GitHub](https://github.com/czlonkowski/n8n-mcp) — 543 nodes available via MCP
- [GitHub Issue: Thinking + Tools Conflict](https://github.com/n8n-io/n8n/issues/15715)

---

## Recommendation

Given the import issues, I'd suggest:

1. **Abandon the existing JSON** temporarily
2. **Build fresh in the UI** using the node chain above
3. **Use MCP for execution** once the workflow is created
4. **Export the working workflow** for backup

This sidesteps the `__rl` format issues entirely and gives you a working baseline to iterate from.
