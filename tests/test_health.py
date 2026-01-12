def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_db_ping(client):
    r = client.get("/db-ping")
    assert r.status_code == 200
    body = r.json()
    assert body["db"] == "ok"
    assert body["value"] == 1
