"""
Security Module Tests
Tests for token encryption, API key validation, and security headers
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from security import TokenManager, add_security_headers, RateLimiter, validate_api_key, require_api_key
from flask import Flask, request

class TestTokenManager:
    """Test TokenManager class for secure token handling"""
    
    def setup_method(self):
        """Set up test environment"""
        # Use test environment variables
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['TOKEN_ENCRYPTION_PASSWORD'] = 'test-password-1234567890'
        os.environ['TOKEN_ENCRYPTION_SALT'] = 'test-salt-1234567890'
        self.token_manager = TokenManager()
    
    def teardown_method(self):
        """Clean up environment"""
        if 'FLASK_ENV' in os.environ:
            del os.environ['FLASK_ENV']
        if 'TOKEN_ENCRYPTION_PASSWORD' in os.environ:
            del os.environ['TOKEN_ENCRYPTION_PASSWORD']
        if 'TOKEN_ENCRYPTION_SALT' in os.environ:
            del os.environ['TOKEN_ENCRYPTION_SALT']
    
    def test_token_encryption_decryption(self):
        """Test that tokens can be encrypted and decrypted correctly"""
        test_token = "test_sportmonks_token_1234567890"
        
        # Encrypt token
        encrypted = self.token_manager.encrypt_token(test_token)
        assert encrypted != test_token
        assert isinstance(encrypted, str)
        
        # Decrypt token
        decrypted = self.token_manager.decrypt_token(encrypted)
        assert decrypted == test_token
    
    def test_different_tokens_produce_different_encryptions(self):
        """Test that different tokens produce different encrypted values"""
        token1 = "token_1234567890"
        token2 = "token_0987654321"
        
        encrypted1 = self.token_manager.encrypt_token(token1)
        encrypted2 = self.token_manager.encrypt_token(token2)
        
        assert encrypted1 != encrypted2
    
    def test_mask_token(self):
        """Test token masking for logs"""
        # Test normal token
        token = "abcdefghijklmnopqrstuvwxyz"
        masked = self.token_manager.mask_token(token)
        assert masked == "abcd...wxyz"
        
        # Test short token
        short_token = "short"
        masked_short = self.token_manager.mask_token(short_token)
        assert masked_short == "*****"
    
    def test_validate_token_format(self):
        """Test token format validation"""
        # Valid tokens
        assert self.token_manager.validate_token_format("a" * 60) == True
        assert self.token_manager.validate_token_format("ABC123" * 10) == True
        
        # Invalid tokens
        assert self.token_manager.validate_token_format("") == False
        assert self.token_manager.validate_token_format("short") == False
        assert self.token_manager.validate_token_format("a" * 101) == False
        assert self.token_manager.validate_token_format("has spaces") == False
        assert self.token_manager.validate_token_format("has-dashes") == False
    
    def test_generate_api_key(self):
        """Test API key generation"""
        key1 = self.token_manager.generate_api_key()
        key2 = self.token_manager.generate_api_key()
        
        assert isinstance(key1, str)
        assert len(key1) > 20
        assert key1 != key2  # Keys should be unique
    
    def test_production_requires_encryption_settings(self):
        """Test that production environment requires encryption settings"""
        os.environ['FLASK_ENV'] = 'production'
        del os.environ['TOKEN_ENCRYPTION_PASSWORD']
        del os.environ['TOKEN_ENCRYPTION_SALT']
        
        with pytest.raises(ValueError, match="TOKEN_ENCRYPTION_PASSWORD and TOKEN_ENCRYPTION_SALT must be set in production!"):
            TokenManager()


class TestSecurityHeaders:
    """Test security headers middleware"""
    
    def test_add_security_headers(self):
        """Test that security headers are added correctly"""
        app = Flask(__name__)
        
        with app.test_request_context():
            response = MagicMock()
            response.headers = {}
            
            # Test in development
            os.environ['FLASK_ENV'] = 'development'
            result = add_security_headers(response)
            
            assert result.headers['X-Content-Type-Options'] == 'nosniff'
            assert result.headers['X-Frame-Options'] == 'DENY'
            assert result.headers['X-XSS-Protection'] == '1; mode=block'
            assert 'Content-Security-Policy' in result.headers
            assert 'Strict-Transport-Security' not in result.headers
            
            # Test in production
            os.environ['FLASK_ENV'] = 'production'
            response.headers = {}
            result = add_security_headers(response)
            
            assert 'Strict-Transport-Security' in result.headers
            assert result.headers['Strict-Transport-Security'] == 'max-age=31536000; includeSubDomains'


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def setup_method(self):
        """Set up rate limiter"""
        self.rate_limiter = RateLimiter()
    
    def test_rate_limit_allows_requests_under_limit(self):
        """Test that requests under the limit are allowed"""
        identifier = "test_ip_1"
        
        # Make 5 requests (under default limit of 60)
        for i in range(5):
            assert self.rate_limiter.is_allowed(identifier, max_requests=10, window=60) == True
    
    def test_rate_limit_blocks_requests_over_limit(self):
        """Test that requests over the limit are blocked"""
        identifier = "test_ip_2"
        
        # Make 10 requests (at the limit)
        for i in range(10):
            assert self.rate_limiter.is_allowed(identifier, max_requests=10, window=60) == True
        
        # 11th request should be blocked
        assert self.rate_limiter.is_allowed(identifier, max_requests=10, window=60) == False
    
    def test_rate_limit_window_reset(self):
        """Test that rate limit resets after window expires"""
        identifier = "test_ip_3"
        
        # Make requests at the limit
        for i in range(5):
            assert self.rate_limiter.is_allowed(identifier, max_requests=5, window=1) == True
        
        # Should be blocked
        assert self.rate_limiter.is_allowed(identifier, max_requests=5, window=1) == False
        
        # Wait for window to expire
        import time
        time.sleep(1.1)
        
        # Should be allowed again
        assert self.rate_limiter.is_allowed(identifier, max_requests=5, window=1) == True


class TestAPIKeyValidation:
    """Test API key validation"""
    
    def test_validate_api_key(self):
        """Test API key validation against environment variables"""
        # Set up test API keys
        os.environ['INTERNAL_API_KEYS'] = 'key1,key2,key3'
        
        assert validate_api_key('key1') == True
        assert validate_api_key('key2') == True
        assert validate_api_key('key3') == True
        assert validate_api_key('invalid_key') == False
        assert validate_api_key('') == False
        
        # Clean up
        del os.environ['INTERNAL_API_KEYS']
    
    def test_require_api_key_decorator(self):
        """Test the require_api_key decorator"""
        app = Flask(__name__)
        
        @require_api_key
        def protected_endpoint():
            return "Success"
        
        with app.test_request_context():
            # Test without API key
            with patch('security.request') as mock_request:
                mock_request.headers = {}
                response, status_code = protected_endpoint()
                assert status_code == 401
                assert response.json['error'] == 'API key required'
            
            # Test with invalid API key
            with patch('security.request') as mock_request:
                mock_request.headers = {'X-API-Key': 'invalid_key'}
                with patch('security.validate_api_key', return_value=False):
                    response, status_code = protected_endpoint()
                    assert status_code == 403
                    assert response.json['error'] == 'Invalid API key'
            
            # Test with valid API key
            with patch('security.request') as mock_request:
                mock_request.headers = {'X-API-Key': 'valid_key'}
                with patch('security.validate_api_key', return_value=True):
                    result = protected_endpoint()
                    assert result == "Success"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])