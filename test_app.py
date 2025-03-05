import pytest
import json
import hmac
import hashlib
from app import app
from unittest.mock import patch, MagicMock

# tests/test_app.py

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_zalo_api():
    with patch('app.zalo_api') as mock:
        yield mock

def test_webhook_get(client):
    """Test GET request to webhook endpoint"""
    response = client.get('/webhook')
    assert response.status_code == 200
    assert b"Webhook is active!" in response.data

def test_webhook_post_invalid_signature(client, mock_zalo_api):
    """Test POST request with invalid signature"""
    mock_zalo_api.verify_webhook.return_value = False
    
    data = {
        "event_name": "user_send_text",
        "sender": {"id": "test_user"},
        "message": {"text": "Hello"}
    }
    
    headers = {
        'X-ZaloOA-Signature': 'invalid_signature'
    }
    
    response = client.post('/webhook', 
                         json=data,
                         headers=headers)
    
    assert response.status_code == 401
    assert response.json['error'] == "Invalid signature"

def test_webhook_user_send_text(client, mock_zalo_api):
    """Test handling user_send_text event"""
    mock_zalo_api.verify_webhook.return_value = True
    mock_zalo_api.send_text_message.return_value = {"success": True}
    
    data = {
        "event_name": "user_send_text",
        "sender": {"id": "test_user"},
        "message": {"text": "Hello"}
    }
    
    # Create valid signature
    mock_secret = "test_secret"
    data_str = json.dumps(data)
    hmac_obj = hmac.new(mock_secret.encode(), 
                        data_str.encode(), 
                        hashlib.sha256)
    valid_signature = hmac_obj.hexdigest()
    
    headers = {
        'X-ZaloOA-Signature': valid_signature
    }
    
    response = client.post('/webhook',
                         json=data, 
                         headers=headers)
    
    assert response.status_code == 200
    assert response.json['status'] == "success"
    mock_zalo_api.send_text_message.assert_called_once()

def test_webhook_user_follow(client, mock_zalo_api):
    """Test handling user_follow event"""
    mock_zalo_api.verify_webhook.return_value = True
    
    data = {
        "event_name": "user_follow",
        "follower": {"id": "test_user"}
    }
    
    response = client.post('/webhook', json=data)
    
    assert response.status_code == 200
    assert response.json['status'] == "success"
    
    # Verify welcome message was sent
    mock_zalo_api.send_text_message.assert_called_once()
    called_args = mock_zalo_api.send_text_message.call_args[0]
    assert "Xin chào!" in called_args[1]

def test_webhook_user_send_image(client, mock_zalo_api):
    """Test handling user_send_image event"""
    mock_zalo_api.verify_webhook.return_value = True
    
    data = {
        "event_name": "user_send_image",
        "sender": {"id": "test_user"}
    }
    
    response = client.post('/webhook', json=data)
    
    assert response.status_code == 200
    assert response.json['status'] == "success"
    
    # Verify proper response message
    mock_zalo_api.send_text_message.assert_called_once()
    called_args = mock_zalo_api.send_text_message.call_args[0]
    assert "chỉ có thể xử lý tin nhắn văn bản" in called_args[1]

def test_webhook_unhandled_event(client, mock_zalo_api):
    """Test handling of unrecognized event"""
    mock_zalo_api.verify_webhook.return_value = True
    
    data = {
        "event_name": "unknown_event",
        "sender": {"id": "test_user"}
    }
    
    response = client.post('/webhook',
                         json=data)
    
    assert response.status_code == 200 
    assert response.json['status'] == "unhandled_event"