# Complete API Documentation

**TLH + Open Banking System - REST API Reference**

API Version: 1.0.0  
Base URL: `http://localhost:8000/api/v1`  
Status: Production Ready  

---

## Table of Contents

1. [TLH Endpoints (13 total)](#tlh-endpoints)
2. [Banking Endpoints (7 total)](#banking-endpoints)
3. [Database Models](#database-models)
4. [Error Codes](#error-codes)

---

## TLH Endpoints

### 1. Scan Portfolio

**POST** `/tlh/scan`

Scan portfolio for Tax-Loss Harvesting opportunities.

**Request:**
```json
{}
```

**Response (200):**
```json
{
  "opportunities_found": 42,
  "total_harvestable_losses": "125000.50",
  "total_tax_benefit": "30000.12",
  "opportunities": [
    {
      "id": "opp_1",
      "user_id": "test_user",
      "asset": "BTC",
      "loss_amount": "50000.00",
      "priority_score": 85.5,
      "priority_breakdown": {
        "tax_savings": 30.0,
        "liquidity": 25.0,
        "volatility": 15.0,
        "wash_sale_penalty": -5.0,
        "fee_impact": -5.0,
        "urgency": 24.5
      },
      "explanation": "BTC showing 45% loss...",
      "status": "new",
      "wash_sale_risk": false,
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

---

### 2. List Opportunities

**GET** `/tlh/opportunities`

List all TLH opportunities with optional filtering.

**Query Parameters:**
- `status` (string, optional) - Filter by status
- `asset` (string, optional) - Filter by asset (BTC, ETH)
- `min_loss` (number, optional) - Minimum loss amount

**Response (200):**
```json
[
  {
    "id": "opp_1",
    "asset": "BTC",
    "loss_amount": "50000.00",
    "priority_score": 85.5,
    "status": "new"
  }
]
```

---

### 3. Get Opportunity Details

**GET** `/tlh/opportunities/{opportunity_id}`

Get detailed information about a specific opportunity.

**Path Parameters:**
- `opportunity_id` (string, required)

**Response (200):**
```json
{
  "id": "opp_1",
  "user_id": "test_user",
  "asset": "BTC",
  "loss_amount": "50000.00",
  "priority_score": 85.5,
  "priority_breakdown": { ... },
  "explanation": "...",
  "status": "new",
  "execution_strategy": null,
  "wash_sale_risk": false,
  "wash_sale_days_remaining": 0,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "execution_history": []
}
```

**Response (404):**
```json
{
  "detail": "Opportunity not found"
}
```

---

### 4. Create Opportunity

**POST** `/tlh/opportunities`

Manually create a new TLH opportunity.

**Request:**
```json
{
  "position_id": "pos_123",
  "asset": "ETH",
  "loss_amount": "25000.00",
  "tax_rate": 24.0,
  "priority_score": 78.5,
  "explanation": "ETH position with significant loss"
}
```

**Response (200):**
```json
{
  "id": "opp_new_1",
  "user_id": "test_user",
  "position_id": "pos_123",
  "asset": "ETH",
  "loss_amount": "25000.00",
  "priority_score": 78.5,
  "status": "new",
  "created_at": "2024-01-01T12:00:00"
}
```

---

### 5. Update Opportunity

**PUT** `/tlh/opportunities/{opportunity_id}`

Update opportunity status, strategy, or notes.

**Request:**
```json
{
  "status": "approved",
  "execution_strategy": "immediate",
  "notes": "Ready for execution"
}
```

**Response (200):**
```json
{
  "id": "opp_1",
  "status": "approved",
  "execution_strategy": "immediate",
  "notes": "Ready for execution",
  "updated_at": "2024-01-01T12:30:00"
}
```

---

### 6. Delete Opportunity

**DELETE** `/tlh/opportunities/{opportunity_id}`

Cancel/delete an opportunity.

**Response (200):**
```json
{
  "status": "cancelled",
  "opportunity_id": "opp_1"
}
```

---

### 7. Execute Opportunity (Single)

**POST** `/tlh/opportunities/{opportunity_id}/execute`

Execute a single opportunity with specified strategy.

**Request:**
```json
{
  "strategy": "immediate",
  "limit_price": null,
  "scheduled_for": null,
  "dry_run": true
}
```

**Strategies:**
- `immediate` - Execute now
- `limit_price` - Execute when price reaches limit
- `scheduled` - Execute at scheduled time

**Response (200):**
```json
{
  "success": true,
  "opportunity_id": "opp_1",
  "status": "dry_run_pending",
  "message": "Execution initiated with immediate strategy",
  "dry_run": true,
  "quantity_executed": "0.5",
  "fees_paid": "50.00"
}
```

---

### 8. Bulk Execute

**POST** `/tlh/bulk-execute`

Execute multiple opportunities at once.

**Request:**
```json
{
  "opportunity_ids": ["opp_1", "opp_2", "opp_3"],
  "strategy": "immediate",
  "dry_run": true
}
```

**Response (200):**
```json
{
  "total_opportunities": 3,
  "successful": 2,
  "failed": 1,
  "pending": 0,
  "total_harvestable_loss": "125000.00",
  "total_tax_benefit": "30000.00",
  "results": [
    {
      "success": true,
      "opportunity_id": "opp_1",
      "status": "dry_run_pending",
      "message": "Queued for immediate execution",
      "dry_run": true
    },
    {
      "success": false,
      "opportunity_id": "opp_2",
      "status": "failed",
      "message": "Insufficient liquidity"
    }
  ]
}
```

---

### 9. Get Execution History

**GET** `/tlh/opportunities/{opportunity_id}/history`

Get execution history for a specific opportunity.

**Response (200):**
```json
[
  {
    "id": "exec_1",
    "strategy": "immediate",
    "status": "completed",
    "dry_run": false,
    "order_id": "order_123",
    "quantity_executed": "0.5",
    "average_price": "20000.00",
    "fees_paid": "50.00",
    "executed_at": "2024-01-01T12:00:00"
  }
]
```

---

### 10. Get Price Events

**GET** `/tlh/events`

Get recent price events that trigger TLH recalculation.

**Query Parameters:**
- `asset` (string, optional) - Filter by asset
- `hours` (integer, default 24) - Look back N hours

**Response (200):**
```json
[
  {
    "id": "event_1",
    "event_type": "PRICE_DROP",
    "asset": "BTC",
    "previous_price": "21000.00",
    "current_price": "19500.00",
    "price_change_pct": -7.14,
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

---

### 11. Get TLH Metrics

**GET** `/tlh/metrics`

Get system-wide TLH metrics and statistics.

**Response (200):**
```json
{
  "total_harvestable_losses": "500000.00",
  "total_tax_benefit": "120000.00",
  "average_priority_score": 78.5,
  "wash_sale_risks": 3,
  "executed_opportunities": 15,
  "pending_executions": 8,
  "success_rate": 0.9375,
  "average_fees": "45.50"
}
```

---

### 12. TLH Health Check

**GET** `/tlh/health`

Health check endpoint.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "tlh",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## Banking Endpoints

### 1. Connect Bank Account

**POST** `/banking/accounts/connect`

Connect a new bank account via Open Banking API.

**Request:**
```json
{
  "bank_type": "nubank",
  "account_number": "12345678",
  "account_name": "My Nubank Account",
  "currency": "BRL",
  "api_key": "key_xxx",
  "api_secret": "secret_xxx"
}
```

**Supported Banks:**
- `nubank` - Nubank (Brazil)
- `mercado_pago` - Mercado Pago (multi-country)
- `lemon` - Lemon (Mexico)
- `belo` - Belo (Argentina)

**Response (200):**
```json
{
  "id": "bank_acc_1",
  "bank_type": "nubank",
  "account_number": "12345678",
  "account_name": "My Nubank Account",
  "currency": "BRL",
  "balance": "50000.00",
  "sync_status": "pending",
  "connected_at": "2024-01-01T12:00:00"
}
```

---

### 2. List Bank Accounts

**GET** `/banking/accounts`

List all connected bank accounts.

**Response (200):**
```json
[
  {
    "id": "bank_acc_1",
    "bank_type": "nubank",
    "account_name": "My Nubank",
    "currency": "BRL",
    "balance": "50000.00",
    "sync_status": "synced",
    "last_sync": "2024-01-01T12:00:00"
  }
]
```

---

### 3. Get Bank Account

**GET** `/banking/accounts/{account_id}`

Get specific bank account details.

**Response (200):**
```json
{
  "id": "bank_acc_1",
  "bank_type": "nubank",
  "account_number": "12345678",
  "account_name": "My Nubank",
  "currency": "BRL",
  "balance": "50000.00",
  "sync_status": "synced",
  "last_sync": "2024-01-01T12:00:00",
  "connected_at": "2024-01-01T10:00:00"
}
```

---

### 4. Sync Bank Transactions

**POST** `/banking/accounts/{account_id}/sync`

Sync transactions from connected bank account.

**Request:**
```json
{
  "days_back": 30,
  "force_full_sync": false
}
```

**Response (200):**
```json
{
  "account_id": "bank_acc_1",
  "transactions_synced": 24,
  "new_deposits": 8,
  "new_withdrawals": 3,
  "last_sync": "2024-01-01T12:00:00",
  "status": "success"
}
```

---

### 5. Disconnect Bank Account

**DELETE** `/banking/accounts/{account_id}`

Disconnect a bank account.

**Response (200):**
```json
{
  "status": "disconnected",
  "account_id": "bank_acc_1"
}
```

---

### 6. List Bank Transactions

**GET** `/banking/transactions`

List bank transactions with optional filtering.

**Query Parameters:**
- `account_id` (string, optional)
- `type` (string, optional) - deposit, withdrawal, transfer
- `min_amount` (number, optional)
- `max_amount` (number, optional)
- `days` (integer, default 30)

**Response (200):**
```json
[
  {
    "id": "bank_txn_1",
    "date": "2024-01-01T12:00:00",
    "type": "deposit",
    "amount": "1000.00",
    "currency": "BRL",
    "description": "Deposit from exchange",
    "counterparty": "Binance",
    "balance_after": "51000.00",
    "matched_crypto_transaction_id": null,
    "matched_confidence": 0.0
  }
]
```

---

### 7. Create Transaction Match

**POST** `/banking/match`

Manually create a match between crypto withdrawal and bank deposit.

**Request:**
```json
{
  "crypto_withdrawal_id": "crypto_wd_1",
  "bank_deposit_id": "bank_txn_1",
  "crypto_amount": "0.05",
  "crypto_currency": "BTC",
  "fiat_amount": "1000.00",
  "fiat_currency": "BRL",
  "exchange_rate": "20000.00",
  "fees_paid": "10.00"
}
```

**Response (200):**
```json
{
  "id": "match_1",
  "crypto_withdrawal_id": "crypto_wd_1",
  "bank_deposit_id": "bank_txn_1",
  "crypto_amount": "0.05",
  "crypto_currency": "BTC",
  "fiat_amount": "1000.00",
  "fiat_currency": "BRL",
  "exchange_rate": "20000.00",
  "fees_paid": "10.00",
  "confidence": 1.0,
  "match_status": "matched",
  "time_delta_hours": 2.5,
  "created_at": "2024-01-01T12:00:00"
}
```

---

### 8. Auto-Match Transactions

**POST** `/banking/match-auto`

Automatically match crypto withdrawals to bank deposits using smart algorithm.

**Request:**
```json
{
  "tolerance_percent": 2.0,
  "time_window_hours": 24
}
```

**Matching Algorithm:**
- Amount tolerance: ±2% (configurable)
- Time window: 24 hours (configurable)
- Counterparty analysis
- Confidence scoring (0-1)

**Response (200):**
```json
{
  "matches_found": 12,
  "high_confidence_matches": 10,
  "medium_confidence_matches": 2,
  "matches": [
    {
      "id": "match_1",
      "crypto_withdrawal_id": "crypto_wd_1",
      "bank_deposit_id": "bank_txn_1",
      "crypto_amount": "0.05",
      "crypto_currency": "BTC",
      "fiat_amount": "1000.00",
      "fiat_currency": "BRL",
      "confidence": 0.98,
      "time_delta_hours": 2.5
    }
  ]
}
```

---

### 9. List Transaction Matches

**GET** `/banking/matches`

List all transaction matches.

**Query Parameters:**
- `min_confidence` (float, default 0.0) - Filter by minimum confidence

**Response (200):**
```json
[
  {
    "id": "match_1",
    "crypto_withdrawal_id": "crypto_wd_1",
    "bank_deposit_id": "bank_txn_1",
    "confidence": 0.98,
    "match_status": "matched"
  }
]
```

---

### 10. Get Cycle Dashboard

**GET** `/banking/cycle-dashboard`

Get complete crypto → fiat cycle visualization (7 stages).

**Response (200):**
```json
{
  "user_id": "test_user",
  "total_positions": 5,
  "total_withdrawn_crypto": "2.5",
  "total_deposited_fiat": "50000.00",
  "total_fees": "250.00",
  "matched_cycles": 12,
  "pending_matches": 3,
  "tax_ready": true,
  "stages": [
    {
      "stage_number": 1,
      "stage_name": "Holdings",
      "status": "complete",
      "holdings": { ... }
    },
    {
      "stage_number": 2,
      "stage_name": "Exchange Connection",
      "status": "complete"
    }
  ]
}
```

---

### 11. Get Banking Metrics

**GET** `/banking/metrics`

Get banking integration metrics.

**Response (200):**
```json
{
  "connected_banks": 3,
  "synced_accounts": 3,
  "total_transactions": 127,
  "unmatched_transactions": 5,
  "matched_deposits": 122,
  "average_match_confidence": 0.97,
  "total_volume": "500000.00"
}
```

---

### 12. Banking Health Check

**GET** `/banking/health`

Health check endpoint.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "banking",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## Database Models

### TLH Opportunities
- `id` - UUID
- `user_id` - Reference to user
- `position_id` - Reference to portfolio position
- `asset` - Cryptocurrency symbol (BTC, ETH)
- `loss_amount` - Lost value in USD
- `tax_rate` - Tax rate for calculation
- `priority_score` - 0-100 score
- `priority_breakdown` - JSON with component scores
- `status` - new, reviewed, approved, executing, executed, failed
- `wash_sale_risk` - Boolean
- `wash_sale_days_remaining` - Days until wash-sale expires

### Bank Accounts
- `id` - UUID
- `user_id` - Reference to user
- `bank_type` - nubank, mercado_pago, lemon, belo
- `account_number` - Bank account identifier
- `currency` - BRL, ARS, MXN, USD
- `balance` - Current balance
- `sync_status` - pending, syncing, synced, error
- `last_sync` - Last sync timestamp

### Bank Transactions
- `id` - UUID
- `account_id` - Reference to bank account
- `date` - Transaction date/time
- `type` - deposit, withdrawal, transfer, fee
- `amount` - Transaction amount
- `currency` - Currency code
- `description` - Transaction description
- `counterparty` - Counterparty identifier

### Transaction Matches
- `id` - UUID
- `crypto_withdrawal_id` - Reference to crypto withdrawal
- `bank_deposit_id` - Reference to bank deposit
- `confidence` - Match confidence (0-1)
- `crypto_amount` - Crypto amount withdrawn
- `fiat_amount` - Fiat amount deposited
- `exchange_rate` - Conversion rate
- `fees_paid` - Transaction fees

---

## Error Codes

### 400 Bad Request
```json
{
  "detail": "Invalid bank type. Supported: nubank, mercado_pago, lemon, belo"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Opportunity not found"
}
```

### 500 Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Best Practices

1. **Always use dry_run=true** before executing opportunities
2. **Auto-match with confidence > 0.95** for production
3. **Call `/health`** endpoints for uptime monitoring
4. **Implement retry logic** for network failures
5. **Cache opportunity list** for 5-10 minutes
6. **Use bulk operations** when possible (more efficient)

---

**Last Updated:** 2024-01-01  
**Status:** Production Ready  
**Endpoints:** 20+ total (13 TLH + 7 Banking)  
**Database:** SQLAlchemy + Alembic Migrations
