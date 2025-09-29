from flask import Flask, jsonify, request, render_template
import os
import sys
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.news_service import NewsService

app = Flask(__name__, template_folder='../../templates', static_folder='../../static')
news_service = NewsService()  # Use service layer for all business logic

def scrape_and_update():
    """Background job to scrape news and update MySQL database"""
    try:
        logger.info("Starting news scraping...")
        articles = news_service.scrape_and_save()
        logger.info(f"Successfully scraped and saved {len(articles)} articles at {datetime.now()}")

        # Log categories found
        categories = set(article.category for article in articles)
        logger.info(f"Categories found: {categories}")

        # Log sources
        sources = set(article.source for article in articles)
        logger.info(f"Sources found: {sources}")

    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(scrape_and_update, 'interval', minutes=30)
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/articles')
def get_articles():
    """Get articles with pagination support"""
    try:
        category = request.args.get('category', 'all')
        limit = int(request.args.get('limit', 15))
        offset = int(request.args.get('offset', 0))

        result = news_service.get_articles(category=category, limit=limit, offset=offset)
        articles = [
            {
                'title': a.get('title', ''),
                'summary': a.get('summary', ''),
                'content': a.get('content', ''),
                'url': a.get('url', ''),
                'image_url': a.get('image_url', ''),
                'category': a.get('category', ''),
                'source': a.get('source', ''),
                'date': a.get('scraped_at') or a.get('published_at') or '',
                'link': a.get('url', ''),
            } for a in result.get('articles', [])
        ]
        # Add MySQL connection status for debugging
        mysql_connected = getattr(news_service.mysql_manager, 'use_mysql', False)
        return jsonify({
            'articles': articles,
            'total': result.get('total', 0),
            'hasMore': result.get('hasMore', False),
            'success': True,
            'mysql_connected': mysql_connected
        })

    except Exception as e:
        logger.error(f"Error in get_articles: {str(e)}")
        return jsonify({
            'articles': [],
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/categories')
def get_categories():
    """Get available categories"""
    try:
        categories = news_service.get_categories()
        return jsonify({'categories': categories})
    except Exception as e:
        logger.error(f"Error in get_categories: {str(e)}")
        return jsonify({'categories': [], 'error': str(e)}), 500

@app.route('/api/scrape-now')
def manual_scrape():
    """Manual trigger for scraping (for testing)"""
    try:
        logger.info("Manual scrape triggered via API.")
        articles = news_service.scrape_and_save()
        mysql_connected = getattr(news_service.mysql_manager, 'use_mysql', False)
        logger.info(f"Scraped {len(articles)} articles. MySQL connected: {mysql_connected}")
        return jsonify({
            'status': 'success',
            'message': 'Scraping completed',
            'scraped_count': len(articles),
            'mysql_connected': mysql_connected
        })
    except Exception as e:
        logger.error(f"Error in manual_scrape: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get application status"""
    try:
        status = news_service.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'mysql_connected': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/debug')
def debug_status():
    """Debugging endpoint to check MySQL status, article count, and last scrape info"""
    try:
        mysql_connected = getattr(news_service.mysql_manager, 'use_mysql', False)
        # Get article count
        try:
            if mysql_connected:
                news_service.mysql_manager.cursor.execute('SELECT COUNT(*) as total FROM articles')
                row = news_service.mysql_manager.cursor.fetchone()
                article_count = row['total'] if row else 0
            else:
                article_count = 0
        except Exception as e:
            article_count = f'Error: {e}'
        # Last scrape info (if available)
        last_scrape = getattr(news_service, 'last_scrape', None)
        last_scrape_count = getattr(news_service, 'last_scrape_count', None)
        return jsonify({
            'mysql_connected': mysql_connected,
            'article_count': article_count,
            'last_scrape': last_scrape,
            'last_scrape_count': last_scrape_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initial scrape
    scrape_and_update()

    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting server on port {port}")

    try:
        app.run(debug=True, host='0.0.0.0', port=port)
    finally:
        # Ensure MySQL connection is closed when app shuts down
        news_service.mysql_manager.close_connection()
