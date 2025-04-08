import json
import os
from flask import Flask, send_file, current_app
from jinja2 import Template
import io
import asyncio
import requests
from playwright.async_api import async_playwright

app = Flask(__name__)

ENTITY_ID = os.environ.get("SENSOR_NAME")
PORT = 5000
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")

print("SUPERVISOR_TOKEN:", SUPERVISOR_TOKEN)
print("ENTITY_ID:", ENTITY_ID)
print("PORT:", PORT)

def get_dashboard_message():
    try:
        headers = {
            "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
            "Content-Type": "application/json"
        }
        current_app.logger.info(f"Sent headers: {headers}")
        response = requests.get(
            f"http://supervisor/core/api/states/{ENTITY_ID}",
            headers=headers,
            timeout=5
        )
        current_app.logger.info(f"Response headers: {response.headers}")
        response.raise_for_status()
        current_app.logger.info(f"Response json: {json.dumps(response.json(), indent=4)}")
        return response.json()["state"]
    except Exception as e:
        current_app.logger.error(f"[ERROR] Failed to fetch from Home Assistant: {e}")
        return "Unavailable"

@app.route("/image")
def render_image():
    return asyncio.run(render_dashboard())

async def render_dashboard():
    message = get_dashboard_message()

    with open("dashboard.html") as f:
        template = Template(f.read())
    html = template.render(message=message)

    path = "/tmp/output.png"

    async with async_playwright() as p:
        browser = await p.firefox.launch()
        page = await browser.new_page(viewport={"width": 1072, "height": 1448})
        await page.set_content(html)
        await page.screenshot(path=path)
        await browser.close()

    return send_file(path, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
