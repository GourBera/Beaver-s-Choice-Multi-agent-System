import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

import sys
import json
from smolagents import (
    tool,
    ToolCallingAgent,
    CodeAgent,
    OpenAIServerModel,
)

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# Multi Agent code Implementation
########################
########################
########################


# Environment Setup and Model Initialization
dotenv.load_dotenv("config.env")

model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    api_base=os.getenv("OPENAI_BASE_URL"),
)


# Terminal Animation - provides colored, real-time visibility 
AGENT_COLORS = {
    "orchestrator": "\033[95m",   # Magenta
    "inventory":    "\033[94m",   # Blue
    "quoting":      "\033[93m",   # Yellow
    "sales":        "\033[92m",   # Green
    "advisor":      "\033[96m",   # Cyan
    "reset":        "\033[0m",
    "bold":         "\033[1m",
}

def print_agent_banner(agent_name: str, action: str) -> None:
    """Display a colored banner indicating the active agent and its current action."""
    color = AGENT_COLORS.get(agent_name.lower(), AGENT_COLORS["reset"])
    reset = AGENT_COLORS["reset"]
    bold = AGENT_COLORS["bold"]
    print(f"\n{color}{bold}{'─' * 60}")
    print(f"[{agent_name.upper()} AGENT] {action}")
    print(f"{'─' * 60}{reset}")
    sys.stdout.flush()


def print_step(agent_name: str, message: str) -> None:
    """Print a colored progress message for an agent's internal step."""
    color = AGENT_COLORS.get(agent_name.lower(), AGENT_COLORS["reset"])
    reset = AGENT_COLORS["reset"]
    print(f"{color}  > {message}{reset}")
    sys.stdout.flush()


def print_section_header(title: str) -> None:
    """Print a prominent section header for major workflow transitions."""
    bold = AGENT_COLORS["bold"]
    reset = AGENT_COLORS["reset"]
    print(f"\n{bold}{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}{reset}")
    sys.stdout.flush()


# Tool Definitions - Each tool wraps one or more of the provided helper functions from the starter
# Tools for inventory agent
@tool
def check_all_inventory(as_of_date: str) -> str:
    """Check the complete inventory of all paper items currently in stock.
    Returns every item with its quantity that has positive stock as of the date.

    Args:
        as_of_date: Date in YYYY-MM-DD format to check inventory snapshot.

    Returns:
        A formatted inventory listing with item names and stock counts.
    """
    print_step("inventory", f"Checking full inventory as of {as_of_date}")
    inventory = get_all_inventory(as_of_date)
    if not inventory:
        return "No inventory items found as of the given date."
    lines = ["Current Inventory (items with positive stock):"]
    for item_name, stock in sorted(inventory.items()):
        lines.append(f"  - {item_name}: {int(stock)} units")
    lines.append(f"\nTotal distinct items in stock: {len(inventory)}")
    return "\n".join(lines)


@tool
def check_item_stock(item_name: str, as_of_date: str) -> str:
    """Check the stock level of a specific item and whether it needs reordering.
    Also returns the unit price and minimum stock threshold when available.

    Args:
        item_name: Exact name of the item (e.g., 'A4 paper', 'Cardstock').
        as_of_date: Date in YYYY-MM-DD format for the stock snapshot.

    Returns:
        Stock level details including reorder status.
    """
    print_step("inventory", f"Checking stock for '{item_name}' as of {as_of_date}")
    result_df = get_stock_level(item_name, as_of_date)
    stock = int(result_df["current_stock"].iloc[0])
    inv_df = pd.read_sql(
        "SELECT min_stock_level, unit_price FROM inventory WHERE item_name = :name",
        db_engine,
        params={"name": item_name},
    )
    if not inv_df.empty:
        min_level = int(inv_df["min_stock_level"].iloc[0])
        unit_price = float(inv_df["unit_price"].iloc[0])
        needs_reorder = stock < min_level
        status = " -- BELOW MINIMUM, REORDER RECOMMENDED" if needs_reorder else " -- Stock OK"
        return (
            f"{item_name}: {stock} units in stock | "
            f"Min threshold: {min_level} | Unit price: ${unit_price:.2f}{status}"
        )
    return f"{item_name}: {stock} units in stock (not in managed inventory catalog)"


