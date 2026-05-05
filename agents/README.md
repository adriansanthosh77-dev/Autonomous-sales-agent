# Agents

This directory is reserved for agent prompts, routing policies, and orchestration notes that sit above the MCP tools.

In the MCP architecture, Claude should call stable business tools such as `fetch_high_intent_leads`, `send_followup_email`, and `trigger_background_sales_workflow` instead of embedding provider-specific Gmail, WhatsApp, Google Ads, or Iterable logic inside prompts.

