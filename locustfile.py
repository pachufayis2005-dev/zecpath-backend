from locust import HttpUser, task, between


class JobPortalUser(HttpUser):

    wait_time = between(1, 3)

    def on_start(self):
        response = self.client.post(
            "/api/login/",
            json={
                "username": "employer2",
                "password": "test123",
            },
            name="Login",
        )

        if response.status_code == 200:
            token = response.json().get("access")

            if token:
                self.client.headers.update({
                    "Authorization": f"Bearer {token}"
                })
            else:
                print("Login succeeded but no access token was returned.")

        else:
            print(
                f"Login failed: {response.status_code} "
                f"{response.text}"
            )

    @task(3)
    def view_jobs(self):
        self.client.get(
            "/api/jobs/",
            name="GET /api/jobs/"
        )

    @task(2)
    def latest_jobs(self):
        self.client.get(
            "/api/jobs/latest/",
            name="GET /api/jobs/latest/"
        )

    @task(1)
    def featured_jobs(self):
        self.client.get(
            "/api/jobs/featured/",
            name="GET /api/jobs/featured/"
        )