@tool
def get_delivery_estimate(order_date: str, quantity: int) -> str:
    """Estimate when a supplier delivery will arrive based on order size.
    Lead times: 10 or fewer units = same day, 11-100 = +1 day,
    101-1000 = +4 days, more than 1000 = +7 days.

    Args:
        order_date: The date the order would be placed, in YYYY-MM-DD format.
        quantity: Number of units to be ordered from the supplier.

    Returns:
        The estimated delivery date string.
    """
    print_step("inventory", f"Estimating delivery for {quantity} units from {order_date}")
    delivery = get_supplier_delivery_date(order_date, quantity)
    return f"Supplier delivery for {quantity} units ordered on {order_date}: expected by {delivery}"


@tool
def get_item_unit_price(item_name: str) -> str:
    """Look up the catalog unit price and category for an item.
    Searches inventory first, then the full product catalog as fallback.

    Args:
        item_name: Name or partial name of the item to look up.

    Returns:
        Pricing information for matching items.
    """
    inv_df = pd.read_sql(
        "SELECT * FROM inventory WHERE LOWER(item_name) LIKE :name",
        db_engine,
        params={"name": f"%{item_name.lower()}%"},
    )
    if not inv_df.empty:
        results = []
        for _, row in inv_df.iterrows():
            results.append(
                f"  {row['item_name']}: ${row['unit_price']:.2f}/unit "
                f"({row['category']}) [IN STOCK]"
            )
        return "Matching items in inventory:\n" + "\n".join(results)
    matches = [s for s in paper_supplies if item_name.lower() in s["item_name"].lower()]
    if matches:
        results = []
        for item in matches:
            results.append(
                f"  {item['item_name']}: ${item['unit_price']:.2f}/unit "
                f"({item['category']}) [NOT CURRENTLY STOCKED]"
            )
        return "Catalog matches (not in current inventory):\n" + "\n".join(results)
    return f"No item matching '{item_name}' found in inventory or product catalog."


# Tools for quoting agent
@tool
def search_past_quotes(search_terms: str) -> str:
    """Search historical quote records to find relevant pricing precedents.
    Helps ensure consistent and competitive pricing for similar orders.

    Args:
        search_terms: Comma-separated keywords (e.g., 'cardstock, ceremony, large').

    Returns:
        Matching historical quotes with amounts, explanations, and metadata.
    """
    print_step("quoting", f"Searching quote history for: {search_terms}")
    terms = [t.strip() for t in search_terms.split(",")]
    quotes = search_quote_history(terms, limit=5)
    if not quotes:
        return "No matching historical quotes found for those terms."
    lines = [f"Found {len(quotes)} relevant historical quote(s):"]
    for i, q in enumerate(quotes, 1):
        lines.append(f"\n  Quote #{i}:")
        lines.append(f"    Total Amount: ${q['total_amount']}")
        lines.append(
            f"    Job: {q['job_type']}  |  Size: {q['order_size']}  "
            f"|  Event: {q['event_type']}"
        )
        explanation = q["quote_explanation"][:300]
        lines.append(f"    Explanation: {explanation}")
    return "\n".join(lines)

# Tools for Sales or Transaction
@tool
def record_sale(item_name: str, quantity: int, total_price: float, sale_date: str) -> str:
    """Record a completed sale in the database. Deducts stock and adds revenue.
    Only call this AFTER confirming the item is in stock with sufficient quantity.

    Args:
        item_name: Exact item name matching the inventory (e.g., 'A4 paper').
        quantity: Number of units sold.
        total_price: Total sale price in dollars.
        sale_date: Date of sale in YYYY-MM-DD format.

    Returns:
        Confirmation message with the transaction ID.
    """
    print_step("sales", f"Recording sale: {quantity} x {item_name} for ${total_price:.2f}")
    txn_id = create_transaction(item_name, "sales", quantity, total_price, sale_date)
    return (
        f"Sale recorded (Txn #{txn_id}): "
        f"{quantity} units of '{item_name}' sold for ${total_price:.2f}"
    )


