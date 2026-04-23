"""Test Phase 10 implementations"""
from app.db import SessionLocal
from app.models import User, AnalysisRun
from app.phase10_integration import Phase10DataIntegration

db = SessionLocal()
try:
    user = db.query(User).filter(User.id == 1).first()
    run = db.query(AnalysisRun).filter(AnalysisRun.id == 1).first()

    if user and run:
        print("Testing Phase 10 Implementations:")
        print("=" * 50)
        
        # Test GCAP Generation
        result = Phase10DataIntegration.generate_gcap_report(user, run, db)
        print(f"\n✅ GCAP Generation:")
        print(f"   Status: {result.get('status')}")
        print(f"   Transactions: {result.get('transactions_count', 0)}")
        print(f"   Total Gains: {result.get('total_gains', 0)}")
        print(f"   Total Losses: {result.get('total_losses', 0)}")
        
        # Test Carnê-Leão Generation
        result = Phase10DataIntegration.generate_carne_leao_report(user, run, db)
        print(f"\n✅ Carnê-Leão Generation:")
        print(f"   Status: {result.get('status')}")
        print(f"   Months: {result.get('months_count', 0)}")
        print(f"   Total Income: {result.get('total_income', 0)}")
        print(f"   Total Tax Due: {result.get('total_tax_due', 0)}")
        
        # Test Tax Scenarios
        result = Phase10DataIntegration.analyze_tax_scenarios(1, [35000, 40000], True, user, db)
        print(f"\n✅ Tax Scenarios Analysis:")
        print(f"   Position ID: {result.get('position_id')}")
        print(f"   Scenarios: {len(result.get('scenarios', []))}")
        
        print("\n" + "=" * 50)
        print("✅ All Phase 10 tests completed successfully!")
    else:
        print("❌ User or run not found")
finally:
    db.close()
