from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import json
from datetime import datetime
import pytz

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER")
GRAPH_URL = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"

RECIPIENTS = [
    "919360605902",
    "919710908050"
]

class EnquiryForm(BaseModel):
    name: str
    phone: str
    area: str = "Not specified"
    service: str
    message: str = "No message"

@app.get("/")
def root():
    return {
        "status": "Meta WhatsApp Backend Running",
        "token_loaded": bool(ACCESS_TOKEN),
        "phone_loaded": bool(PHONE_NUMBER_ID)
    }

@app.post("/send-enquiry")
def send_enquiry(form: EnquiryForm):
    if not ACCESS_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="WHATSAPP_TOKEN missing"
        )

    ist = pytz.timezone("Asia/Kolkata")
    time_now = datetime.now(ist).strftime("%d %b %Y, %I:%M %p")

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    results = []
    for recipient in RECIPIENTS:
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": "enquiry_notification",
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "parameter_name": "name", "text": form.name or "N/A"},
                            {"type": "text", "parameter_name": "phone", "text": form.phone or "N/A"},
                            {"type": "text", "parameter_name": "service", "text": form.service or "N/A"},
                            {"type": "text", "parameter_name": "area", "text": form.area or "Not specified"},
                            {"type": "text", "parameter_name": "message", "text": form.message or "No message"},
                            {"type": "text", "parameter_name": "time", "text": time_now}
                        ]
                    }
                ]
            }
        }

        response = requests.post(
            GRAPH_URL,
            data=json.dumps(payload),
            headers=headers
        )
        print(f"Meta Response: {response.status_code} - {response.text}")
        results.append({
            "recipient": recipient,
            "status": response.status_code,
            "response": response.json() if response.text else {}
        })

    return {
        "success": True,
        "results": results
    }