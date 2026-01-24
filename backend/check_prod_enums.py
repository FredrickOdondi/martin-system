#!/usr/bin/env python3
"""Check production database enum values"""
import asyncio
import asyncpg
import os
import sys

async def check_enums():
    # Get DATABASE_URL from environment (Railway will inject it)
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    
    print(f"Connecting to database...")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Check MeetingStatus enum
        print("\n=== MeetingStatus Enum Values ===")
        rows = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'meetingstatus') 
            ORDER BY enumsortorder;
        """)
        for row in rows:
            print(f"  - {row['enumlabel']}")
        
        # Check RsvpStatus enum
        print("\n=== RsvpStatus Enum Values ===")
        rows = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'rsvpstatus') 
            ORDER BY enumsortorder;
        """)
        for row in rows:
            print(f"  - {row['enumlabel']}")
        
        # Check ActionItemStatus enum
        print("\n=== ActionItemStatus Enum Values ===")
        rows = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'actionitemstatus') 
            ORDER BY enumsortorder;
        """)
        for row in rows:
            print(f"  - {row['enumlabel']}")
        
        # Check ProjectStatus enum
        print("\n=== ProjectStatus Enum Values ===")
        rows = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'projectstatus') 
            ORDER BY enumsortorder;
        """)
        for row in rows:
            print(f"  - {row['enumlabel']}")
        
        # Check actual data in meetings table
        print("\n=== Sample Meeting Status Values (first 5) ===")
        rows = await conn.fetch("""
            SELECT id, title, status 
            FROM meetings 
            LIMIT 5;
        """)
        for row in rows:
            print(f"  - {row['title'][:50]}: {row['status']}")
        
        await conn.close()
        print("\n✓ Check complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(check_enums())
