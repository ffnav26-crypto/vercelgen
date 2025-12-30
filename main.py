# telegram: @The_Earths / @UnknownGuy9876

import requests
import time
import json
import random
import re
import asyncio
import aiohttp
from urllib.parse import unquote
from fake_useragent import UserAgent
import os
import sys
from flask import Flask, jsonify, request

app = Flask(__name__)
ua = UserAgent()

class EmailGenerator:
    def __init__(self):
        self.url = "https://api.mail.tm"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        
    async def generate(self):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(f"{self.url}/domains") as resp:
                    if resp.status != 200: return None
                    data = await resp.json()
                    domain = data["hydra:member"][0]["domain"]

                address = ''.join(random.choice("qwertyuiopasdfghjklzxcvbnm") for _ in range(10)) + "@" + domain
                password = ''.join(random.choice("qwertyuiopasdfghjklzxcvbnm0123456789") for _ in range(12))
                
                payload = {"address": address, "password": password}
                async with session.post(f"{self.url}/accounts", json=payload) as resp:
                    if resp.status != 201: return None

                async with session.post(f"{self.url}/token", json=payload) as resp:
                    if resp.status != 200: return None
                    token_data = await resp.json()
                    return address, token_data.get("token")
            except:
                return None

    async def get_otp(self, token):
        async with aiohttp.ClientSession(headers={**self.headers, "Authorization": f"Bearer {token}"}) as session:
            for _ in range(20):
                await asyncio.sleep(5)
                try:
                    async with session.get(f"{self.url}/messages") as resp:
                        if resp.status != 200: continue
                        data = await resp.json()
                        messages = data.get("hydra:member", [])
                        if messages:
                            msg_id = messages[0]["id"]
                            async with session.get(f"{self.url}/messages/{msg_id}") as r:
                                if r.status == 200:
                                    msg = await r.json()
                                    text = msg.get("text", "")
                                    otp = re.search(r"\b\d{6}\b", text)
                                    if otp: return otp.group(0)
                except:
                    continue
            return None

async def create_instagram_account():
    email_gen = EmailGenerator()
    email_data = await email_gen.generate()
    if not email_data: return {"status": "error", "message": "Failed to create email"}
    email, email_token = email_data
    
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    password = "".join(random.choices(chars, k=12)) + str(random.randint(1, 9999))
    
    random_letters = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(8, 12)))
    random_numbers = ''.join(random.choices('0123456789', k=random.randint(5, 8)))
    username = f"insta.{random_letters}{random_numbers}"
    
    link = "https://www.instagram.com/"
    create_url = "https://www.instagram.com/accounts/web_create_ajax/attempt/"
    verify_mail = "https://i.instagram.com/api/v1/accounts/send_verify_email/"
    check_confo = "https://i.instagram.com/api/v1/accounts/check_confirmation_code/"
    final_create_url = "https://www.instagram.com/accounts/web_create_ajax/"
    
    headers = {
        "user-agent": ua.random,
        "x-requested-with": "XMLHttpRequest",
        "referer": "https://www.instagram.com/accounts/emailsignup/",
    }

    try:
        with requests.Session() as s:
            s.get(link)
            csrf = s.cookies.get("csrftoken", "")
            mid = s.cookies.get("mid", "")
            if not csrf: return {"status": "error", "message": "Failed to get CSRF token"}
            headers["x-csrftoken"] = csrf

            payload = {
                "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}",
                "email": email, "username": username, "first_name": "User",
                "opt_into_one_tap": "false", "client_id": mid, "seamless_login_enabled": "1",
            }
            s.post(create_url, data=payload, headers=headers)
            s.post(verify_mail, data={"device_id": mid, "email": email}, headers=headers)
            
            otp = await email_gen.get_otp(email_token)
            if not otp: return {"status": "error", "message": "OTP not received"}

            resp = s.post(check_confo, data={"code": otp, "device_id": mid, "email": email}, headers=headers)
            signup_code = resp.json().get("signup_code")
            if not signup_code: return {"status": "error", "message": "Failed to get signup code"}

            final_payload = {
                "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}",
                "email": email, "username": username, "first_name": "User",
                "month": "1", "day": "18", "year": "1995", "opt_into_one_tap": "false",
                "client_id": mid, "seamless_login_enabled": "1", "tos_version": "row",
                "force_sign_up_code": signup_code,
            }
            
            resp = s.post(final_create_url, data=final_payload, headers=headers)
            resp_text = resp.text
            if "account_created" in resp_text.lower() and "true" in resp_text.lower():
                return {
                    "status": "success",
                    "username": username,
                    "password": password,
                    "email": email,
                    "response": resp.json()
                }
            else:
                return {"status": "fail", "message": "Instagram rejected creation", "response": resp.json() if resp.status_code == 200 else resp_text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "running", "endpoints": ["/gen"]})

@app.route('/gen', methods=['GET'])
def gen_accounts():
    count = request.args.get('count', default=1, type=int)
    if count > 5: count = 5  # Limit per request
    
    results = []
    for _ in range(count):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(create_instagram_account())
        results.append(result)
        if count > 1: time.sleep(10) # Small delay between multiple creations in one request
        
    return jsonify(results)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

# Export the app for Vercel
app = app
