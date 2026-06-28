import sys
import logging
logging.basicConfig(level=logging.INFO)
from api.workers.tasks.request_types_importer import import_request_types_from_response_network
print(import_request_types_from_response_network())
