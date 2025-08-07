import logging
import threading
from opensearchpy import OpenSearch
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenSearchClient:
    _thread_local = threading.local()

    def __init__(self, index):
        self.index = index
        self.query_match_cutoff_score = float(settings.QUERY_MATCH_CUTOFF_SCORE)

    def _get_client(self):
        if not hasattr(self._thread_local, "client"):
            logger.info("Initializing OpenSearchClient for thread %s", threading.get_ident())
            self._thread_local.client = OpenSearch(hosts=[{'host': settings.OPENSEARCH_HOST, 'port': settings.OPENSEARCH_PORT}],
                                                 http_compress=True,
                                                 http_auth=(settings.OPENSEARCH_USER, settings.OPENSEARCH_PASSWORD) if settings.OPENSEARCH_USER else None,
                                                 use_ssl=False,
                                                 verify_certs=False,
                                                 ssl_show_warn=False)
        return self._thread_local.client

    def get_max_id(self):
        logger.debug("Querying Opensearch for max id")
        response = self._get_client().search(index=self.index, body={
            "size": 1,
            "_source": "id",
            "sort": [{"id": "desc"}]
        })
        logger.debug(f"Response from Opensearch for max id: {response}")
        if response['hits']['hits']:
            max_id = response['hits']['hits'][0]['_source']['id']
            return int(max_id)
        else:
            return 0

    def index_doc(self, doc):
        doc_id = self.get_max_id() + 1
        doc['id'] = doc_id
        response = self._get_client().index(index=self.index, id=doc['id'], body=doc, refresh=True)
        return int(response['_id'])
    
    def check_and_create_opensearch_index(self, index_body):
        if not self._get_client().indices.exists(index=self.index):
            self.create_index(index_body)
        else:
            logger.info(f"index '{self.index}' already exists.")

    def create_index(self, index_body):
        self._get_client().indices.create(index=self.index, body=index_body)

    def search(self, query):
        return self._get_client().search(index=self.index, body=query)  
