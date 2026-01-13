#!/usr/bin/env python3
"""
Script to inspect PostgreSQL enum values in the database.
Run this with the DATABASE_URL environment variable set to inspect actual enum values.

Usage:
    DATABASE_URL="postgresql://..." python inspect_enums.py
    
Or via Railway:
    railway run python inspect_enums.py
"""
import os
import sys

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2-binary...")
    os.system("pip install psycopg2-binary")
    import psycopg2

def get_enum_values(conn, enum_name):
    """Get all values for a given enum type."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT enumlabel 
        FROM pg_enum 
        WHERE enumtypid = %s::regtype 
        ORDER BY enumsortorder
    """, (enum_name,))
    return [row[0] for row in cursor.fetchall()]

def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set!")
        print("Usage: DATABASE_URL='postgresql://...' python inspect_enums.py")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        print("Connected to database successfully!\n")
        
        # List of enums to inspect
        enums = [
            "minutesstatus",
            "meetingstatus",
            "userrole",
            "projectstatus",
            "actionitemstatus",
            "actionitempriority",
            "rsvpstatus",
            "dependencystatus",
            "twgpillar"
        ]
        
        print("=" * 60)
        print("ENUM VALUES IN DATABASE")
        print("=" * 60)
        
        for enum_name in enums:
            try:
                values = get_enum_values(conn, enum_name)
                print(f"\n{enum_name}:")
                for v in values:
                    print(f"  - '{v}'")
            except Exception as e:
                print(f"\n{enum_name}: ERROR - {e}")
        
        print("\n" + "=" * 60)
        conn.close()
        
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
