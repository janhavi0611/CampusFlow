def test_login_page_renders(client):
    res = client.get("/auth/login")
    assert res.status_code == 200
    assert b"Log in" in res.data or b"CampusFlow" in res.data


def test_login_success(client):
    res = client.post("/auth/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Welcome back" in res.data or b"Dashboard" in res.data


def test_login_failure(client):
    res = client.post("/auth/login", data={"username": "admin", "password": "wrongpassword"}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Invalid username or password" in res.data


def test_admin_route_protection(client):
    # Log in as organizer
    client.post("/auth/login", data={"username": "organizer", "password": "org123"})
    res = client.get("/resources/create", follow_redirects=True)
    assert res.status_code == 200
    assert b"requires administrator access" in res.data or b"Dashboard" in res.data
