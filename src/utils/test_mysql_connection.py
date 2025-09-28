import mysql.connector
from mysql.connector import Error
import sys


def test_mysql_connection():
    connection = None
    try:
        # First, try connecting without specifying a database
        config_no_db = {
            'host': '118.139.176.89',
            'user': 'taiwanewshorts',
            'password': '10Hn1a0!407',
            'port': 3306,
            'connection_timeout': 10
        }

        print("Step 1: Testing connection without database...")
        connection = mysql.connector.connect(**config_no_db)

        if connection.is_connected():
            print("✅ Basic connection successful!")
            cursor = connection.cursor()

            # Check what databases the user can see
            print("\nStep 2: Checking available databases...")
            cursor.execute("SHOW DATABASES;")
            databases = cursor.fetchall()
            print("Available databases:")
            for db in databases:
                print(f"  - {db[0]}")
            db_names = [db[0] for db in databases]

            # Create the database if it does not exist
            if 'taiwanewshorts' not in db_names:
                print("\nStep 2b: 'taiwanewshorts' database not found. Attempting to create it...")
                try:
                    cursor.execute("CREATE DATABASE taiwanewshorts CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                    print("✅ 'taiwanewshorts' database created successfully!")
                except Error as create_db_error:
                    print(f"❌ Failed to create 'taiwanewshorts' database: {create_db_error}")
                    return False
                # Refresh database list
                cursor.execute("SHOW DATABASES;")
                databases = cursor.fetchall()
                db_names = [db[0] for db in databases]

            # Check user privileges
            print("\nStep 3: Checking user privileges...")
            cursor.execute("SHOW GRANTS FOR CURRENT_USER();")
            grants = cursor.fetchall()
            print("Current user grants:")
            for grant in grants:
                print(f"  - {grant[0]}")

            # Try to use the specific database
            print("\nStep 4: Attempting to use 'taiwanewshorts' database...")
            try:
                cursor.execute("USE taiwanewshorts;")
                print("✅ Successfully switched to 'taiwanewshorts' database!")

                # Show tables if successful
                cursor.execute("SHOW TABLES;")
                tables = cursor.fetchall()
                print(f"Tables in database ({len(tables)} total):")
                for table in tables[:10]:
                    print(f"  - {table[0]}")
                if len(tables) > 10:
                    print(f"  ... and {len(tables) - 10} more tables")

            except Error as db_error:
                print(f"❌ Cannot access 'taiwanewshorts' database: {db_error}")
                return False

            cursor.close()

        # Now try with the original config including database
        print("\nStep 5: Testing direct database connection...")
        connection.close()

        config_with_db = {
            'host': '118.139.176.89',
            'database': 'taiwanewshorts',
            'user': 'taiwanewshorts',
            'password': '10Hn1a0!407',
            'port': 3306,
            'connection_timeout': 10
        }

        connection = mysql.connector.connect(**config_with_db)

        if connection.is_connected():
            print("✅ Direct database connection successful!")
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE(), VERSION(), NOW();")
            result = cursor.fetchone()
            print(f"Connected to database: {result[0]}")
            print(f"Server version: {result[1]}")
            print(f"Current time: {result[2]}")
            cursor.close()
            print("\n✅ All connection tests completed successfully!")

    except Error as e:
        print(f"❌ Error while connecting to MySQL: {e}")
        if e.errno:
            print(f"Error code: {e.errno}")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    finally:
        if connection and connection.is_connected():
            connection.close()
            print("MySQL connection closed.")

    return True


if __name__ == "__main__":
    test_mysql_connection()