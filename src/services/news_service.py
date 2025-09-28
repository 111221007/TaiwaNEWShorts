# Business logic for scraping and saving articles
from src.scrapers.news_scraper import NewsScraper
from src.models.article import Article
from src.utils.mysql_config import MySQLManager
from datetime import datetime

class NewsService:
    def __init__(self):
        self.scraper = NewsScraper()
        self.mysql_manager = MySQLManager()

    def scrape_and_save(self):
        articles_raw = self.scraper.scrape_all_sources()
        print(f"[DEBUG] Scraper returned {len(articles_raw)} articles.")
        # Remove 'link' key if present in any article dict
        cleaned_articles = []
        for a in articles_raw:
            if 'link' in a:
                a = dict(a)  # copy to avoid mutating original
                a.pop('link')
            cleaned_articles.append(a)
        articles = [Article(**a) for a in cleaned_articles]
        saved_count = self.mysql_manager.save_articles([a.to_dict() for a in articles])
        print(f"[DEBUG] Saved {saved_count} articles to the database.")
        return articles

    def get_articles(self, category=None, limit=15, offset=0):
        result = self.mysql_manager.get_articles(category, limit, offset)
        return result

    def get_categories(self):
        return self.mysql_manager.get_categories()

    def get_status(self):
        mysql_connected = self.mysql_manager.test_connection()
        return {
            'status': 'running',
            'mysql_connected': mysql_connected,
            'database': 'MySQL (taiwanewshorts)',
            'timestamp': datetime.now().isoformat()
        }
