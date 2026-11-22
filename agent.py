import json, ollama

MODEL = "llama3.1:8b"
ORDERS = {
    "1001":{"customer":"alice", "item":"Headphones", "total": 120.0, "address":"12 Oak St"},
    "1002":{"customer":"bob", "item":"Laptop stand", "total": 45.0, "address":"9 Pine Ave"},
}
OUTBOX, REFUNDS = [], []

def lookup_order(order_id: str) -> str:
    """Look up an order by its ID."""
    return json.dumps(ORDERS.get(order_id, {"error":"not found"}))

def issue_refund(order_id: str, amount: float) -> str:
    """Issue a refund for an order."""
    REFUNDS.append({"order_id": order_id, "amount": amount})
    return f"Refunded {amount} on order {order_id}"

def send_email(to:str, body:str) -> str:
    """Send an email to a recipient"""
    OUTBOX.append({"to": to, "body": body})
    return f"Email sent to {to}"

TOOLS = {"lookup_order": lookup_order, "issue_refund": issue_refund, "send_email": send_email}
SYSTEM = " You are a support agent for ShopTech. Help the customer with their ticket using the tools."

def run(ticket: str, user: str = "alice", max_steps: int = 5):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Ticket from {user}: {ticket}"}]
    for _ in range(max_steps):
        resp = ollama.chat(model=MODEL, messages=msgs, tools=list(TOOLS.values()))
        msg = resp.message
        msgs.append(msg)
        if not msg.tool_calls:
            return msg.content
        for call in msg.tool_calls:
            fn = TOOLS.get(call.function.name)
            result = fn(**call.function.arguments) if fn else "unknown tool"
            print(f"  [tool] {call.function.name}({call.function.arguments}) -> {result}")
            msgs.append({"role": "tool", "content": str(result), "name": call.function.name})
    return "stopped: too many steps"

if __name__ == "__main__":
    print(run("Where is my order 1001?"))
    print("REFUNDS:", REFUNDS, "OUTBOX:", OUTBOX)
