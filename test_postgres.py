#!/usr/bin/env python3
"""
PostgreSQL Connection Test Script for Budget Management System
"""

import os
import sys
import psycopg
from decouple import config

def test_postgresql_connection():
    """Test PostgreSQL connection with different configurations."""
    
    print("Testing PostgreSQL Connection...")
    print("=" * 50)
    
    # Test configurations
    configs = [
        {
            'name': 'Default PostgreSQL',
            'host': 'localhost',
            'port': 5432,
            'user': 'postgres',
            'password': 'admin',
            'database': 'postgres'
        },
        {
            'name': 'Budget Management DB',
            'host': 'localhost', 
            'port': 5432,
            'user': 'postgres',
            'password': 'admin',
            'database': 'budget_management'
        }
    ]
    
    for config in configs:
        print(f"\nTesting: {config['name']}")
        print(f"Host: {config['host']}:{config['port']}")
        print(f"User: {config['user']}")
        print(f"Database: {config['database']}")
        
        try:
            # Test connection
            conn = psycopg.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                dbname=config['database']
            )
            
            # Test query
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                print(f"✅ Connection successful!")
                print(f"PostgreSQL version: {version[0]}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    
    print("\n" + "=" * 50)
    print("Connection test completed!")

def test_django_postgresql():
    """Test Django with PostgreSQL settings."""
    
    print("\nTesting Django PostgreSQL Integration...")
    print("=" * 50)
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_system.settings')
    
    try:
        import django
        django.setup()
        
        from django.db import connection
        
        # Test database connection with a simple query
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            db_name = cursor.fetchone()
            print(f"✅ Django PostgreSQL connection successful!")
            print(f"Connected to database: {db_name[0]}")
            
    except Exception as e:
        print(f"❌ Django PostgreSQL connection failed: {e}")

def test_postgresql_installation():
    """Test if psycopg is properly installed."""
    
    print("Testing PostgreSQL Installation...")
    print("=" * 50)
    
    try:
        import psycopg
        print(f"✅ psycopg version: {psycopg.__version__}")
    except ImportError as e:
        print(f"❌ psycopg not installed: {e}")
        print("Install with: pip install psycopg[binary]==3.1.18")
        return False
    
    try:
        import psycopg.conninfo
        print("✅ psycopg.conninfo module available")
    except ImportError as e:
        print(f"❌ psycopg.conninfo not available: {e}")
        return False
    
    return True

def check_postgresql_service():
    """Check if PostgreSQL service is running."""
    
    print("Checking PostgreSQL Service...")
    print("=" * 50)
    
    import subprocess
    
    try:
        # Check if PostgreSQL is running
        result = subprocess.run(['brew', 'services', 'list'], 
                              capture_output=True, text=True)
        
        if 'postgresql' in result.stdout:
            print("✅ PostgreSQL service found in brew services")
            if 'started' in result.stdout:
                print("✅ PostgreSQL service is running")
            else:
                print("⚠️  PostgreSQL service is not running")
                print("Start with: brew services start postgresql@14")
        else:
            print("❌ PostgreSQL service not found")
            
    except Exception as e:
        print(f"❌ Error checking PostgreSQL service: {e}")

def test_database_creation():
    """Test creating the budget_management database."""
    
    print("Testing Database Creation...")
    print("=" * 50)
    
    try:
        # Try to connect to postgres database first
        conn = psycopg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='admin',
            dbname='postgres'
        )
        
        with conn.cursor() as cur:
            # Check if budget_management database exists
            cur.execute("SELECT datname FROM pg_database WHERE datname = 'budget_management';")
            result = cur.fetchone()
            
            if result:
                print("✅ budget_management database already exists")
            else:
                print("⚠️  budget_management database does not exist")
                print("Create with: createdb -U postgres budget_management")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    print("PostgreSQL Connection Test for Budget Management System")
    print("=" * 60)
    
    # Test installation first
    if test_postgresql_installation():
        # Check service status
        check_postgresql_service()
        
        # Test database creation
        test_database_creation()
        
        # Test direct connections
        test_postgresql_connection()
        
        # Test Django integration
        test_django_postgresql()
    
    print("\n" + "=" * 60)
    print("All tests completed!")