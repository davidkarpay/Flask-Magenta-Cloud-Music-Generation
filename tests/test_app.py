import json

def test_list_models(client):
    rv = client.get('/models')
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)


def test_generate_missing_fields(client):
    # Missing required fields should yield a 400 error
    rv = client.post('/generate', json={})
    assert rv.status_code == 400


def test_generate_success(monkeypatch, client):
    # Mock model_loader and generator to isolate endpoint logic
    monkeypatch.setattr('model_loader.load_model', lambda m: 'model')
    monkeypatch.setattr('generator.generate', lambda model, data, t, p: {'notes': []})

    payload = {
        'model': 'test_model',
        'input_data': '{}',
        'input_type': 'notes_json',
        'params': {}
    }
    rv = client.post('/generate', json=payload)
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'job_id' in data
    assert data['format'] == 'MIDI'
