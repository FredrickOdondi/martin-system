"""
Seed Investor Database with Realistic African Infrastructure Investors

This script populates the database with diverse investors including:
- Development Finance Institutions (DFIs)
- Green Bond Funds
- Sovereign Wealth Funds
- Private Equity/VC Firms
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.models import Investor
from loguru import logger


async def seed_investors():
    """Seed the database with realistic African infrastructure investors."""
    
    investors_data = [
        # Development Finance Institutions (DFIs)
        {
            "name": "African Development Bank (AfDB)",
            "investor_type": "DFI",
            "sector_preferences": ["Infrastructure", "Energy", "Transport", "Water"],
            "ticket_size_min": 50.0,  # $50M
            "ticket_size_max": 500.0,  # $500M
            "geographic_focus": ["West Africa", "East Africa", "Central Africa", "Southern Africa", "North Africa"],
            "investment_instruments": ["Debt", "Equity", "Grants", "Blended Finance"],
            "total_commitments_usd": 5000000000.0,  # $5B
            "contact_email": "projects@afdb.org",
        },
        {
            "name": "International Finance Corporation (IFC)",
            "investor_type": "DFI",
            "sector_preferences": ["Infrastructure", "Energy", "Manufacturing", "Agribusiness"],
            "ticket_size_min": 30.0,
            "ticket_size_max": 400.0,
            "geographic_focus": ["West Africa", "East Africa", "Southern Africa"],
            "investment_instruments": ["Debt", "Equity", "Blended Finance"],
            "total_commitments_usd": 8000000000.0,  # $8B
            "contact_email": "africa@ifc.org",
        },
        {
            "name": "European Investment Bank (EIB)",
            "investor_type": "DFI",
            "sector_preferences": ["Infrastructure", "Energy", "Climate", "Transport"],
            "ticket_size_min": 40.0,
            "ticket_size_max": 350.0,
            "geographic_focus": ["West Africa", "North Africa", "East Africa"],
            "investment_instruments": ["Debt", "Grants", "Technical Assistance"],
            "total_commitments_usd": 3500000000.0,
            "contact_email": "africa@eib.org",
        },
        
        # Green Bond Funds
        {
            "name": "Green Climate Fund",
            "investor_type": "Climate Fund",
            "sector_preferences": ["Energy", "Climate", "Agriculture", "Water"],
            "ticket_size_min": 20.0,
            "ticket_size_max": 250.0,
            "geographic_focus": ["West Africa", "East Africa", "Central Africa", "Southern Africa"],
            "investment_instruments": ["Grants", "Concessional Loans", "Equity"],
            "total_commitments_usd": 2000000000.0,
            "contact_email": "info@gcfund.org",
        },
        {
            "name": "Climate Investment Funds",
            "investor_type": "Climate Fund",
            "sector_preferences": ["Energy", "Climate", "Infrastructure"],
            "ticket_size_min": 15.0,
            "ticket_size_max": 200.0,
            "geographic_focus": ["West Africa", "East Africa", "Southern Africa"],
            "investment_instruments": ["Grants", "Concessional Loans", "Blended Finance"],
            "total_commitments_usd": 1500000000.0,
            "contact_email": "cif@worldbank.org",
        },
        
        # Sovereign Wealth Funds
        {
            "name": "Nigeria Sovereign Investment Authority (NSIA)",
            "investor_type": "Sovereign Wealth Fund",
            "sector_preferences": ["Infrastructure", "Energy", "Agriculture", "Real Estate"],
            "ticket_size_min": 25.0,
            "ticket_size_max": 300.0,
            "geographic_focus": ["West Africa", "Nigeria"],
            "investment_instruments": ["Equity", "Debt"],
            "total_commitments_usd": 2500000000.0,
            "contact_email": "info@nsia.com.ng",
        },
        {
            "name": "Ghana Infrastructure Investment Fund (GIIF)",
            "investor_type": "Sovereign Wealth Fund",
            "sector_preferences": ["Infrastructure", "Energy", "Transport"],
            "ticket_size_min": 10.0,
            "ticket_size_max": 150.0,
            "geographic_focus": ["West Africa", "Ghana"],
            "investment_instruments": ["Equity", "Debt", "Blended Finance"],
            "total_commitments_usd": 800000000.0,
            "contact_email": "info@giif.gov.gh",
        },
        
        # Private Equity / VC
        {
            "name": "Africa Infrastructure Investment Managers (AIIM)",
            "investor_type": "Private Equity",
            "sector_preferences": ["Infrastructure", "Energy", "Transport", "Telecom"],
            "ticket_size_min": 20.0,
            "ticket_size_max": 200.0,
            "geographic_focus": ["West Africa", "East Africa", "Southern Africa"],
            "investment_instruments": ["Equity", "Mezzanine"],
            "total_commitments_usd": 1200000000.0,
            "contact_email": "info@ai-im.com",
        },
        {
            "name": "Helios Investment Partners",
            "investor_type": "Private Equity",
            "sector_preferences": ["Infrastructure", "Energy", "Telecom", "Financial Services"],
            "ticket_size_min": 30.0,
            "ticket_size_max": 250.0,
            "geographic_focus": ["West Africa", "East Africa", "Southern Africa", "North Africa"],
            "investment_instruments": ["Equity"],
            "total_commitments_usd": 3000000000.0,
            "contact_email": "info@heliosinvestment.com",
        },
        {
            "name": "Emerging Capital Partners (ECP)",
            "investor_type": "Private Equity",
            "sector_preferences": ["Infrastructure", "Energy", "Manufacturing", "Consumer"],
            "ticket_size_min": 25.0,
            "ticket_size_max": 200.0,
            "geographic_focus": ["West Africa", "Central Africa", "East Africa"],
            "investment_instruments": ["Equity", "Growth Capital"],
            "total_commitments_usd": 2200000000.0,
            "contact_email": "info@ecpinvestments.com",
        },
        
        # Regional Development Banks
        {
            "name": "West African Development Bank (BOAD)",
            "investor_type": "Regional Bank",
            "sector_preferences": ["Infrastructure", "Energy", "Transport", "Agriculture"],
            "ticket_size_min": 15.0,
            "ticket_size_max": 180.0,
            "geographic_focus": ["West Africa"],
            "investment_instruments": ["Debt", "Grants", "Technical Assistance"],
            "total_commitments_usd": 1800000000.0,
            "contact_email": "boad@boad.org",
        },
        {
            "name": "ECOWAS Bank for Investment and Development (EBID)",
            "investor_type": "Regional Bank",
            "sector_preferences": ["Infrastructure", "Energy", "Agriculture", "SME"],
            "ticket_size_min": 10.0,
            "ticket_size_max": 120.0,
            "geographic_focus": ["West Africa"],
            "investment_instruments": ["Debt", "Equity", "Guarantees"],
            "total_commitments_usd": 900000000.0,
            "contact_email": "info@ebid.org",
        },
        
        # Impact Investors
        {
            "name": "Convergence Blended Finance",
            "investor_type": "Impact Investor",
            "sector_preferences": ["Infrastructure", "Energy", "Health", "Education"],
            "ticket_size_min": 5.0,
            "ticket_size_max": 100.0,
            "geographic_focus": ["West Africa", "East Africa", "Southern Africa"],
            "investment_instruments": ["Blended Finance", "Grants", "Technical Assistance"],
            "total_commitments_usd": 500000000.0,
            "contact_email": "info@convergence.finance",
        },
        {
            "name": "Africa50 Infrastructure Fund",
            "investor_type": "Infrastructure Fund",
            "sector_preferences": ["Infrastructure", "Energy", "Transport", "ICT"],
            "ticket_size_min": 30.0,
            "ticket_size_max": 300.0,
            "geographic_focus": ["West Africa", "East Africa", "Central Africa", "Southern Africa"],
            "investment_instruments": ["Equity", "Debt", "Project Development"],
            "total_commitments_usd": 2000000000.0,
            "contact_email": "info@africa50.com",
        },
        
        # Bilateral Development Agencies
        {
            "name": "USAID Development Credit Authority",
            "investor_type": "Bilateral Agency",
            "sector_preferences": ["Infrastructure", "Energy", "Agriculture", "Health"],
            "ticket_size_min": 10.0,
            "ticket_size_max": 150.0,
            "geographic_focus": ["West Africa", "East Africa"],
            "investment_instruments": ["Guarantees", "Grants", "Technical Assistance"],
            "total_commitments_usd": 1000000000.0,
            "contact_email": "dca@usaid.gov",
        }
    ]
    
    async with AsyncSessionLocal() as session:
        # Check if investors already exist
        from sqlalchemy import select
        result = await session.execute(select(Investor))
        existing = result.scalars().all()
        
        if len(existing) > 0:
            logger.info(f"Found {len(existing)} existing investors. Skipping seed.")
            return
        
        logger.info(f"Seeding {len(investors_data)} investors...")
        
        for data in investors_data:
            investor = Investor(**data)
            session.add(investor)
        
        await session.commit()
        logger.info(f"✓ Successfully seeded {len(investors_data)} investors")


if __name__ == "__main__":
    asyncio.run(seed_investors())
