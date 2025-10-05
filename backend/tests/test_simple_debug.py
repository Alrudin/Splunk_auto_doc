"""Simple debug test for fixtures."""


def test_simple_debug():
    """Simple test to see if fixtures work."""
    print("Simple test running")
    assert True


def test_debug_with_test_db(test_db):
    """Test with test_db fixture."""
    print(f"test_db fixture: {test_db}")
    session = test_db()
    print(f"session: {session}")
    session.close()
    assert True


def test_debug_with_client(client):
    """Test with client fixture."""
    print(f"client fixture: {client}")
    response = client.get("/health")
    print(f"health response: {response.status_code}")

    # Test the actual runs endpoint
    response = client.get("/v1/runs")
    print(f"runs response: {response.status_code}")
    if response.status_code == 200:
        print(f"runs data: {response.json()}")
    else:
        print(f"runs error: {response.text}")

    assert True
