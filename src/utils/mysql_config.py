import mysql.connector
from mysql.connector import Error
import logging

logger = logging.getLogger(__name__)

class MySQLManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.use_mysql = False
        self.db_config = {
            'host': '118.139.176.89',
            'database': 'taiwanewshorts',
            'user': 'taiwanewshorts',
            'password': '10Hn1a0!407',
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'port': 3306,
            'connection_timeout': 10,
            'autocommit': True
        }
        print("🗄️ Initializing MySQL for Taiwan News...")
        try:
            self._initialize_mysql()
        except Exception as e:
            print(f"❌ MySQL connection EXCEPTION: {e}")
            import traceback
            print(traceback.format_exc())
            logger.error(f"❌ MySQL connection EXCEPTION: {e}")
            self._create_local_fallback()
            print("⚠️ Using local fallback storage. No real data will be saved or fetched.")

    def _initialize_mysql(self):
        """Initialize MySQL connection and create tables if needed"""
        try:
            # Connect to MySQL
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True)

            # Test connection
            self.cursor.execute("SELECT 1")
            result = self.cursor.fetchone()

            if result:
                self.use_mysql = True
                logger.info("✅ MySQL initialized successfully")
                print("✅ MySQL initialized successfully and connected to database 'taiwanewshorts'")

                # Create tables if they don't exist
                self._create_tables()

        except Error as e:
            logger.error(f"❌ MySQL connection failed: {str(e)}")
            print(f"❌ MySQL connection failed: {str(e)}")
            self._create_local_fallback()

    def _create_tables(self):
        """Create required tables if they do not exist (stub, implement as needed)"""
        # Example: create articles table if not exists
        create_articles_table = '''
        CREATE TABLE IF NOT EXISTS articles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(512),
            summary TEXT,
            content TEXT,
            url VARCHAR(1024),
            image_url VARCHAR(1024),
            category VARCHAR(128),
            source VARCHAR(128),
            scraped_at DATETIME,
            published_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        '''
        self.cursor.execute(create_articles_table)
        self.connection.commit()

    def _create_local_fallback(self):
        # Dummy fallback for local storage (implement as needed)
        self.use_mysql = False
        class DummyLocalStorage:
            def get_articles(self, category, limit, offset=0):
                # Always return a list of dicts for articles
                return [{
                    'title': '', 'summary': '', 'content': '', 'url': '', 'image_url': '',
                    'category': category if category else '', 'source': '', 'scraped_at': '', 'published_at': '',
                    'created_at': '', 'updated_at': ''
                }] * 0
            def get_categories(self):
                return []
            def save_articles(self, articles):
                return len(articles)
        self.local_storage = DummyLocalStorage()

    def fetch_articles_for_api(self, category=None, limit=100, offset=0):
        """Fetch articles for API/web frontend, always returns a list of dicts with correct keys"""
        result = self.get_articles(category, limit, offset)
        articles = result['articles'] if isinstance(result, dict) and 'articles' in result else []
        mapped = []
        for a in articles:
            mapped.append({
                'title': a.get('title', ''),
                'summary': a.get('summary', ''),
                'content': a.get('content', ''),
                'url': a.get('url', ''),
                'image_url': a.get('image_url', ''),
                'category': a.get('category', ''),
                'source': a.get('source', ''),
                'date': a.get('scraped_at') or a.get('published_at') or '',
                'link': a.get('url', ''),
            })
        return mapped

    def get_articles(self, category=None, limit=100, offset=0):
        """Retrieve articles from MySQL database with pagination"""
        if not self.use_mysql:
            return self._get_articles_local(category, limit, offset)

        try:
            # Build query
            base_query = "SELECT * FROM articles"
            count_query = "SELECT COUNT(*) as total FROM articles"

            params = []
            where_clause = ""

            if category and category != 'all':
                where_clause = " WHERE category = %s"
                params.append(category)

            # Get total count
            total_query = count_query + where_clause
            self.cursor.execute(total_query, params)
            total_result = self.cursor.fetchone()
            total_count = total_result['total'] if total_result else 0

            # Get articles with pagination
            articles_query = base_query + where_clause + " ORDER BY scraped_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            self.cursor.execute(articles_query, params)
            articles = self.cursor.fetchall()

            # Convert datetime objects to strings for JSON serialization
            for article in articles:
                for field in ['scraped_at', 'published_at', 'created_at', 'updated_at']:
                    if field in article and article[field]:
                        if hasattr(article[field], 'strftime'):
                            article[field] = article[field].strftime('%Y-%m-%d %H:%M:%S')

            logger.info(f"✅ Retrieved {len(articles)} articles from MySQL (offset: {offset}, total: {total_count})")

            return {
                'articles': articles,
                'total': total_count,
                'hasMore': (offset + len(articles)) < total_count
            }

        except Error as e:
            logger.error(f"❌ Error retrieving articles from MySQL: {str(e)}")
            print(f"⚠️  MySQL get failed: {str(e)}")
            self._create_local_fallback()
            return self._get_articles_local(category, limit, offset)

    def _get_articles_local(self, category=None, limit=100, offset=0):
        """Get articles from local storage with pagination"""
        articles = self.local_storage.get_articles(category, limit + offset)

        if category and category != 'all':
            articles = [a for a in articles if a.get('category') == category]

        total = len(articles)
        paginated_articles = articles[offset:offset+limit]

        return {
            'articles': paginated_articles,
            'total': total,
            'hasMore': (offset + len(paginated_articles)) < total
        }

    def get_categories(self):
        """Get unique categories from MySQL database"""
        if not self.use_mysql:
            return self.local_storage.get_categories()

        try:
            query = "SELECT DISTINCT category FROM articles WHERE category IS NOT NULL ORDER BY category"
            self.cursor.execute(query)
            results = self.cursor.fetchall()

            categories = [row['category'] for row in results]
            logger.info(f"✅ Retrieved {len(categories)} categories from MySQL: {categories}")

            return categories

        except Error as e:
            logger.error(f"❌ Error retrieving categories from MySQL: {str(e)}")
            return self.local_storage.get_categories()

    def test_connection(self):
        """Test MySQL connection"""
        if not self.use_mysql:
            return False
        try:
            self.cursor.execute("SELECT 1")
            result = self.cursor.fetchone()
            return result is not None
        except Error as e:
            logger.error(f"MySQL connection test failed: {str(e)}")
            return False

    def close_connection(self):
        """Close MySQL connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")

    def __del__(self):
        """Destructor to ensure connection is closed"""
        self.close_connection()

    def save_articles(self, articles):
        """Save a list of articles to the MySQL database."""
        if not self.use_mysql:
            return self.local_storage.save_articles(articles)
        if not articles:
            return 0
        insert_query = '''
        INSERT INTO articles (title, summary, content, url, image_url, category, source, scraped_at, published_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            summary=VALUES(summary),
            content=VALUES(content),
            image_url=VALUES(image_url),
            category=VALUES(category),
            source=VALUES(source),
            scraped_at=VALUES(scraped_at),
            published_at=VALUES(published_at),
            updated_at=NOW()
        '''
        count = 0
        for article in articles:
            try:
                self.cursor.execute(insert_query, (
                    article.get('title'),
                    article.get('summary'),
                    article.get('content'),
                    article.get('url'),
                    article.get('image_url'),
                    article.get('category'),
                    article.get('source'),
                    article.get('scraped_at'),
                    article.get('published_at')
                ))
                count += 1
            except Exception as e:
                logger.error(f"Error saving article: {e}")
        self.connection.commit()
        logger.info(f"✅ Saved {count} articles to MySQL.")
        return count

def test_mysql_connection():
    connection = None
    try:
        # First, try connecting without specifying a database
        config_no_db = {
            'host': '118.139.176.89',
            'user': 'taiwanewshorts',  # <-- updated user
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
            'user': 'taiwanewshorts',  # <-- updated user
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
        if hasattr(e, 'errno'):
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
