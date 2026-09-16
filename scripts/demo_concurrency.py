"""
Concurrency Demo Script for iBanking Tuition Payment System.

This script demonstrates that the system correctly handles concurrent requests
(Race Conditions) preventing double-spending and ensuring data consistency.

Scenario:
User "levanc" has a balance of 10,000,000 VND.
He tries to pay a tuition fee of 6,500,000 VND (from MSSV 52100007).
He intentionally sends TWO identical payment requests at the EXACT SAME TIME.

Expected Result:
1 request succeeds, deducting 6,500,000 VND.
1 request fails (insufficient balance or already paid), preventing double-spending.
Final balance should be 3,500,000 VND.
"""
import asyncio
import httpx
import time

API_URL = "http://localhost:8000/api"

async def login_user(username, password):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{API_URL}/auth/login", json={
            "username": username,
            "password": password
        })
        res.raise_for_status()
        return res.json()["access_token"]

async def initiate_payment(client, mssv, tuition_fee_id, req_id):
    print(f"[Req {req_id}] Initiating payment at {time.time()}")
    try:
        res = await client.post(f"{API_URL}/payments/initiate", json={
            "mssv": mssv,
            "tuition_fee_id": tuition_fee_id
        })
        print(f"[Req {req_id}] Initiate Result: {res.status_code} - {res.text}")
        if res.status_code == 201:
            return res.json()["transaction_id"]
        return None
    except Exception as e:
        print(f"[Req {req_id}] Error: {e}")
        return None

async def confirm_payment(client, transaction_id, req_id):
    if not transaction_id:
        return None
    try:
        res = await client.post(f"{API_URL}/payments/{transaction_id}/confirm")
        print(f"[Req {req_id}] Confirm Result: {res.status_code} - {res.text}")
        return res.status_code == 200
    except Exception as e:
        print(f"[Req {req_id}] Error: {e}")
        return False

async def get_fee_id(mssv):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_URL}/tuition/{mssv}")
        if res.status_code == 200:
            fees = res.json().get("tuition_fees", [])
            for fee in fees:
                if fee["amount"] == 6500000.00:
                    return fee["id"]
        return None

async def run_concurrency_test():
    print("="*60)
    print("🚦 CONCURRENCY TEST DEMO (RACE CONDITION) 🚦")
    print("="*60)
    
    # 1. Login
    print("1. Logging in as 'levanc' (Balance: 10,000,000 VND)...")
    token = await login_user("levanc", "password123")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get target tuition fee (MSSV: 52100007, Amount: 6.500.000)
    print("2. Looking up tuition fee...")
    mssv = "52100007"
    tuition_fee_id = await get_fee_id(mssv)
    if not tuition_fee_id:
        print("❌ Cannot find target tuition fee. Please run seed_data.py first.")
        return
        
    print(f"   Target Fee ID: {tuition_fee_id} (6,500,000 VND)")

    async with httpx.AsyncClient(headers=headers) as client:
        # Check initial balance
        user_info = await client.get(f"{API_URL}/users/me/balance")
        initial_balance = user_info.json()["balance"]
        print(f"\n💰 Initial Balance: {initial_balance:,.0f} VND\n")

        print("3. FIring 2 simultaneous payment requests...")
        # Fire 2 requests at the exact same time
        task1 = asyncio.create_task(initiate_payment(client, mssv, tuition_fee_id, 1))
        task2 = asyncio.create_task(initiate_payment(client, mssv, tuition_fee_id, 2))
        
        txn_id1, txn_id2 = await asyncio.gather(task1, task2)
        
        print("\n4. Checking final balance after concurrent requests...")
        user_info = await client.get(f"{API_URL}/users/me/balance")
        final_balance = user_info.json()["balance"]
        
        print(f"💰 Final Balance: {final_balance:,.0f} VND")
        
        if initial_balance - final_balance == 6500000.0:
            print("\n✅ SUCCESS! System successfully prevented double-spending.")
            print("   Only one request was allowed to lock and deduct the balance.")
        else:
            print("\n❌ FAILURE! Balance anomaly detected.")

if __name__ == "__main__":
    asyncio.run(run_concurrency_test())
