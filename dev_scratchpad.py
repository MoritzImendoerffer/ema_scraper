from config_loader import load_config
from urllib.parse import urlparse
import regex as re

config = load_config("config.yml")

url = "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/quality-design"

parser_map = {
    "/en/medicines/human/EPAR": "parse_human_epar",
    "/en/human-regulatory-overview": "parse_with_sidebar",
}

match_dict = {}
for key in parser_map:
    upath = urlparse(url).path.strip("/").split("/")
    rpath = key.strip("/").split("/")
    n_match = 0
    for match_item in list(zip(upath, rpath)):
        if match_item[0] == match_item[1]:
            n_match += 1
    
    match_dict[key] = n_match


parser = max(match_dict, key=match_dict.get)