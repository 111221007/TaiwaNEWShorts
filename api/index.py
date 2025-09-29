from src.api.app import app

# Vercel serverless function entry point
def handler(request):
    return app(request.environ, lambda *args: None)

# For local development
if __name__ == "__main__":
    app.run(debug=True)
