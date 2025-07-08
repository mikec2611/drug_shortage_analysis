import psycopg2
import os
from psycopg2 import OperationalError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_database_connection():
    """Test connection to PostgreSQL database with detailed error reporting."""
    
    # Database configuration
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST'),
        'port': os.environ.get('DB_PORT'),
        'database': os.environ.get('DB_NAME'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
        # 'connect_timeout': 10  # 10 second timeout
    }
    
    # Check if credentials are provided
    if not DB_CONFIG['user'] or not DB_CONFIG['password']:
        print("❌ ERROR: Database credentials not found!")
        print("Please create a .env file with the following variables:")
        print("  DB_USER=your_username")
        print("  DB_PASSWORD=your_password")
        print("  DB_NAME=your_database_name (optional)")
        return False
    
    print("🔧 Testing database connection...")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"Port: {DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"User: {DB_CONFIG['user']}")
    print("-" * 50)
    
    try:
        # Attempt to connect
        print("⏳ Attempting to connect...")
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Test the connection
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        
        print("✅ CONNECTION SUCCESSFUL!")
        print(f"Database version: {db_version}")
        
        # Close connections
        cursor.close()
        conn.close()
        return True
        
    except OperationalError as e:
        print("❌ CONNECTION FAILED!")
        error_msg = str(e)
        
        if "Connection timed out" in error_msg:
            print("\n🔍 DIAGNOSIS: Connection timeout")
            print("This usually means:")
            print("1. RDS Security Group is blocking your IP address")
            print("2. Database is not publicly accessible")
            print("3. Database is in a private subnet")
            print("\n🔧 SOLUTIONS:")
            print("1. Update RDS Security Group to allow your IP on port 5432")
            print("2. Ensure database has 'Public access' enabled")
            print("3. Check VPC and subnet configuration")
            
        elif "authentication failed" in error_msg:
            print("\n🔍 DIAGNOSIS: Authentication failed")
            print("Check your username and password")
            
        elif "database" in error_msg and "does not exist" in error_msg:
            print("\n🔍 DIAGNOSIS: Database does not exist")
            print("Check your database name")
            
        else:
            print(f"\n🔍 DIAGNOSIS: Other error")
            print(f"Error details: {error_msg}")
            
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 DATABASE CONNECTION TEST")
    print("=" * 60)
    success = test_database_connection()
    print("=" * 60)
    
    if success:
        print("✅ Connection test passed! You can now run load_to_database.py")
    else:
        print("❌ Connection test failed. Please fix the issues above first.") 