@tool
def record_stock_order(
    item_name: str, quantity: int, total_cost: float, order_date: str
) -> str:
    """Record a stock reorder from the supplier. Adds inventory and deducts cash.
    Use when stock falls below minimum threshold or to prepare for large orders.

    Args:
        item_name: Exact item name to restock.
        quantity: Number of units to order from supplier.
        total_cost: Total purchase cost in dollars.
        order_date: Date of the stock order in YYYY-MM-DD format.

    Returns:
        Confirmation message with the transaction ID.
    """
    print_step("sales", f"Recording restock: {quantity} x {item_name} for ${total_cost:.2f}")
    txn_id = create_transaction(item_name, "stock_orders", quantity, total_cost, order_date)
    return (
        f"Stock order recorded (Txn #{txn_id}): "
        f"{quantity} units of '{item_name}' purchased for ${total_cost:.2f}"
    )


@tool
def check_cash(as_of_date: str) -> str:
    """Check the company's current cash balance (total sales minus total stock costs).

    Args:
        as_of_date: Date in YYYY-MM-DD format.

    Returns:
        The current cash balance formatted as a string.
    """
    print_step("sales", f"Checking cash balance as of {as_of_date}")
    balance = get_cash_balance(as_of_date)
    return f"Cash balance as of {as_of_date}: ${balance:,.2f}"

# Tools for Reporting and Advisor
@tool
def get_financial_summary(as_of_date: str) -> str:
    """Generate a full financial report: cash, inventory valuation, total assets,
    and the top-selling products by revenue.

    Args:
        as_of_date: Date in YYYY-MM-DD format for the report cutoff.

    Returns:
        Comprehensive financial report as a formatted string.
    """
    print_step("advisor", f"Generating financial report for {as_of_date}")
    report = generate_financial_report(as_of_date)
    lines = [
        f"Financial Report ({report['as_of_date']})",
        f"  Cash Balance:     ${report['cash_balance']:>12,.2f}",
        f"  Inventory Value:  ${report['inventory_value']:>12,.2f}",
        f"  Total Assets:     ${report['total_assets']:>12,.2f}",
    ]
    if report["top_selling_products"]:
        lines.append("\n  Top Selling Products:")
        for p in report["top_selling_products"]:
            try:
                units = int(p['total_units'])
            except (TypeError, ValueError):
                units = 0
            try:
                rev = float(p['total_revenue'])
            except (TypeError, ValueError):
                rev = 0.0
            lines.append(
                f"    - {p['item_name']}: {units} units, "
                f"${rev:,.2f} revenue"
            )
    lines.append("\n  Inventory Breakdown (top 10 by value):")
    sorted_inv = sorted(
        report["inventory_summary"],
        key=lambda x: float(x["value"]) if x["value"] is not None else 0.0,
        reverse=True,
    )
    for item in sorted_inv[:10]:
        try:
            stock = int(item['stock'])
        except (TypeError, ValueError):
            stock = 0
        try:
            price = float(item['unit_price'])
        except (TypeError, ValueError):
            price = 0.0
        try:
            val = float(item['value'])
        except (TypeError, ValueError):
            val = 0.0
        lines.append(
            f"    - {item['item_name']}: {stock} units "
            f"@ ${price:.2f} = ${val:,.2f}"
        )
    return "\n".join(lines)


