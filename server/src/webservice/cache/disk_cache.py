from diskcache import Cache
from shared.config import Config

disk_cache = Cache(directory=Config.DISK_CACHE_DIR, size_limit=Config.DISK_CACHE_SIZE_LIMIT)

