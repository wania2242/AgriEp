"""
Configuration utilities for web automation.

This module provides centralized configuration management for:
- Environment variable handling
- Default configurations
- Configuration validation
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class ConfigUtils:
    """Configuration management utilities."""
    
    @staticmethod
    def load_env_config() -> Dict[str, Any]:
        """Load configuration from environment variables."""
        load_dotenv()
        
        config = {
            'login_url': os.getenv("FARM_APP_LOGIN_URL"),
            'email': os.getenv("FARM_APP_EMAIL"),
            'password': os.getenv("FARM_APP_PASSWORD"),
            'totp_secret': os.getenv("FARM_APP_TOTP_SECRET"),
            'target_url': os.getenv("FARM_APP_LOGIN_URL")
        }
        
        # Validate required fields
        missing_fields = [key for key, value in config.items() 
                         if key != 'totp_secret' and not value]
        
        if missing_fields:
            logger.warning(f"Missing required environment variables: {missing_fields}")
        
        return config
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """Validate configuration completeness."""
        required_fields = ['login_url', 'email', 'password']
        missing_fields = [field for field in required_fields if not config.get(field)]
        
        if missing_fields:
            logger.error(f"Missing required configuration: {missing_fields}")
            return False
        
        return True
    
    @staticmethod
    def get_retry_config() -> Dict[str, Any]:
        """Get retry mechanism configuration."""
        return {
            'max_retries': int(os.getenv("RETRY_MAX_ATTEMPTS", "3")),
            'base_delay': float(os.getenv("RETRY_BASE_DELAY", "2.0")),
            'max_delay': float(os.getenv("RETRY_MAX_DELAY", "15.0"))
        }
    
    @staticmethod
    def get_timeout_config() -> Dict[str, Any]:
        """Get timeout configuration."""
        return {
            'page_load_timeout': int(os.getenv("PAGE_LOAD_TIMEOUT", "30")),
            'element_timeout': int(os.getenv("ELEMENT_TIMEOUT", "10")),
            'navigation_timeout': int(os.getenv("NAVIGATION_TIMEOUT", "10"))
        }
    
    @staticmethod
    def get_workorder_config() -> Dict[str, Any]:
        """Get workorder-specific configuration."""
        return {
            'workorders_url': os.getenv("WORKORDERS_URL", "https://agrierp-eh-pon-farms-qa-dfedaqg0hegranhf.eastus-01.azurewebsites.net/workorders"),
            'api_url': os.getenv("WORKORDER_API_URL", "https://agrierp-eh-pon-farms-api-qa-ebdzb4csbsa7hccp.eastus-01.azurewebsites.net/api/workOrder"),
            'farm_option_xpath': os.getenv("FARM_OPTION_XPATH", "//*[@id='myDropdown']/a[6]"),
            'operation_option_xpath': os.getenv("OPERATION_OPTION_XPATH", "//a[contains(@class, 'dropdown-item') and normalize-space()='Early Spray Corn VR (9025100)']"),
            'supervisor_option_xpath': os.getenv("SUPERVISOR_OPTION_XPATH", "//a[contains(@class, 'dropdown-item') and normalize-space()='Farm Fuel (CPF-FF-17-001)']")
        } 