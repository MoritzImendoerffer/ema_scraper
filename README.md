# ema_scraper
A scraper for ema.europa.eu, hobby project

# Basic functionality

The scraper does scrape the web page into a mongoDB database with the aim to provide a dataset for developing of a graph RAG retrieval pipeline.

# Roadmap


## Envised project structure

- **ema-rag/**
  - `config.yaml` - All configuration (patterns, paths, etc.)
  - `config_loader.py` - YAML config loading
  - `run_crawl.py` - Entry point for crawling
  - `explore_graph.py` - Explore graph after crawling
  - `requirements.txt`
  - **scraper/**
    - `spider.py` - Thin orchestrator
    - `classifiers.py` - URL classification (Strategy pattern)
    - `extractors.py` - Content extraction (Strategy pattern)
    - `items.py` - Data containers
    - `pipelines.py` - Spider output → Graph
    - `settings.py` - Scrapy settings
- **storage/**
    - `pymongodb.py` - Connector to MongoDB(Repository pattern)
- **parsers/** - PDF parsing (Strategy + Factory)
    - `base.py`
    - `__init__.py` - Factory: get_parser()
    - `pymupdf_parser.py`
- **embeddings/** - Embedding models (Strategy + Factory)
    - `base.py`
    - `__init__.py`
    - `local_hf.py`
- **vectordb/** - Vector store (for later)



