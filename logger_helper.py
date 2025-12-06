import logging
import sys
from pathlib import Path
from typing import Optional

class LoggerHelper:
    """
    A reusable logging helper that logs to both stdout and a file.
    
    Usage:
        logger = LoggerHelper(name="my_app", log_file="app.log").get_logger()
        logger.info("This goes to both console and file")
    """
    
    def __init__(
        self,
        name: str = "app",
        log_file: str = "app.log",
        level: int = logging.INFO,
        log_format: Optional[str] = None,
        date_format: Optional[str] = None
    ):
        """
        Initialize the logging helper.
        
        Args:
            name: Name of the logger
            log_file: Path to the log file
            level: Logging level (default: logging.INFO)
            log_format: Custom log format string (optional)
            date_format: Custom date format string (optional)
        """
        self.name = name
        self.log_file = log_file
        self.level = level
        
        # Default format if none provided
        if log_format is None:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        if date_format is None:
            date_format = "%Y-%m-%d %H:%M:%S"
        
        self.formatter = logging.Formatter(log_format, datefmt=date_format)
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with both stdout and file handlers."""
        # Get or create logger
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Console handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        logger.addHandler(console_handler)
        
        # File handler
        # Create parent directories if they don't exist
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger
    
    def get_logger(self) -> logging.Logger:
        """Return the configured logger instance."""
        return self.logger


def get_logger(
    name: str = "app",
    log_file: str = "app.log",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Convenience function to quickly get a configured logger.
    
    Args:
        name: Name of the logger
        log_file: Path to the log file
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    return LoggerHelper(name=name, log_file=log_file, level=level).get_logger()

if __name__ == "__main__":
    # Example 1: Quick setup with convenience function
    logger = get_logger(name="my_app", log_file="my_app.log")

    logger.info("Application started")
    logger.warning("This is a warning")
    logger.error("Something went wrong!")

    # Example 2: Using the class for more control
    custom_logger = LoggerHelper(
        name="data_processor",
        log_file="logs/data_processor.log",
        level=logging.DEBUG,
        log_format="%(levelname)-8s | %(asctime)s | %(message)s",
        date_format="%H:%M:%S"
    ).get_logger()

    custom_logger.debug("Processing started...")
    custom_logger.info("Processing 100 records")
    custom_logger.info("Processing complete!")

    # Example 3: Different logger instances for different modules
    db_logger = get_logger(name="database", log_file="logs/database.log")
    api_logger = get_logger(name="api", log_file="logs/api.log")

    db_logger.info("Database connection established")
    api_logger.info("API endpoint called: /users")