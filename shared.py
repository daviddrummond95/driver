from cachetools import TTLCache

# Create a cache to store generated emails
email_cache = TTLCache(maxsize=100, ttl=3600)  # Cache for 1 hour