import json
from django.views import generic
from rest_framework.views import APIView
from django.http.response import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .helpers import bot_processor
from pymessenger.bot import Bot
import requests
from django.conf import settings
from talk_back import serializers
import psycopg2

bot = Bot(settings.ACCESS_TOKEN, app_secret=settings.APP_SECRET)


class Talk_Back_View(generic.View):
    post_data = {
        "get_started": {"payload": "<postback_payload>"},
        "greeting": [
            {
                "locale": "default",
                "text": "Hello {{user_first_name}}!"
            },
        ]
    }
    headers = {'Content-type': 'application/json'}
    response = requests.post(f"https://graph.facebook.com/v2.6/me/messenger_profile?access_token={settings.ACCESS_TOKEN}",
                             data=json.dumps(post_data), headers=headers)
    content = response.content

    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == settings.VERIFY_TOKEN:
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse('Error, invalid token')

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        for entry in incoming_message['entry']:
            # print(entry)
            recipient_id = int(entry["messaging"][0]['sender']['id'])
            if is_silent(recipient_id, entry):
                print("I'm silent")
            else:
                bot_processor(entry, bot, recipient_id)
        return HttpResponse()
        

def is_silent(recipient_id, entry):
    try:
        if entry['messaging'][0]["postback"]["title"] == "Get Started":
            # bot.send_action(recipient_id, 'typing_on')
            post_data = {
                "recipient": {
                    "id": f"{recipient_id}"
                },
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "generic",
                            "elements": [
                                {
                                    "title": "Hi! Welcome to XXXX.",
                                    "image_url": "",
                                    "subtitle": "",
                                    # "subtitle": "",
                                    # "default_action": {
                                    #     "type": "web_url",
                                    #     "url": "",
                                    #     "webview_height_ratio": "tall",
                                    # },
                                    "buttons": [
                                        {
                                            "type": "postback",
                                            "title": "New Application",
                                            "payload": "New Application"
                                        },
                                        {
                                            "type": "postback",
                                            "title": "My application status",
                                            "payload": "My application status"
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
            headers = {'Content-type': 'application/json'}
            response = requests.post(
                f"https://graph.facebook.com/v2.6/me/messages?access_token={settings.ACCESS_TOKEN}",
                data=json.dumps(post_data), headers=headers)
            # bot.send_action(recipient_id, 'typing_off')
            content = response.content
            db_call(f"delete from main_data_table_response_memory where id={recipient_id};")
            print("Get started")
            return False
    except:
        conn = psycopg2.connect(database=settings.DB['database'],
                                user=settings.DB['user'],
                                password=settings.DB['password'],
                                host=settings.DB['host'],
                                port=settings.DB['port'])
        cur = conn.cursor()
        command = f"select add_query from user_memory where id = {recipient_id};"
        cur.execute(command)
        try:
            x = cur.fetchall()[0][0]
            conn.commit()
            conn.close()
            if x == "silent":
                return True
            else:
                return False
        except:
            conn.commit()
            conn.close()
            return False


def db_call(command):
    conn = psycopg2.connect(database=settings.DB['database'],
                            user=settings.DB['user'],
                            password=settings.DB['password'],
                            host=settings.DB['host'],
                            port=settings.DB['port'])
    cur = conn.cursor()
    cur.execute(command)
    conn.commit()
    conn.close()