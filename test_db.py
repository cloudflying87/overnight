#!/usr/bin/env python
"""
Quick script to test database connection
"""
import os
import sys
import django

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection
from django.core.management import call_command

def test_connection():
    """Test database connection"""
    try:
        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Database connection successful!")
            print(f"   PostgreSQL version: {version[0]}")

            # Get database name
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()
            print(f"   Connected to database: {db_name[0]}")

            # Check if tables exist
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()

            if tables:
                print(f"\n📊 Existing tables ({len(tables)}):")
                for table in tables[:10]:  # Show first 10
                    print(f"   - {table[0]}")
                if len(tables) > 10:
                    print(f"   ... and {len(tables) - 10} more")
            else:
                print("\n⚠️  No tables found. Run migrations first:")
                print("   python manage.py migrate")

        return True

    except Exception as e:
        print(f"❌ Database connection failed!")
        print(f"   Error: {str(e)}")
        print("\n🔍 Troubleshooting:")
        print("   1. Check that PostgreSQL is running")
        print("   2. Verify credentials in .env file")
        print("   3. Ensure network connectivity to 'hercules' (172.16.29.5)")
        print("   4. Check firewall rules for port 5432")
        return False

if __name__ == '__main__':
    print("🔌 Testing database connection...\n")
    success = test_connection()
    sys.exit(0 if success else 1)
