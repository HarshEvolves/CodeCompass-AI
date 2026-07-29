from fastapi import status

def test_health_check(client):
    """
    Test GET /health endpoint using the client fixture.
    It expects a 200 OK status code and a JSON response body: {"status": "healthy"}.
    """
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}
