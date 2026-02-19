# Reflection Report — Beaver's Choice Paper Company Multi-Agent System

## 1. Agent Workflow Diagram Explanation

### 1.1 System Overview

The multi-agent system for Beaver's Choice Paper Company is built using the **smolagents** framework with `ToolCallingAgent` instances backed by the `gpt-4o-mini` model. The architecture consists of **five agents**: one orchestrator and four specialised worker agents. The system processes customer paper-supply requests end-to-end—from inventory lookup through quoting, sales recording, and final response composition.

### 1.2 Agent Roles and Responsibilities

| Agent | Role | Key Tools |
|---|---|---|
| **Orchestrator** | Customer-facing coordinator. Runs a deterministic four-step pipeline (Inventory → Quoting → Sales → Response) for every request. Synthesises worker outputs into a warm, professional reply that never reveals internal details. | `search_past_quotes`, `check_all_inventory` |
| **Inventory Agent** | Checks current stock levels for individual items or the complete catalog, flags items below their minimum-stock threshold for reorder, estimates supplier delivery lead times, and looks up unit pricing. | `check_all_inventory`, `check_item_stock`, `get_delivery_estimate`, `get_item_unit_price` |
| **Quoting Agent** | Generates competitive price quotes using tiered bulk discounts (5 % for 100-499 units up to 20 % for 5 000+ units). Searches historical quote data for pricing precedents to ensure consistency. | `search_past_quotes`, `check_item_stock`, `check_all_inventory`, `get_item_unit_price` |
| **Sales Agent** | Records each fulfilled line item as a separate sales transaction in the database using `record_sale`. Verifies stock before selling, handles partial fulfillment, and can reorder from the supplier via `record_stock_order`. | `record_sale`, `record_stock_order`, `check_cash`, `check_item_stock`, `get_delivery_estimate`, `get_item_unit_price` |
| **Business Advisor** | Runs once after all requests are processed. Analyses revenue trends, inventory health, and top sellers, then provides two actionable strategic recommendations. | `get_financial_summary`, `check_cash`, `check_all_inventory` |

### 1.3 Decision-Making Process for the Architecture

The architecture was guided by three design principles:

1. **Separation of concerns** — Each agent owns a single domain (inventory, pricing, fulfillment, analysis) so that prompts stay focused and tool access is scoped to only what is needed. This prevents tool-call confusion and makes the system easier to debug.

2. **Deterministic pipeline over autonomous routing** — Rather than letting the orchestrator decide which agents to call dynamically, the `process_customer_request` function enforces a fixed four-step sequence (Inventory → Quoting → Sales → Compose). This guarantees every request goes through inventory verification *before* quoting and quoting *before* sales, eliminating race conditions or skipped steps.

3. **Reuse of starter-code helper functions** — Every tool is a thin wrapper around one or more of the seven helper functions provided in the starter file (`get_all_inventory`, `get_stock_level`, `get_supplier_delivery_date`, `get_cash_balance`, `generate_financial_report`, `create_transaction`, `search_quote_history`). This keeps business logic centralised and testable outside the agent layer.

### 1.4 Data Flow

```
Customer CSV → Orchestrator
  │
  ├─1. Inventory Agent  ← reads inventory & transactions tables
  │    └─ returns stock levels, prices, reorder flags
  │
  ├─2. Quoting Agent    ← reads quotes & inventory tables
  │    └─ returns itemised quote with discounts
  │
  ├─3. Sales Agent      ← writes to transactions table
  │    └─ returns transaction confirmations
  │
  └─4. Orchestrator composes customer-facing response
       └─> saved to test_results.csv
After all requests:
  └─5. Business Advisor ← reads transactions & inventory
        → prints strategic analysis
```

---

## 2. Evaluation Results Discussion

### 2.1 Test Summary

The system was evaluated against all **20 customer requests** in `quote_requests_sample.csv`. Results are recorded in `test_results.csv`.

| Metric | Value |
|---|---|
| Total requests processed | 20 |
| Requests resulting in a cash balance change | **7** (Requests 3, 5, 6, 7, 10, 14, 15) |
| Requests fully or partially fulfilled | ~8–10 (items sold and transactions recorded) |
| Requests not fulfilled | ~10–12 (items out of stock or not in catalog) |
| Starting cash balance | $45,124.70 |
| Final cash balance | $46,423.35 |
| Net revenue generated | **$1,298.65** |
| Starting inventory value | $4,940.30 |
| Final inventory value | $3,701.65 |

### 2.2 Strengths

1. **Reliable sales recording** — When items were available, the Sales Agent correctly called `record_sale` for each line item, producing verifiable transaction records and real cash-balance movement. Seven distinct requests produced measurable revenue, comfortably exceeding the three-request minimum.

2. **Honest partial fulfillment** — The system transparently handled cases where only a subset of requested items could be supplied (e.g., Request 7 for the business owner's exhibition: 87 of 500 glossy sheets fulfilled, 148 of 200 cardstock sheets fulfilled, poster paper fully filled). Customers received clear item-by-item breakdowns.

3. **Appropriate rejection of unfulfillable orders** — Requests for items not in the catalog (e.g., balloons, A3 paper, tickets) were correctly declined with professional explanations and alternative suggestions, avoiding promise-then-fail scenarios.

4. **Professional, customer-appropriate responses** — Outputs consistently included greetings, itemised pricing, discount explanations, delivery estimates, and sign-offs. No internal agent names, system architecture details, or profit margins were leaked.

5. **Bulk discount strategy** — The Quoting Agent applied tiered discounts consistently, matching the defined tiers (5 %–20 %) and explaining each to the customer.

6. **Terminal animation** — The colour-coded, real-time console output made it easy to follow which agent was active and what step was executing, aiding development and debugging.


## 4. Files to Submit

| File                        | Description                                                                       |
|-----------------------------|-----------------------------------------------------------------------------------|
| `project_starter.py`        | Complete implementation of the multi-agent system using smolagents                |
| `test_results.csv`          | Evaluation results from processing all 20 requests in `quote_requests_sample.csv` |
| `reflection_report.md`      | This file - Reflective report                                                     |
| `Inventtory Management.png` | Agent flow diagram                                                                |