# ===================================================================================
# Agen Creation
# 1. Inventory Agent    – stock checking, reorder assessment, delivery estimates
# 2. Quoting Agent      – competitive pricing based on history and discounts
# 3. Sales Agent        – transaction processing and order fulfillment
# 4. Business Advisor   – financial analysis and strategic recommendations
# 5. Orchestrator       – customer-facing coordinator that delegates to 1-4
# ===================================================================================

# Agent 1: Inventory Agent
inventory_agent = ToolCallingAgent(
    tools=[check_all_inventory, check_item_stock, get_delivery_estimate, get_item_unit_price],
    model=model,
    name="inventory_agent",
    description=(
        "Manages inventory: checks stock levels for all items or specific items, "
        "assesses whether items need reordering based on minimum thresholds, "
        "estimates supplier delivery times, and looks up item pricing. "
        "Use this agent when you need to know what items are available and in "
        "what quantities."
    ),
    instructions=(
        "You are the Inventory Manager for Beaver's Choice Paper Company.\n"
        "Your responsibilities:\n"
        "1. Check current stock levels accurately using check_item_stock or check_all_inventory\n"
        "2. Flag items that are below their minimum stock threshold for reorder\n"
        "3. Estimate supplier delivery timelines using get_delivery_estimate\n"
        "4. Look up item pricing using get_item_unit_price\n\n"
        "Always provide precise numbers. When an item is not found in inventory, "
        "state clearly that it is not currently stocked. Do not guess stock levels."
    ),
    max_steps=6,
)

# Agent 2: Quoting Agent
quoting_agent = ToolCallingAgent(
    tools=[search_past_quotes, check_item_stock, check_all_inventory, get_item_unit_price],
    model=model,
    name="quoting_agent",
    description=(
        "Generates competitive price quotes for customer orders. Uses historical "
        "quote data and applies bulk discount strategies. Checks item availability "
        "before quoting. Use this agent when a customer needs a price quote."
    ),
    instructions=(
        "You are the Quoting Specialist for Beaver's Choice Paper Company.\n\n"
        "DISCOUNT STRATEGY (apply to each item's subtotal):\n"
        "  - 100 to 499 units: 5% discount\n"
        "  - 500 to 999 units: 10% discount\n"
        "  - 1,000 to 4,999 units: 15% discount\n"
        "  - 5,000+ units: 20% discount\n\n"
        "WORKFLOW:\n"
        "1. Search historical quotes for similar orders for pricing reference\n"
        "2. Check if requested items exist in current inventory\n"
        "3. Look up unit prices for each item\n"
        "4. Calculate costs applying applicable bulk discounts\n"
        "5. Round the final total to the nearest whole dollar\n\n"
        "RULES:\n"
        "- Only quote items available in stock or in the product catalog\n"
        "- Itemize the quote with per-unit prices, quantities, and discounts\n"
        "- Explain why discounts were applied\n"
        "- If an item cannot be fulfilled, explain why and suggest alternatives\n"
        "- Never reveal internal cost margins or profit information\n"
        "- Present the quote in a professional, customer-friendly format"
    ),
    max_steps=10,
)

