import re

def patch_gateway():
    path = "gateway/app/main.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix CORS allow_origins with allow_credentials
    old_cors = """app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""
    new_cors = """app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID", "Content-Disposition"],
)"""
    if "allow_origin_regex" not in content:
        content = content.replace('allow_origins=["*"]', 'allow_origin_regex=r"^https?://.*"')
        if 'expose_headers' not in content:
            content = content.replace('allow_headers=["*"],', 'allow_headers=["*"],\n    expose_headers=["X-Correlation-ID", "Content-Disposition"],')
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Patched gateway CORS configuration.")
    else:
        print("Gateway CORS already patched.")

def patch_payment_service():
    path = "services/payment-service/app/service.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update compensation status to REFUNDED if refund succeeds
    old_block = """            tx.status = "FAILED"
            await db.commit()"""

    new_block = """            tx.status = "REFUNDED" if refund_success else "FAILED"
            if refund_success and tx.user_balance_before is not None:
                tx.user_balance_after = tx.user_balance_before
            tx.completed_at = datetime.now(timezone.utc)
            await db.commit()"""

    if old_block in content:
        content = content.replace(old_block, new_block)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Patched payment service compensation status.")
    else:
        print("Payment service already patched or pattern differed.")

if __name__ == "__main__":
    patch_gateway()
    patch_payment_service()
