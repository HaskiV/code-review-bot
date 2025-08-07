def test_get_models(client):
    """Test the /api/models endpoint."""
    response = client.get('/api/models')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True
    assert 'models' in json_data
    assert isinstance(json_data['models'], list)
    assert 'default_model' in json_data
