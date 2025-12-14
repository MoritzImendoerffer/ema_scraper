from config_loader import load_config
from urllib.parse import urlparse
import regex as re

config = load_config("config.yml")

url = "https://www.bmwet.gv.at/dam/jcr:b280cf0d-72b7-4b96-9886-534d0f17f5bf/IPPC_Antworten%20auf%20gestellte%20Fragen.pdfhttps://www.bmwet.gv.at/dam/jcr:b280cf0d-72b7-4b96-9886-534d0f17f5bf/IPPC_Antworten%20auf%20gestellte%20Fragen.pdf"

url = urlparse(url)

