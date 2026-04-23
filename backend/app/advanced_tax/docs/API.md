# Advanced Tax Engine - API Reference

## Complete REST API Documentation

All endpoints are prefixed with `/api/premium/`

---

## Tax-Loss Harvesting API

### `/tax-loss/opportunities` [GET]

**Summary:** Scan portfolio for tax-loss harvesting opportunities

**Parameters:**
- `country` (query, string) - Country code (MX, BR, AR, default: MX)

**Response:**
```json
{
  "status": "success",
  "opportunities": [
    {
      "asset": "BTC",
      "quantity": 0.5,
      "purchase_price": 50000,
      "current_price": 40000,
      "loss_amount": 5000,
      "loss_percentage": -10.0,
      "tax_rate": 0.30,
      "tax_savings": 1500,
      "wash_sale_days_remaining": 0,
      "priority_score": 95,
      "risk_level": "medium",
      "volatility": 8.5
    }
  ],
  "summary": {
    "opportunities_count": 5,
    "total_realizable_loss": 15000,
    "total_potential_tax_savings": 4500
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Validation error
- `500` - Server error

---

### `/tax-loss/impact-summary` [GET]

**Summary:** Get total tax impact of all opportunities

**Parameters:**
- `country` (query, string) - Country code

**Response:**
```json
{
  "status": "success",
  "summary": {
    "opportunities_count": 5,
    "total_realizable_loss": 15000.00,
    "total_potential_tax_savings": 4500.00,
    "top_opportunities": [...]
  }
}
```

---

### `/tax-loss/execute/{opportunity_id}` [POST]

**Summary:** Execute tax-loss harvest - sell the losing position

**Parameters:**
- `opportunity_id` (path, integer) - Harvest opportunity ID
- `exchange_id` (query, integer, required) - Exchange ID for execution

**Response:**
```json
{
  "status": "success",
  "action_executed": {
    "status": "success",
    "action": "SELL",
    "asset": "BTC",
    "quantity": 0.5,
    "price": 40000,
    "tax_savings": 1500,
    "rebuy_date": "2025-05-12T15:30:00"
  }
}
```

**Notes:**
- Wash-sale rule: cannot rebuy within 30 days
- Rebuy must be "substantially identical" asset
- Execution is live on exchange (if enabled)

---

### `/tax-loss/execute-rebuy/{harvest_id}` [POST]

**Summary:** Execute rebuy after wash-sale period expires

**Parameters:**
- `harvest_id` (path, integer) - Harvest ID
- `exchange_id` (query, integer, required) - Exchange ID

**Response:**
```json
{
  "status": "success",
  "message": "Rebuy executed - tax loss now locked in"
}
```

---

### `/tax-loss/history` [GET]

**Summary:** Get all past harvests and results

**Parameters:**
- `year` (query, integer, optional) - Filter by tax year

**Response:**
```json
{
  "status": "success",
  "history": [
    {
      "harvest_id": 123,
      "asset": "ETH",
      "executed_at": "2024-05-10",
      "tax_savings": 800,
      "status": "completed"
    }
  ],
  "total_realized_savings": 3500.00
}
```

---

### `/tax-loss/status/{harvest_id}` [GET]

**Summary:** Get current status of harvest operation

**Parameters:**
- `harvest_id` (path, integer) - Harvest ID

**Response:**
```json
{
  "status": "success",
  "harvest": {
    "id": 123,
    "asset": "BTC",
    "status": "executed",
    "executed_at": "2024-05-10",
    "executed_price": 40000,
    "tax_savings": 1500,
    "rebuy_scheduled_at": "2024-06-09"
  }
}
```

---

## Smart Reconciliation API

### `/reconciliation/gaps` [GET]

**Summary:** Find all transactions with missing cost basis

**Parameters:**
- `country` (query, string) - Country code

**Response:**
```json
{
  "status": "success",
  "gaps": [
    {
      "transaction_id": 456,
      "asset": "ETH",
      "quantity": 5,
      "date": "2024-01-15",
      "current_estimated_value": 15000,
      "potential_tax_impact": 4500,
      "severity_score": 0.85
    }
  ],
  "summary": {
    "total_gaps": 12,
    "total_tax_impact": 35000.00
  }
}
```

---

### `/reconciliation/suggestions/{transaction_id}` [GET]

**Summary:** Find potential source transactions

**Parameters:**
- `transaction_id` (path, integer) - Transaction with gap
- `search_depth_hours` (query, integer) - Search window (default: 72)

**Response:**
```json
{
  "status": "success",
  "transaction_id": 456,
  "suggestions": [
    {
      "source_id": 450,
      "source_type": "blockchain_transfer",
      "asset": "ETH",
      "quantity": 5,
      "date": "2024-01-14",
      "confidence": "95%",
      "reason": "exact_transfer_match",
      "estimated_price": 3000
    },
    {
      "source_id": 451,
      "source_type": "exchange_buy",
      "asset": "ETH",
      "quantity": 5.01,
      "date": "2024-01-14",
      "confidence": "89%",
      "reason": "amount_fee_adjustment",
      "estimated_price": 2999
    }
  ]
}
```

**Matching reasons:**
- `exact_transfer_match` - Same address, same amount, same date
- `exchange_buy_order` - Buy on exchange matching deposit
- `import_timestamp_match` - Import record with matching timestamp
- `pattern_match` - Statistical match

---

### `/reconciliation/accept-match` [POST]

**Summary:** Link send and receive transactions

**Parameters:**
- `receive_txn_id` (query, integer) - Transaction with gap
- `send_txn_id` (query, integer) - Source transaction
- `reason` (query, string) - Reason for match

**Response:**
```json
{
  "status": "success",
  "matched": {
    "status": "success",
    "message": "Cost basis linked successfully",
    "cost_basis": 15000.00
  }
}
```

---

### `/reconciliation/manual-entry` [POST]

**Summary:** User manually sets cost basis

**Parameters:**
- `transaction_id` (query, integer) - Transaction ID
- `cost_basis` (query, decimal) - Cost basis in USD
- `source` (query, string) - Source (user_entry, import, etc.)
- `notes` (query, string) - User notes

**Response:**
```json
{
  "status": "success",
  "result": {
    "status": "success",
    "message": "Cost basis set manually",
    "cost_basis": 15000.00
  }
}
```

---

### `/reconciliation/summary` [GET]

**Summary:** Get reconciliation overview

**Response:**
```json
{
  "status": "success",
  "summary": {
    "total_gaps": 12,
    "pending_count": 5,
    "matched_count": 6,
    "manual_count": 1,
    "total_tax_impact": 35000.00,
    "pending_gaps": [...]
  }
}
```

---

## Audit Trail API

### `/audit/export` [GET]

**Summary:** Generate complete audit package

**Parameters:**
- `tax_year` (query, integer, required) - Tax year
- `country` (query, string) - Country code
- `formats` (query, array) - Export formats (json, pdf, excel)

**Response:**
```json
{
  "status": "success",
  "audit_package": {
    "package_id": 789,
    "transaction_count": 500,
    "calculation_count": 1200,
    "total_tax": 25000.00,
    "country": "MX",
    "tax_year": 2024,
    "files": {
      "json": "/audit/download/789/json",
      "pdf": "/audit/download/789/pdf",
      "excel": "/audit/download/789/excel"
    }
  }
}
```

---

### `/audit/rules` [GET]

**Summary:** Get verified tax rules for a country

**Parameters:**
- `country` (query, string) - Country code

**Response:**
```json
{
  "status": "success",
  "country": "MX",
  "rules_count": 8,
  "rules": [
    {
      "code": "MX_ISR_001",
      "name": "ISR Progressive Income Tax",
      "tax_type": "INCOME_TAX",
      "verified_date": "2024-04-01",
      "verified_by": "expert@latamtax.com",
      "law": "Ley del Impuesto Sobre la Renta",
      "law_link": "https://www.sat.gob.mx/...",
      "authority": "SAT",
      "status": "active"
    }
  ]
}
```

---

### `/audit/calculation/{calculation_id}` [GET]

**Summary:** Get detailed audit info about a calculation

**Parameters:**
- `calculation_id` (path, integer) - Calculation ID

**Response:**
```json
{
  "status": "success",
  "calculation_details": {
    "calculation": {
      "id": 1001,
      "asset": "BTC",
      "quantity": 1.5,
      "buy_price": 40000,
      "sell_price": 50000,
      "tax_type": "CAPITAL_GAINS",
      "tax_rate": 0.20,
      "calculated_tax": 3000,
      "reasoning": "Long-term capital gain (held >12 months) at 20% rate",
      "method": "FIFO"
    },
    "rule": {
      "code": "MX_CG_LONG_001",
      "name": "Long-Term Capital Gains",
      "law": "Ley del ISR Art. 63",
      "law_link": "...",
      "authority": "SAT",
      "verified_date": "2024-01-15"
    },
    "verified": {
      "status": true,
      "verified_by": "accountant@firm.com",
      "verified_date": "2024-04-10"
    }
  }
}
```

---

### `/audit/download/{package_id}/{format}` [GET]

**Summary:** Download audit package file

**Parameters:**
- `package_id` (path, integer) - Package ID
- `format` (path, string) - Format (json, pdf, excel)

**Response:**
- `200` - File download
- `404` - Package or format not found
- `403` - Unauthorized (not user's package)

**Headers:**
```
Content-Type: application/pdf (or application/json, application/vnd.ms-excel)
Content-Disposition: attachment; filename="audit_MX_2024.pdf"
```

---

### `/audit/summary` [GET]

**Summary:** Get overview of all audit packages

**Parameters:**
- `tax_year` (query, integer, optional)
- `country` (query, string) - Country code

**Response:**
```json
{
  "status": "success",
  "packages": [
    {
      "package_id": 789,
      "tax_year": 2024,
      "country": "MX",
      "status": "ready",
      "generated_at": "2024-04-12",
      "transaction_count": 500,
      "total_tax": 25000.00
    }
  ]
}
```

---

## Error Responses

### Standard Error Format
```json
{
  "detail": "Error description"
}
```

### Common HTTP Status Codes
- `200` - Success
- `400` - Bad request (validation failed)
- `401` - Unauthorized (no JWT token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `500` - Internal server error
- `503` - Service unavailable

### Example Error
```json
{
  "detail": "Invalid opportunity_id: -1"
}
```

---

## Rate Limiting

No explicit rate limits, but recommend:
- Export operations: 1 per minute (can take time)
- Scan operations: 1 per 10 seconds
- Query operations: 10 per second

---

## Authentication

All requests require JWT token in header:
```
Authorization: Bearer <token>
```

Token obtained from backend login endpoint.

---

## Pagination

List endpoints support pagination:
- `skip` (query, integer) - Number of items to skip (default: 0)
- `limit` (query, integer) - Items per page (default: 100, max: 1000)

Example:
```
GET /api/premium/reconciliation/gaps?skip=0&limit=50
```

---

## Versioning

Current API version: **v1** (in URL path: `/api/v1/premium/...`)

Future version will support `/api/v2/premium/...` with backward compatibility.

---

## Webhook Events (Future)

Coming soon: Webhook notifications for:
- `tax_loss.opportunity_identified`
- `reconciliation.match_found`
- `audit.package_ready`