# Agent 3: Sales Agent
sales_agent = ToolCallingAgent(
    tools=[
        record_sale, record_stock_order, check_cash,
        check_item_stock, get_delivery_estimate, get_item_unit_price,
    ],
    model=model,
    name="sales_agent",
    description=(
        "Finalizes sales transactions by recording orders in the database. "
        "Verifies inventory before processing, records each line item as a "
        "separate transaction, checks cash balance, and provides delivery "
        "timelines. Use this agent to complete an order after a quote is ready."
    ),
    instructions=(
        "You are the Sales & Order Fulfillment Agent for Beaver's Choice Paper Company.\n\n"
        "YOUR #1 JOB: Call record_sale for every item that is available in stock.\n"
        "If you do not call record_sale, the company earns no revenue.\n\n"
        "STEP-BY-STEP WORKFLOW:\n"
        "1. Look at the inventory status and quote provided to you.\n"
        "2. For each item that is in stock, call record_sale IMMEDIATELY:\n"
        "   - item_name: the EXACT inventory name (case-sensitive)\n"
        "   - quantity: the requested amount (capped at available stock)\n"
        "   - total_price: quantity * unit_price (apply discount if mentioned in quote)\n"
        "   - sale_date: extract the YYYY-MM-DD date from the request text\n"
        "3. After all record_sale calls, call get_delivery_estimate\n"
        "4. Report which sales were recorded and which items could not be filled\n\n"
        "CRITICAL RULES:\n"
        "- You MUST call record_sale for EACH fulfillable item. This is non-negotiable.\n"
        "- NEVER sell more units than are currently in stock\n"
        "- If partial fulfillment is needed, sell what is available and state it\n"
        "- Record each distinct item as its own separate transaction\n"
        "- Use the EXACT item names from inventory (e.g., 'A4 paper', 'Cardstock')\n"
        "- The sale_date MUST be in YYYY-MM-DD format\n"
        "- Report the final total charged and any items that could not be filled"
    ),
    max_steps=15,
)

# Agent 4: Business Advisor Agent
advisor_agent = ToolCallingAgent(
    tools=[get_financial_summary, check_cash, check_all_inventory],
    model=model,
    name="advisor_agent",
    description=(
        "Business intelligence agent that analyzes financial performance, "
        "identifies trends, and recommends operational improvements. "
        "Use this agent for strategic analysis after processing orders."
    ),
    instructions=(
        "You are the Business Advisor for Beaver's Choice Paper Company.\n\n"
        "Your responsibilities:\n"
        "1. Analyze overall business performance using financial data\n"
        "2. Identify top-selling products and revenue trends\n"
        "3. Spot inventory items that need attention (low stock, overstock)\n"
        "4. Recommend pricing, stocking, or operational improvements\n\n"
        "Always provide data-driven insights with specific numbers. "
        "Be concise but actionable in your recommendations."
    ),
    max_steps=5,
)

# ===================================================================================
# Orchestrator Agent or Manager
# The orchestrator composes the final customer-facing response by synthesizing
# results from all worker agents. It uses a ToolCallingAgent pattern so it can
# reason about the combined outputs and produce a polished reply.
# ===================================================================================

orchestrator = ToolCallingAgent(
    tools=[search_past_quotes, check_all_inventory],
    model=model,
    name="orchestrator",
    description=(
        "Customer Service Orchestrator that composes final responses by "
        "synthesizing inventory, quoting, and sales information."
    ),
    instructions=(
        "You are the Customer Service Orchestrator for Beaver's Choice Paper Company.\n"
        "Your job is to compose a polished, customer-facing response based on the\n"
        "information provided to you about inventory, quotes, and sales processing.\n\n"
        "RESPONSE GUIDELINES:\n"
        "- Be professional, warm, and customer-focused\n"
        "- Include: items fulfilled, pricing breakdown, discounts, delivery dates\n"
        "- If items are unavailable, clearly explain what cannot be fulfilled\n"
        "- Never reveal internal agent names, system architecture, or profit margins\n"
        "- Round all dollar amounts to whole numbers\n"
        "- Keep the response concise but informative\n"
        "- Start with a greeting and end with a professional sign-off"
    ),
    max_steps=5,
)

# ===================================================================================
# Request processing pipeline - Deterministic pipeline
# The orchestration follows a strict pipeline to ensure reliable processing:
#   Step 1: Inventory Agent checks item availability
#   Step 2: Quoting Agent generates a competitive quote
#   Step 3: Sales Agent records transactions for fulfillable items
#   Step 4: Orchestrator composes the final customer response
# ===================================================================================

