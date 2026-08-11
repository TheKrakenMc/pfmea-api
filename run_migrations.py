import os
import re
import sys
import psycopg2
from dotenv import load_dotenv

def main():
    # 1. Load environment variables
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL", "").strip().strip('"').strip("'")
    if not database_url:
        print("Error: DATABASE_URL not found in .env file.")
        sys.exit(1)
        
    print(f"Original DATABASE_URL from .env: {database_url}")
    
    # 2. Clean DATABASE_URL for psycopg2 compatibility
    # psycopg2 doesn't understand the '+psycopg2' or '+asyncpg' schemes, it expects 'postgresql://'
    cleaned_url = database_url.replace("postgresql+psycopg2://", "postgresql://").replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"Connecting to database...")
    try:
        conn = psycopg2.connect(cleaned_url)
        # Enable autocommit so SQL internal BEGIN/COMMIT blocks manage their own transactions
        conn.autocommit = True
        print("Successfully connected to the database!")
    except Exception as e:
        print(f"Database connection error: {e}")
        sys.exit(1)
        
    cursor = conn.cursor()
    
    try:
        # 3. Ensure the pfmea schema exists
        cursor.execute("CREATE SCHEMA IF NOT EXISTS pfmea;")
        print("Ensured schema 'pfmea' exists.")
        
        # Set search path to pfmea
        cursor.execute("SET search_path TO pfmea, public;")
        print("Set search_path to 'pfmea, public'.")
        
        # 4. Check if base tables exist (e.g. check if 'roles' table exists in pfmea schema)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'pfmea' AND table_name = 'roles'
            );
        """)
        roles_exists = cursor.fetchone()[0]
        
        if not roles_exists:
            print("\nTable 'roles' not found in 'pfmea' schema. Initializing base schema from PFMEA_v2.sql...")
            base_sql_path = os.path.join(os.path.dirname(__file__), "PFMEA_v2.sql")
            
            if not os.path.isfile(base_sql_path):
                print(f"Error: Base SQL file '{base_sql_path}' not found!")
                sys.exit(1)
                
            with open(base_sql_path, "r", encoding="utf-8") as f:
                base_sql = f.read()
                
            # Let's fix the case-insensitive 'timestampz' -> 'timestamptz' typo in PFMEA_v2.sql
            # and write the fixed SQL back to PFMEA_v2.sql so it's clean for the user.
            fixed_sql, count = re.subn(r'\btimestampz\b', 'timestamptz', base_sql, flags=re.IGNORECASE)
            if count > 0:
                print(f"Fixed {count} instances of typo 'timestampz' to 'timestamptz' in SQL.")
                with open(base_sql_path, "w", encoding="utf-8") as f:
                    f.write(fixed_sql)
                print("Saved fixed SQL back to PFMEA_v2.sql.")
                base_sql = fixed_sql
                
            try:
                print("Executing base schema creation...")
                cursor.execute(base_sql)
                print("Base schema successfully initialized!")
            except Exception as base_err:
                print(f"Error executing base schema: {base_err}")
                sys.exit(1)
        else:
            print("\nBase schema already initialized ('roles' table exists). Skipping base initialization.")
            
        # 5. Ensure migration history table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Ensured 'migration_history' table exists.")
        
        # 6. Get list of migrations from directory
        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        if not os.path.isdir(migrations_dir):
            print(f"Error: Migrations directory '{migrations_dir}' not found.")
            sys.exit(1)
            
        sql_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith(".sql")])
        
        if not sql_files:
            print("No migration SQL files found in the migrations folder.")
            sys.exit(0)
            
        print(f"Found {len(sql_files)} migration files in {migrations_dir}.")
        
        # 7. Run pending migrations
        for file_name in sql_files:
            # Check if already applied
            cursor.execute("SELECT id FROM migration_history WHERE migration_name = %s;", (file_name,))
            if cursor.fetchone():
                print(f"Migration '{file_name}' already applied. Skipping.")
                continue
                
            file_path = os.path.join(migrations_dir, file_name)
            print(f"\nApplying migration: {file_name} ...")
            
            with open(file_path, "r", encoding="utf-8") as f:
                sql_content = f.read()
                
            try:
                cursor.execute(sql_content)
                
                # Record successful application
                cursor.execute(
                    "INSERT INTO migration_history (migration_name) VALUES (%s);",
                    (file_name,)
                )
                print(f"Successfully applied: {file_name}")
            except Exception as sql_err:
                print(f"Error executing migration '{file_name}': {sql_err}")
                print("Aborting remaining migrations.")
                sys.exit(1)
                
        print("\nAll pending migrations completed successfully!")
        
    finally:
        cursor.close()
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()
