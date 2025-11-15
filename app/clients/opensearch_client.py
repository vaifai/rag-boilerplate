from opensearchpy import OpenSearch
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
port = 9200
host = 'localhost'

def create_opensearch_client() -> OpenSearch:
    """
        Create a single OpenSearch client instance (no auth).
        This should be called only once during app startup.
        """
    client = OpenSearch(
        hosts=[{'host': host, 'port': port}],
        timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )

    try:
        if client.ping():
            logger.info(f"Connected to OpenSearch at {settings.OPENSEARCH_HOST}")
        else:
            logger.warning(f"Ping to OpenSearch failed at {settings.OPENSEARCH_HOST}")
    except Exception as e:
        logger.exception("OpenSearch ping failed: %s", e)

    return client