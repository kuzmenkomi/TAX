# 🚀 Declairo - Crypto Tax Portal

A comprehensive tax optimization tool for cryptocurrency transactions, supporting multiple exchanges, wallets, DeFi protocols, and blockchain networks.

## 📚 Quick Links

- **👋 Getting Started**: [GETTING_STARTED_GUIDE.md](GETTING_STARTED_GUIDE.md) - **START HERE** (5 min setup)
- **📖 All Documentation**: [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Complete docs index
- **⚡ Quick Reference**: [QUICK_REFERENCE_DEV.md](QUICK_REFERENCE_DEV.md) - Copy-paste commands
- **📍 Development Setup**: [backend/LOCAL_DEVELOPMENT.md](backend/LOCAL_DEVELOPMENT.md) - Full dev guide
- **🚀 Deployment**: [backend/DEPLOYMENT_GUIDE.md](backend/DEPLOYMENT_GUIDE.md) - Production ready

## ✨ Features

- **🔗 Multi-Blockchain Support**: 10+ networks (Ethereum, Polygon, BSC, Solana, Bitcoin, TRON, Avalanche, Arbitrum, Optimism, Base)
- **💱 100+ Exchanges**: Direct API integration with CCXT (Binance, Coinbase, Kraken, OKX, KuCoin, Gate.io, Bybit, Huobi, + 92 more)
- **🔐 Secure API Management**: Encrypted storage using Fernet symmetric encryption
- **📊 Blockchain Explorer**: Real-time wallet scanning with auto-sync every 6 hours
- **📈 DeFi Protocol Support**: Uniswap, Aave, Curve, Lido, Compound, Balancer, yearn, MakerDAO
- **💰 Tax Calculations**: FIFO, LIFO, HIFO, AVCO, weighted average methods
- **🇧🇷 Brazilian Compliance**: GCAP, DIRPF, DeCripto forms (IRPF XML export)
- **📱 Portfolio Dashboard**: Unified view of all assets and transactions
- **🔄 Auto-Sync Scheduler**: Background jobs for wallets, exchanges, and price feeds
- **⚡ Real-time Prices**: CryptoCompare (historical) + CoinCap (real-time)
- **📊 Interactive Analytics**: Charts, tax breakdown, unrealized P&L tracking

## 🏗️ Technology Stack

**Backend:**
- FastAPI (Python async web framework)
- SQLAlchemy ORM with Alembic migrations
- PostgreSQL / SQLite
- APScheduler (background jobs)
- CCXT (100+ exchanges)
- Fernet encryption (API keys)
- JWT authentication

**Frontend:**
- React 18 with TypeScript
- Vite (development server)
- Tailwind CSS (styling)
- TanStack Query (data fetching)
- Lucide React (icons)

**Infrastructure:**
- Docker & Docker Compose
- PostgreSQL 16
- CORS middleware
- Rate limiting (SlowAPI)

## ⚡ Quick Start

### 🎯 Option 1: SQLite (Fastest - 5 minutes)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Keep DATABASE_URL=sqlite:///./tax_app.db
python -m alembic upgrade head
python -m uvicorn app.api.server:app --reload

# Frontend (new terminal)
cd fronted
npm install
npm run dev
```

Then:
- **Backend API**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173

### 🐘 Option 2: PostgreSQL with Docker (Recommended)

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Backend (same as above but different .env)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "DATABASE_URL=postgresql://taxuser:taxpass123@localhost:5432/tax_app_db" > .env
python -m alembic upgrade head
python -m uvicorn app.api.server:app --reload

# Frontend
cd fronted
npm install
npm run dev
```

### 🐳 Option 3: Full Docker Stack

```bash
docker-compose up --build
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432

## 📚 Documentation

- **[LOCAL_DEVELOPMENT.md](backend/LOCAL_DEVELOPMENT.md)** - Complete dev setup guide
- **[ENV_CONFIGURATION.md](backend/ENV_CONFIGURATION.md)** - Environment variables & database setup
- **[DEPLOYMENT_GUIDE.md](backend/DEPLOYMENT_GUIDE.md)** - Production deployment (Railway, Render, AWS, Azure)
- **[POSTGRESQL_MIGRATION.md](backend/POSTGRESQL_MIGRATION.md)** - SQLite to PostgreSQL migration guide
- **[PHASE_10_COMPLETE.md](backend/PHASE_10_COMPLETE.md)** - Complete feature implementation status

## 🔐 Security

### API Keys Storage
- API keys encrypted with Fernet (symmetric encryption)
- 512-bit encrypted string storage
- Support for exchange API keys (Binance, Coinbase, Kraken, etc.)
- Support for blockchain RPC nodes (optional custom endpoints)

### Authentication
- JWT tokens with auto-generated strong secrets
- Password hashing with bcrypt
- CORS protection with configurable origins
- Rate limiting on API endpoints (SlowAPI)

### Environment Variables
```bash
# Critical - change in production!
JWT_SECRET_KEY=<64+ random characters>
ENCRYPTION_KEY=<Fernet key>

# For production, see .env.production template
```

## 🚀 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Current user
- `POST /api/v1/auth/logout` - Logout

### Portfolio
- `GET /api/v1/portfolio` - All holdings
- `GET /api/v1/portfolio/summary` - Portfolio summary
- `GET /api/v1/portfolio/unrealized-pnl` - Unrealized gains/losses

### Wallets (Blockchain)
- `POST /api/v1/wallet/import-blockchain` - Import blockchain wallet
- `GET /api/v1/wallet/transactions` - Wallet transactions
- `GET /api/v1/wallet/holdings` - Current holdings

### Exchanges (CCXT)
- `POST /api/v1/exchange/connect` - Add exchange connection
- `GET /api/v1/exchange/list` - List connected exchanges
- `GET /api/v1/exchange/trades` - All exchange trades

### Sync & Automation
- `POST /api/v1/sync/enqueue-job` - Start sync job
- `GET /api/v1/sync/status` - Sync status & history
- `GET /api/v1/sync/settings` - Sync schedule settings

### Tax Exports
- `POST /api/v1/exports/gcap` - GCAP export
- `POST /api/v1/exports/dirpf` - DIRPF export
- `POST /api/v1/exports/irpf-xml` - IRPF XML export

Full API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI: `http://localhost:8000/openapi.json`

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest

# Run specific test
pytest tests/test_auth.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

## 🌍 Supported Networks

### Blockchains
- Ethereum (ETH)
- Polygon (MATIC)
- Binance Smart Chain (BSC)
- Bitcoin (BTC)
- Solana (SOL)
- TRON (TRX)
- Avalanche (AVAX)
- Arbitrum (ARB)
- Optimism (OP)
- Base (BASE)

### Exchanges (100+ via CCXT)
- Tier 1: Binance, Coinbase, Kraken, OKX, Huobi
- Tier 2: KuCoin, Gate.io, Bybit, Gateio, FTX (archived)
- 90+ more supported by CCXT

### DeFi Protocols
- **DEX**: Uniswap V2/V3, Curve, Balancer
- **Lending**: Aave, Compound, RocketPool
- **Staking**: Lido, Yearn, MakerDAO
- **Bridges**: Any ERC-20 bridge transactions
- **NFTs**: OpenSea, Blur, Magic Eden

## 📊 Database Schema

Core Tables:
- `user` - Users with encrypted keys
- `exchange_connection` - API keys for exchanges
- `blockchain_wallet` - Wallet addresses
- `transaction` - Crypto transactions
- `sync_job` - Scheduled sync history
- `portfolio_holding` - Current asset holdings
- `defi_event` - DeFi protocol events

See `app/models/` for complete schema definition.

## 🔄 Auto-Sync System

Built-in scheduled tasks:
- **Wallet Sync**: Every 6 hours (blockchain data)
- **Exchange Sync**: Every 4 hours (trade history)
- **Price Updates**: Every 1 hour (historical prices)

Control via:
- API: `POST /api/v1/sync/enqueue-job`
- Dashboard: Sync Settings tab
- Manual: Database direct

## 🌐 Deployment

### Production Ready
- TLS/SSL support (HTTPS)
- Connection pooling (PostgreSQL)
- Background job queue
- Automated backups
- Error monitoring ready

### Quick Deploy Options
- **Railway.app**: 5 minutes (recommended)
- **Render.com**: 5 minutes
- **AWS RDS + EC2**: 30 minutes
- **Azure**: 20 minutes
- **Fly.io**: 10 minutes

See [DEPLOYMENT_GUIDE.md](backend/DEPLOYMENT_GUIDE.md) for step-by-step instructions.

## 📈 Performance

- **API Response Time**: < 100ms (p95)
- **Database Queries**: Indexed and optimized
- **Background Jobs**: Non-blocking, async
- **Frontend Bundle**: ~150KB gzipped

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is proprietary. All rights reserved.

## 🆘 Support

For issues and questions:
1. Check [LOCAL_DEVELOPMENT.md](backend/LOCAL_DEVELOPMENT.md) troubleshooting
2. Check [ENV_CONFIGURATION.md](backend/ENV_CONFIGURATION.md) for config issues
3. Review API docs: http://localhost:8000/docs
4. Check application logs
5. Open GitHub issue with details

## 🎯 Roadmap

### Phase 1-5 ✅ COMPLETE
- ✅ User authentication & registration
- ✅ Portfolio dashboard
- ✅ Multi-blockchain wallet import
- ✅ 100+ exchange integration (CCXT)
- ✅ DeFi protocol recognition
- ✅ Auto-sync scheduler
- ✅ Brazilian tax forms (GCAP, DIRPF, IRPF XML)

### Phase 6-7 (Planned)
- [ ] Advanced DeFi protocols (+20 more)
- [ ] Machine learning classifier
- [ ] Mobile app (React Native)
- [ ] Multi-country tax support
- [ ] Bank account integration
- [ ] Accounting software bridges

### Phase 8+ (Future)
- [ ] Real-time portfolio alerts
- [ ] Advanced analytics & reporting
- [ ] Accountant/CPA portal
- [ ] Audit trails & compliance
- [ ] API for third-party apps
- [ ] White-label solution

## 📞 Contact

**Email**: [contact@declairo.com](mailto:contact@declairo.com)  
**Website**: [declairo.com](https://declairo.com)  
**Twitter**: [@Declairo](https://twitter.com/declairo)

---

Made with ❤️ for Latin America's crypto community

**Status**: Production Ready ✅  
**Last Updated**: 2024

### Heroku

1. Create Heroku app
2. Set environment variables
3. Deploy backend and frontend separately

### Vercel (Frontend)

1. Connect GitHub repo
2. Set `FRONTEND_ORIGINS` to production URL
3. Deploy

### AWS/DigitalOcean

Use Docker Compose for full stack deployment.

## Security

- Rate limiting (10 requests/minute)
- Input validation
- No API key storage on server
- HTTPS required in production

## Testing

```bash
cd backend
pytest
```

## Architecture

- **Backend**: FastAPI, SQLAlchemy, pandas
- **Frontend**: React, Vite, TypeScript, Tailwind
- **Matching**: Graph-based probabilistic matching
- **Normalization**: Unified transaction schema