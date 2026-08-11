import os
import sys

# Override the environment variable
os.environ["DATABASE_URL"] = "postgresql://postgres:Baxter:(208132);@db.punjqgzdbtzepeqphuug.supabase.co:5432/postgres"

# Import and run the main function from run_migrations
try:
    import run_migrations
    run_migrations.main()
except Exception as e:
    print(f"Error running migrations: {e}")
    sys.exit(1)
