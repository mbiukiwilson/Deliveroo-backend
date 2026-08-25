from run import create_app

def test_get_parcel_unauthorized():
    app = create_app()
    client = app.test_client()

    response = client.get('/parcels/1')

    assert response.status_code == 401

def test_update_destination_unauthorized():
    app = create_app()
    client = app.test_client()

    response = client.patch('/parcels/1/destination', json={"destination": "New Location"})

    assert response.status_code == 401

def test_cancel_parcel_unauthorized():
    app = create_app()
    client = app.test_client()

    response = client.patch('/parcels/1/cancel')

    assert response.status_code == 401