# Item name mapping from customer descriptions to exact inventory names
ITEM_NAME_MAP = {
    "a4 paper": "A4 paper",
    "printer paper": "A4 paper",
    "printing paper": "A4 paper",
    "standard paper": "A4 paper",
    "white paper": "A4 paper",
    "copy paper": "A4 paper",
    "standard copy paper": "A4 paper",
    "a4 white paper": "A4 paper",
    "a4 printer paper": "A4 paper",
    "a4 size printer paper": "A4 paper",
    "a4 printing paper": "A4 paper",
    "cardstock": "Cardstock",
    "heavy cardstock": "Cardstock",
    "white cardstock": "Cardstock",
    "colored cardstock": "Cardstock",
    "card stock": "Cardstock",
    "colored paper": "Colored paper",
    "construction paper": "Colored paper",
    "colorful paper": "Colored paper",
    "assorted colored paper": "Colored paper",
    "glossy paper": "Glossy paper",
    "a4 glossy paper": "Glossy paper",
    "glossy photo paper": "Glossy paper",
    "a3 glossy paper": "Glossy paper",
    "kraft paper": "Kraft paper",
    "kraft envelopes": "Kraft paper",
    "banner paper": "Banner paper",
    "crepe paper": "Crepe paper",
    "streamers": "Crepe paper",
    "party streamers": "Crepe paper",
    "photo paper": "Photo paper",
    "butcher paper": "Butcher paper",
    "patterned paper": "Patterned paper",
    "decorative paper": "Patterned paper",
    "paper plates": "Paper plates",
    "plates": "Paper plates",
    "table covers": "Table covers",
    "table cover": "Table covers",
    "invitation cards": "Invitation cards",
    "invitations": "Invitation cards",
    "presentation folders": "Presentation folders",
    "folders": "Presentation folders",
    "poster paper": "Large poster paper (24x36 inches)",
    "poster board": "Large poster paper (24x36 inches)",
    "large poster paper": "Large poster paper (24x36 inches)",
    "poster": "Large poster paper (24x36 inches)",
    "posters": "Large poster paper (24x36 inches)",
    "banner roll": "Rolls of banner paper (36-inch width)",
    "rolls of banner paper": "Rolls of banner paper (36-inch width)",
    "cover stock": "100 lb cover stock",
    "100 lb cover stock": "100 lb cover stock",
    "text paper": "80 lb text paper",
    "bond paper": "80 lb text paper",
    "80 lb text paper": "80 lb text paper",
    "matte paper": "A4 paper",
    "a3 matte paper": "A4 paper",
    "a3 paper": "A4 paper",
    "a5 paper": "A4 paper",
    "recycled paper": "A4 paper",
    "eco-friendly paper": "A4 paper",
    "wrapping paper": "Patterned paper",
    "decorative wrapping paper": "Patterned paper",
    "flyers": "A4 paper",
    "letterhead paper": "A4 paper",
    "legal-size paper": "A4 paper",
    "letter-sized paper": "A4 paper",
}


