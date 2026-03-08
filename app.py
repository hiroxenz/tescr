import os
import uuid
import time
from flask import Flask, request, jsonify
from cloudflyer import Cloudflyer

app = Flask(__name__)

CLIENT_KEY = os.getenv("CLIENT_KEY", "hiroxen")

solver = Cloudflyer(
    client_key=CLIENT_KEY,
    max_tasks=5
)

tasks = {}


@app.route("/")
def home():
    return jsonify({
        "service": "cloudflyer api",
        "status": "running"
    })


@app.route("/createTask", methods=["POST"])
def create_task():

    data = request.json
    key = data.get("clientKey")

    if key != CLIENT_KEY:
        return jsonify({"error": "invalid clientKey"})

    task_type = data.get("type")
    url = data.get("url")
    sitekey = data.get("sitekey")
    userAgent = data.get("userAgent")
    proxy = data.get("proxy")

    task_id = str(uuid.uuid4())

    tasks[task_id] = {
        "status": "processing",
        "result": None
    }

    try:

        if task_type == "CloudflareChallenge":
            result = solver.solve_cloudflare(
                url=url,
                user_agent=userAgent,
                proxy=proxy
            )

        elif task_type == "Turnstile":
            result = solver.solve_turnstile(
                url=url,
                sitekey=sitekey,
                user_agent=userAgent,
                proxy=proxy
            )

        elif task_type == "RecaptchaInvisible":
            result = solver.solve_recaptcha(
                url=url,
                sitekey=sitekey,
                user_agent=userAgent,
                proxy=proxy
            )

        else:
            return jsonify({"error": "unsupported task type"})

        tasks[task_id]["status"] = "ready"
        tasks[task_id]["result"] = result

    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["result"] = str(e)

    return jsonify({
        "errorId": 0,
        "taskId": task_id
    })


@app.route("/getTaskResult", methods=["POST"])
def get_task():

    data = request.json
    task_id = data.get("taskId")

    task = tasks.get(task_id)

    if not task:
        return jsonify({
            "errorId": 1,
            "error": "task not found"
        })

    return jsonify({
        "errorId": 0,
        "status": task["status"],
        "solution": task["result"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
