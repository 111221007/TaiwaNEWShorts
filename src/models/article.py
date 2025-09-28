# Article DB model and data access

from datetime import datetime

class Article:
    def __init__(self, title, summary, content, url, image_url, category, source, scraped_at=None, published_at=None):
        self.title = title
        self.summary = summary
        self.content = content
        self.url = url
        self.image_url = image_url
        self.category = category
        self.source = source
        self.scraped_at = scraped_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.published_at = published_at

    def to_dict(self):
        return {
            'title': self.title,
            'summary': self.summary,
            'content': self.content,
            'url': self.url,
            'image_url': self.image_url,
            'category': self.category,
            'source': self.source,
            'scraped_at': self.scraped_at,
            'published_at': self.published_at
        }