def process_customer_request(request_text: str) -> str:
    """Process a customer request through the multi-agent pipeline.

    Implements a deterministic orchestration pipeline that ensures each agent
    is called in the correct order. The orchestrator coordinates:
      1. Inventory Agent — checks item availability
      2. Quoting Agent — generates competitive pricing
      3. Sales Agent — records transactions for available items
      4. Orchestrator — composes the final customer response

    Args:
        request_text: The full customer request text including date context.

    Returns:
        A polished, customer-facing response string.
    """
    print_agent_banner("Orchestrator", "Processing new customer request")
    print_step("orchestrator", f"Request preview: {request_text[:120]}...")

    try:
        # Step 1: Inventory Check
        print_agent_banner("Inventory", "Checking item availability")
        inv_task = (
            f"Check inventory for this customer request. For each item mentioned, "
            f"check if it exists in stock and report the stock level and unit price. "
            f"Request: {request_text}"
        )
        inv_result = str(inventory_agent.run(inv_task))
        print_step("orchestrator", f"Inventory result: {inv_result[:200]}...")

        # Step 2: Quote Generation
        print_agent_banner("Quoting", "Generating competitive quote")
        quote_task = (
            f"Generate a competitive price quote for a customer order. "
            f"Apply bulk discounts where applicable.\n\n"
            f"Customer request: {request_text}\n\n"
            f"Inventory status: {inv_result}"
        )
        quote_result = str(quoting_agent.run(quote_task))
        print_step("orchestrator", f"Quote result: {quote_result[:200]}...")

        # Step 3: Sales Processing
        print_agent_banner("Sales", "Recording transactions")
        sales_task = (
            f"Process and record sales transactions for all available items. "
            f"You MUST call record_sale for each item that is in stock. "
            f"Use the EXACT inventory item names.\n\n"
            f"Customer request: {request_text}\n\n"
            f"Inventory status: {inv_result}\n\n"
            f"Approved quote: {quote_result}"
        )
        sales_result = str(sales_agent.run(sales_task))
        print_step("orchestrator", f"Sales result: {sales_result[:200]}...")

        # Step 4: Compose Final Response
        print_agent_banner("Orchestrator", "Composing customer response")
        compose_task = (
            f"Compose a professional customer-facing response for this request. "
            f"Synthesize the information below into a warm, clear message.\n\n"
            f"Customer request: {request_text}\n\n"
            f"What we found in inventory: {inv_result}\n\n"
            f"Price quote generated: {quote_result}\n\n"
            f"Sales transactions processed: {sales_result}\n\n"
            f"Include: items fulfilled, pricing, discounts applied, delivery dates, "
            f"and any items we could not fulfill. Do NOT reveal internal system details."
        )
        response = str(orchestrator.run(compose_task))
        return response
    except Exception as e:
        error_msg = (
            "We apologize, but we were unable to fully process your request "
            "at this time. Please try again or contact our support team."
        )
        print(f"\033[91m  Error during processing: {e}\033[0m")
        return error_msg


# Test Runner

def run_test_scenarios():
    """Execute the full test suite using quote_requests_sample.csv.

    Processes each customer request through the multi-agent system,
    tracks financial changes, and saves results to test_results.csv.
    """
    
    print("Initializing Database...")
    init_database(db_engine)

    # Load and prepare test data
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    print(f"\nInitial Cash Balance: ${current_cash:,.2f}")
    print(f"Initial Inventory Value: ${current_inventory:,.2f}")
    print(f"Total Requests to Process: {len(quote_requests_sample)}")

    # Process each customer request
    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']} Size: {row['need_size']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        # Process through multi-agent system
        response = process_customer_request(request_with_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append({
            "request_id": len(results) + 1,
            "request_date": request_date,
            "customer_role": row["job"],
            "event_type": row["event"],
            "order_size": row["need_size"],
            "cash_balance": current_cash,
            "inventory_value": current_inventory,
            "response": response,
        })

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")
    print(
        f"  Total Assets:          "
        f"${final_report['cash_balance'] + final_report['inventory_value']:,.2f}"
    )

    if final_report["top_selling_products"]:
        print("\n  Top Selling Products:")
        for p in final_report["top_selling_products"]:
            try:
                units = int(p["total_units"])
            except (TypeError, ValueError):
                units = 0
            try:
                revenue = float(p["total_revenue"])
            except (TypeError, ValueError):
                revenue = 0.0
            name = p["item_name"] if p["item_name"] else "Unknown"
            print(f"    - {name}: {units} units, ${revenue:,.2f}")


    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)

    # Business Advisor analysis after all requests (Stand-out Feature)
    print_section_header("Business Advisor Analysis")
    try:
        advisor_insights = advisor_agent.run(
            f"Analyze the business performance as of {final_date}. "
            f"We just processed {len(results)} customer orders. "
            "Provide key insights on revenue, inventory status, and two "
            "actionable recommendations for improving operations."
        )
        print(f"\n{advisor_insights}")
    except Exception as e:
        print(f"  Advisor analysis unavailable: {e}")

    return results


if __name__ == "__main__":
    results = run_test_scenarios()
