import requests
from config import OCATELKOM_BEARER, OCATELKOM_ENDPOINT

def notifWhatsapp(phone_number: str, description: str, status: str):
    url = f'{OCATELKOM_ENDPOINT}'
    
    headers = {
        'Authorization': f'Bearer {OCATELKOM_BEARER}',
        'Content-Type': 'application/json'
    }

    payload = {
        "phone_number": phone_number,
        "message": {
            "type": "template",
            "template": {
                "template_code_id": "d7529850_b0a9_41fe_b49c_b7d78ed184de:informasi_status_update_website",
                "payload": [
                    {
                        "position": "body",
                        "parameters": [
                            {"type": "text", "text": description},
                            {"type": "text", "text": status}
                        ]
                    }
                ]
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("WA Response:", response.status_code, response.text) 
    return response.text



# if __name__ == "__main__":
#     print("=== WhatsApp Monitoring Notifier ===")
#     phone = input("Enter phone number (e.g. 6281234567890): ").strip()
#     desc = input("Enter description: ").strip()
#     status = input("Enter status: ").strip()

#     print("\nSending message...")
#     result = notifWhatsapp(phone, desc, status)
#     print("Response:\n", result)