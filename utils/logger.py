import logging
import sys
import json
import os
from datetime import datetime
from typing import Any, Dict
import structlog
from pythonjsonlogger import jsonlogger

# Color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'

class BeautifulFormatter(logging.Formatter):
    """Beautiful colored formatter for console output"""
    
    COLORS = {
        'DEBUG': Colors.DIM + Colors.WHITE,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.BOLD + Colors.RED + Colors.BG_YELLOW,
    }
    
    def format(self, record):
        # Get the base format
        log_message = super().format(record)
        
        # Add colors based on level
        color = self.COLORS.get(record.levelname, Colors.WHITE)
        
        # Format the message with colors and emojis
        level_emoji = {
            'DEBUG': '🔍',
            'INFO': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }.get(record.levelname, '📝')
        
        # Create beautiful formatted message
        timestamp = datetime.now().strftime("%H:%M:%S")
        logger_name = record.name.split('.')[-1] if '.' in record.name else record.name
        
        formatted_message = (
            f"{Colors.DIM}[{timestamp}]{Colors.RESET} "
            f"{color}{level_emoji} {record.levelname:<8}{Colors.RESET} "
            f"{Colors.CYAN}{logger_name:<20}{Colors.RESET} "
            f"{log_message}"
        )
        
        return formatted_message

class StructuredFormatter(logging.Formatter):
    """Structured formatter for JSON output"""
    
    def format(self, record):
        # Extract structured data from the record
        if hasattr(record, 'structured_data'):
            data = record.structured_data
        else:
            data = {}
        
        # Add basic fields
        data.update({
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        })
        
        # Add exception info if present
        if record.exc_info:
            data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(data, indent=2, ensure_ascii=False)

def setup_logging(log_level: str = "INFO") -> None:
    """Setup beautiful structured logging configuration"""
    
    # Determine output format based on environment
    is_development = os.getenv('ENVIRONMENT', 'development').lower() == 'development'
    use_colors = os.getenv('LOG_COLORS', 'true').lower() == 'true'
    
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add appropriate renderer based on environment
    if is_development and use_colors:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Console handler with beautiful formatting
    console_handler = logging.StreamHandler(sys.stdout)
    
    if is_development and use_colors:
        console_handler.setFormatter(BeautifulFormatter())
    else:
        console_handler.setFormatter(StructuredFormatter())
    
    # Set level
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    
    # Add a separator for better readability
    if is_development:
        print(f"\n{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}🚀 Resume CV Letter Service - Logging Started{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*80}{Colors.RESET}\n")

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)

class RequestLogger:
    """Beautiful context manager for request logging"""
    
    def __init__(self, logger: structlog.BoundLogger, request_id: str, endpoint: str):
        self.logger = logger
        self.request_id = request_id
        self.endpoint = endpoint
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        
        # Beautiful request start logging
        self.logger.info(
            "🚀 Request Started",
            request_id=self.request_id,
            endpoint=self.endpoint,
            timestamp=self.start_time.isoformat(),
            status="STARTED"
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type:
            # Beautiful error logging
            self.logger.error(
                "💥 Request Failed",
                request_id=self.request_id,
                endpoint=self.endpoint,
                duration=f"{duration:.3f}s",
                error_type=exc_type.__name__,
                error_message=str(exc_val),
                status="FAILED",
                exc_info=exc_tb
            )
        else:
            # Beautiful success logging
            status_emoji = "✅" if duration < 1.0 else "⚠️" if duration < 3.0 else "🐌"
            self.logger.info(
                f"{status_emoji} Request Completed",
                request_id=self.request_id,
                endpoint=self.endpoint,
                duration=f"{duration:.3f}s",
                status="COMPLETED",
                performance="FAST" if duration < 1.0 else "NORMAL" if duration < 3.0 else "SLOW"
            )

class PerformanceLogger:
    """Beautiful performance logging utility"""
    
    @staticmethod
    def log_api_call(logger: structlog.BoundLogger, service_name: str, operation: str, duration: float, success: bool = True, **kwargs):
        """Log API calls with beautiful formatting"""
        emoji = "✅" if success else "❌"
        status = "SUCCESS" if success else "FAILED"
        
        logger.info(
            f"{emoji} {service_name} API Call",
            service=service_name,
            operation=operation,
            duration=f"{duration:.3f}s",
            status=status,
            **kwargs
        )
    
    @staticmethod
    def log_database_operation(logger: structlog.BoundLogger, operation: str, duration: float, success: bool = True, **kwargs):
        """Log database operations with beautiful formatting"""
        emoji = "💾" if success else "💥"
        status = "SUCCESS" if success else "FAILED"
        
        logger.info(
            f"{emoji} Database Operation",
            operation=operation,
            duration=f"{duration:.3f}s",
            status=status,
            **kwargs
        )
