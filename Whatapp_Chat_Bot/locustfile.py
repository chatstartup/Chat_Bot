from locust import HttpUser, task, between

class ChatbotUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def chat_request(self):
        self.client.post("/chat", 
            json={"message": "Explain quantum computing"},
            headers={"Content-Type": "application/json"}
        )
