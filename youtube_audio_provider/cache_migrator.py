import logging
from urllib.parse import unquote

from youtube_audio_provider.cache import Cache
from youtube_audio_provider.cache_db import Cache as CacheDB
from youtube_audio_provider.downloader import Downloader

logger = logging.getLogger(__name__)

class CacheToCacheDBMigrator:
    def __init__(self, cache: Cache, cache_db: CacheDB, downloader: Downloader):
        self.cache = cache
        self.cache_db = cache_db
        self.downloader = downloader

    def migrate(self):
        items = self.cache.all_items()  # should get nothing if cache is empty
        if len(items) == 0:
            logger.info("No items to migrate from Cache to CacheDB.")
            return
        
        if len(items) == 1 and items[0].phrase == 'dummy':
            logger.info("No items to migrate from Cache to CacheDB.")
            return
        
        for item in items:
            unquoted_phrase = unquote(item.phrase)

            logger.debug(f"Migrating phrase: {item.phrase} with filename: {item.filename}")
            with self.downloader.create_download_context(unquoted_phrase) as dl_ctx:
                id = dl_ctx.get_id()
                result = self.cache_db.retrieve_by_id(id)

                if (result is not None):
                    logger.debug(f"Youtube id: {id}, already added, adding phrase: {item.phrase}")
                    self.cache_db.add_searchphrase_to_id(id, item.phrase)
                else:
                    result = dl_ctx.get_info()
                    result['filename'] = item.filename
                    logger.debug(f"Youtube id: {id} for phrase: {item.phrase}, and filename {item.filename} adding to CacheDB.")
                    self.cache_db.put_to_cache(item.phrase, **result)
            logger.debug(f"Marking phrase: {item.phrase} as migrated.")
            #self.cache.retrieve_from_cache(item.phrase)  # mark as migrated
        logger.info("Migration completed.")
