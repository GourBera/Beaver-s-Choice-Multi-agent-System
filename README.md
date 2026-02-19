# Beaver's Choice Paper Company — Multi-Agent System

A multi-agent system built with **smolagents** and **GPT-4o-mini** that automates inventory management, quote generation, and order fulfillment for a fictional paper supply company.

---

## Architecture

The system uses **5 agents** orchestrated in a deterministic pipeline:

| Agent | Role |
|---|---|
| **Orchestrator** | Customer-facing coordinator — delegates tasks and composes final responses |
| **Inventory Agent** | Checks stock levels, flags reorders, estimates supplier delivery times |
| **Quoting Agent** | Generates competitive quotes with tiered bulk discounts (5%–20%) |
| **Sales Agent** | Records sales transactions, verifies stock, handles partial fulfillment |
| **Business Advisor** | Post-run financial analysis and strategic recommendations |

### Processing Pipeline

```
Customer Request → Orchestrator
  ├─1. Inventory Agent  (check stock & prices)
  ├─2. Quoting Agent    (generate quote with discounts)
  ├─3. Sales Agent      (record transactions)
  └─4. Orchestrator     (compose customer response)
       → test_results.csv
After all requests:
  └─5. Business Advisor (strategic analysis)
```

### Tools → Helper Function Mapping

All tools wrap the provided starter-code helper functions:

| Tool | Helper Function(s) |
|---|---|
| `check_all_inventory` | `get_all_inventory()` |
| `check_item_stock` | `get_stock_level()` |
| `get_delivery_estimate` | `get_supplier_delivery_date()` |
| `get_item_unit_price` | SQL query on inventory table |
| `search_past_quotes` | `search_quote_history()` |
| `record_sale` | `create_transaction('sales')` |
| `record_stock_order` | `create_transaction('stock_orders')` |
| `check_cash` | `get_cash_balance()` |
| `get_financial_summary` | `generate_financial_report()` |

---

## Project Structure

```
project/
├── project_starter.py            # Full implementation (agents, tools, pipeline)
├── agent_workflow_diagram.md     # Mermaid code for the architecture diagram
├── reflection_report.md          # Evaluation results and improvement suggestions
├── test_results.csv              # Output from processing 20 customer requests
├── requirements.txt              # Python dependencies
├── Inventory Management.png      # Rendered workflow diagram
└── munder_difflin.db             # SQLite database (generated at runtime)
```

---

## Setup & Usage

### Prerequisites

- Python 3.8+
- An OpenAI-compatible API key

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure API Key

Create a `config.env` file in the `project/` directory:

```
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://openai.vocareum.com/v1
```

### Run

```bash
python project_starter.py
```

This will:
1. Initialise the SQLite database with inventory and historical data
2. Process all 20 customer requests from `quote_requests_sample.csv`
3. Save results to `test_results.csv`
4. Print a final financial report and business advisor analysis

---

## Evaluation Highlights

| Metric | Value |
|---|---|
| Requests processed | 20 |
| Cash balance changes | 7 |
| Net revenue generated | $1,298.65 |
| Starting cash | $45,124.70 |
| Final cash | $46,423.35 |

See [reflection_report.md](project/reflection_report.md) for full analysis.

---

## Workflow Diagram

The Mermaid source is in [agent_workflow_diagram.md](project/agent_workflow_diagram.md).

![Workflow Diagram](project/Inventory%20Management.png)


---

## Framework

Built with [smolagents](https://huggingface.co/docs/smolagents) using `ToolCallingAgent` pattern.
