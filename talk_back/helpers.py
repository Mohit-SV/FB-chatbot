from django.conf import settings
import psycopg2
import re
import requests
import json
import datetime
import os


contexts = ['recipient_id',
            'name', 
            'email',
            'ph_no',
            'city',
            'pincode',
            'dob',
            'sex',
            'done']

questions = {
    'opening': ['Thank you for your interest!',
                "Let’s get started with your application! Please tell us your full name."],
    'email': 'Please tell us your email id (example: abc@xyz.com).',
    'ph_no': 'Please tell us your 10 digit mobile number.',
    'city': 'Please tell us which city you currently reside in.',
    'pincode': 'What is the pin code of your locality?',
    'dob': 'What is your date of birth? Please enter in this format: DD/MM/YYYY',
    'sex': {'question': 'Please select your gender.',
            'options': ['Male', 'Female', 'Other']},    
    'done': "Superb! You have reached the final step. We will ask you to upload related documents. You can upload them"
             " by taking their photos/ attaching the files on messenger."
}

doc_flow = ['profile pic', 'address proof', 'done']
id_flow = [1, 2, 0]


app_query = {
    'name': "Please tell us your full name (as mentioned in your application).",
    'ph_no': 'Kindly share your registered 10-digit mobile number.',
    'query': 'Please tell us your query.',
    'thank_him': 'Please tell us anything else if you would like to add.',
    'msged_again': "Thank you for sharing your details! Our customer service representatives will be in touch with "
                   "you soon. Thank you for your patience and understanding."
}

msgs = {
    'purpose_of_visit': ["Hi! Welcome to XXX. We ...! Please select any one of the following options to proceed:",
                         ['New Application', 'My application status']]
}

validators = {
    'ph_no':
         {"regex": r'^$|\d{10}$',
          "message": "That's not the valid format. Here's an example of correct input: 9800000000"},
    'email':
         {"regex": r'^([a-zA-Z0-9_\-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|'
                   r'(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$',
          "message": "That's not the valid format. Here's an example of correct input: abc@xyz.com"},
    'alphabet':
         {"regex": r'[a-zA-Z ]+',
          "message": "Data must be entered in Alphabets only."},
    'pincode':
         {"regex": r'^[1-9][0-9]{5}$',
          "message": "That's not the valid format. Here's an example of correct input: 400001."},
    'numeric':
         {"regex": r'[0-9]+',
          "message": "Data must be entered in Digits only."},
    'dob':
        {"regex": r'^([0-2][0-9]|(3)[0-1])(\/)(((0)[0-9])|((1)[0-2]))(\/)\d{4}$',
         "message": "That's not the valid format. Here's an example of correct input: 01/12/1990"}
}


def bot_processor(entry, bot, recipient_id):
    print("bot processor called")
    for message in entry['messaging']:
        # user at get started stage
        if 'postback' in message:
            if check_repeating_msg(str(message["postback"]["title"]), recipient_id):
                if message["postback"]["title"] == "New Application":
                    bot.send_action(recipient_id, 'typing_on')
                    try:
                        if user_fields_entered_in_table(recipient_id, "user_memory"):
                            db_call(f"delete from user_memory where id={recipient_id};")
                    except:
                        print(4)
                    db_call(f"INSERT INTO user_memory (id, memory) \
                                                                VALUES ({recipient_id}, 'New Application');")
                    try:
                        if present_param_index(recipient_id):
                            db_call(f"delete from main_data_table where id={recipient_id};")
                    except:
                        print(5)
                    db_call(f"INSERT INTO main_data_table (id) \
                                                                VALUES ({recipient_id});")
                    multiple_lines_msg(bot, recipient_id, questions["opening"])
                elif message["postback"]["title"] == "My application status":
                    bot.send_action(recipient_id, 'typing_on')
                    try:
                        if user_fields_entered_in_table(recipient_id, "main_data_table_queries", 'status'):
                            db_call(f"delete from main_data_table_queries where id={recipient_id};")
                    except:
                        print(2)
                    try:
                        if user_fields_entered_in_table(recipient_id, "user_memory"):
                            db_call(f"delete from user_memory where id={recipient_id};")
                    except:
                        print(3)
                    db_call(f"INSERT INTO user_memory (id, memory) \
                                                                VALUES ({recipient_id}, 'My application status');")
                    db_call(f"INSERT INTO main_data_table_queries (id) \
                                                    VALUES ({recipient_id});")
                    bot.send_text_message(recipient_id, app_query['name'])
            else:
                print("weird fb is sending repeated msgs 3")

        # user sent a message
        elif 'message' in message:
            if "is_echo" not in message['message']:
                context, next_context = get_context(recipient_id)

                    # if it is a text msg
                if "text" in message['message']:
                    response = message["message"]["text"]
                    mid = message["message"]["mid"]

                    if check_repeating_msg(mid, recipient_id):
                        bot.send_action(recipient_id, 'typing_on')
                        branching(response, recipient_id, bot)
                    else:
                        print('weird fb is sending repeated msgs 1')
                # if it is not text msg
                elif message['message']["attachments"][0]['type']:

                    mid = message["message"]["mid"]
                    if check_repeating_msg(mid, recipient_id):
                        bot.send_action(recipient_id, 'typing_on')
                        if context == "done":
                            url_fb = message['message']["attachments"][0]["payload"]["url"]
                            file_type = f""".{url_fb.split("/")[5].split(".")[1].split("?")[0]}"""
                            file_path = os.getcwd() + f"\\document\\{recipient_id}{file_type}"
                            r = requests.get(url_fb)
                            with open(file_path, 'wb') as f:
                                f.write(r.content)

                            next_doc = doc_flow[doc_flow.index(doc) + 1]
                            doc_id = id_flow[doc_flow.index(doc)]
                            next_doc_id = id_flow[doc_flow.index(doc) + 1]
                            print("uploading", doc, cust_id, loan_id, 'next_doc_id', next_doc_id)

                            if doc != 'done':
                                db_call(f"UPDATE doc_data SET doc='{next_doc}'"
                                        f"where id={recipient_id};") 
                                if send_file(recipient_id, doc_id, file_type) == 'file_creation_success':
                                    bot.send_text_message(recipient_id, "Your file has been successfully uploaded.")
                                    if next_doc != 'done':
                                        bot.send_text_message(recipient_id, f"Please upload your {next_doc}.")
                                    bot.send_action(recipient_id, 'typing_off')
                                    
                            elif doc == 'done':
                                bot.send_text_message(recipient_id, "We have received your details and will get in touch"
                                                                    " with you.")
                                                                    
                            else:
                                bot.send_text_message(recipient_id, "We have encountered a problem in submitting the file.")

                            if next_doc == 'done':
                                if 1: # replace 1 with fuction that verifies whether all the documents are uploaded perfectly
                                    db_call(f"UPDATE user_memory SET add_query='silent' where "
                                            f"id={recipient_id};")
                                    bot.send_text_message(recipient_id, "Hurray!! Your application has been submitted."
                                                                        "We will be updating the status via email and SMS.")
                                else:
                                    bot.send_text_message(recipient_id, "Problem occurred in forwarding of your docs. "
                                                                        "Please check whether all the files you are "
                                                                        "submitting are of image/pdf format and try "
                                                                        "uploading the documents by entering OK.")
                                    bot.send_action(recipient_id, 'typing_off')
                        else:
                            bot.send_text_message(recipient_id, "Please enter your details in text")
                    else:
                        print('weird fb is sending repeated msgs 2')
                else:
                    bot.send_text_message(recipient_id,
                                          "I'm sorry, I don't understand it. "
                                          "Please enter your responses in text.")
            else:
                bot.send_action(recipient_id, 'mark_seen')


def branching(response, recipient_id, bot):
    # passed branching stage and user is filling the application
    if present_param_index(recipient_id) and check_memory_table(recipient_id) == "New Application":
        apply_bot_message(recipient_id, response, bot)

    # passed branching stage and user is filling the application
    elif user_fields_entered_in_table(recipient_id, "main_data_table_queries", 'status') and \
            check_memory_table(recipient_id) == "My application status":
        status_bot_message(recipient_id, response, bot)

    # no user memory and didn't pick right options
    else:
        bot.send_text_message(recipient_id, "I'm sorry, I don't understand it. Please select one of the following only")
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
                                "image_url": '',
                                "subtitle": "",
                                # "subtitle": "We have the right hat for everyone.",
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


def apply_bot_message(recipient_id, response, bot):
        # open a record for the user
    context, next_context = get_context(recipient_id)
    if context != "done":
        if context in validators:
            if regex_validator(validators[context]['regex'], response):
                say = add_to_db(recipient_id, response, context)
                reply_msgs(next_context, recipient_id, say, bot)
            else:
                bot.send_text_message(recipient_id, validators[context]['message'])
        elif context in ['name', 'city']:
            if regex_validator(validators['alphabet']['regex'], response):
                say = add_to_db(recipient_id, response, context)
                reply_msgs(next_context, recipient_id, say, bot)
            else:
                bot.send_text_message(recipient_id, validators['alphabet']['message'])
        elif context == 'sex':
            if response in questions[context]['options']:
                say = add_to_db(recipient_id, response, context)
                bot.send_text_message(recipient_id,
                                      "We are uploading your details, please be on hold...")
                bot.send_action(recipient_id, 'typing_on')
                
                try:
                    db_call(f"delete from doc_data where id={recipient_id};")
                except:
                    print('new user')
                db_call(f"INSERT INTO doc_data (id, doc) VALUES ({recipient_id}, 'profile pic')")
                
                # upload details collected to remote db if needed
                
                if 1: # replace 1 with function to confirm submission of details
                    bot.send_text_message(recipient_id, "Your details are successfully forwarded")
                    reply_msgs(next_context, recipient_id, say, bot)
                    send_quick_reply(bot, recipient_id, "Type Ok to continue, or Cancel to start over.",
                                     ["Ok", "Cancel"])
                    bot.send_action(recipient_id, "typing_off")
                else:
                    bot.send_text_message(recipient_id, "Type cancel to again start over.")
            else:
                send_quick_reply(bot, recipient_id, "Answer the above question by selecting only from the "
                                                    "options given below.", questions[context]['options']) 
        else:
            say = add_to_db(recipient_id, response, context)
            reply_msgs(next_context, recipient_id, say, bot)

    elif context == "done":
        if response.lower() == "ok":
            bot.send_text_message(recipient_id, "Now please upload your profile pic.")
        elif response.lower() == "cancel":
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
                                    "title": "Hi! Welcome to Upwards Loans.",
                                    "image_url": "https://upwards-assets.s3.ap-south-1.amazonaws.com/shared/logo_without_text.png",
                                    "subtitle": "We provide loans upto Rs. 2 lakhs. Please select an option from the following:",
                                    # "subtitle": "We have the right hat for everyone.",
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
            content = response.content
            try:
                db_call(f"delete from main_data_table_response_memory where id={recipient_id};")
                db_call(f"delete from doc_data where id={recipient_id};")
            except:
                print("cancel tried to remove db records failed to do all")
        else:
            try:
                doc = fetch_4m_db(f"select doc from doc_data WHERE id = {recipient_id}")
                if doc[0][0] == 'profile pic':
                    bot.send_text_message(recipient_id, "Please enter OK to proceed to documents submission step.")
                elif doc[0][0] != "done":
                    bot.send_text_message(recipient_id, "Please continue the application process by uploading "
                                                        "the next document.")
                else:
                    bot.send_action(recipient_id, 'typing_off')
            except:
                bot.send_text_message(recipient_id, "Sorry, there has been a problem occured.")
        return "success"


def status_bot_message(recipient_id, response, bot):
    # passed branching stage and user has just sent a query
    if user_fields_entered_in_table(recipient_id, "main_data_table_queries", 'status') == 1:
        if regex_validator(validators['alphabet']['regex'], response):
            db_call(f"UPDATE main_data_table_queries SET name='{response}' where id={recipient_id};")
            bot.send_text_message(recipient_id, app_query['ph_no'])
        else:
            bot.send_text_message(recipient_id, validators['alphabet']['message'])
    elif user_fields_entered_in_table(recipient_id, "main_data_table_queries", 'status') == 2:
        if regex_validator(validators['ph_no']['regex'], str(response)):
            db_call(f"UPDATE main_data_table_queries SET ph_no='{response}' where id={recipient_id};")
            bot.send_text_message(recipient_id, app_query['query'])
        else:
            bot.send_text_message(recipient_id, validators['ph_no']['message'])
    elif user_fields_entered_in_table(recipient_id, "main_data_table_queries", 'status') == 3:
        db_call(f"UPDATE main_data_table_queries SET query='{response}' where id={recipient_id};")
        bot.send_text_message(recipient_id, app_query['thank_him'])
    # passed branching stage and user's query has been already entered into db
    else:
        xx = fetch_4m_db(f"select add_query from main_data_table_queries where id ={recipient_id}")
        print(xx)
        x = xx[0][0]
        if not (x == 1):
            bot.send_text_message(recipient_id, app_query['msged_again'])
            db_call(f"UPDATE main_data_table_queries \
                                    SET add_query= 1 \
                                    where id={recipient_id};")
        elif x == 1:
            db_call(f"UPDATE user_memory SET add_query='silent' where "
                    f"id={recipient_id};")
            print('user has more queries')

            
def reply_msgs(next_context, recipient_id, say, bot):
    bot_response = questions[next_context]
    # conditional responses from the bot
    if say:
        bot.send_text_message(recipient_id, say)
    elif isinstance(bot_response, str):
        bot.send_text_message(recipient_id, bot_response)
    elif isinstance(bot_response, list):
        multiple_lines_msg(bot, recipient_id, bot_response)
    elif isinstance(bot_response, dict):
        send_quick_reply(bot, recipient_id, bot_response['question'], bot_response['options'])
        # command to redirect user to opening his record
    else:
        bot.send_text_message(recipient_id, "Please type hi to continue.")

        
def check_repeating_msg(response, recipient_id):
    a = 0
    x = fetch_4m_db(f"select response from main_data_table_response_memory where id ={recipient_id} and response='{response}';")
    y = fetch_4m_db(f"select response from main_data_table_response_memory where id ={recipient_id};")
    print(f"x: {x}")
    print(f"y: {y}")
    if len(x) == 0:
        if len(y) == 0:
            db_call(f"Insert INTO main_data_table_response_memory (id, response) \
                                                        VALUES ({recipient_id}, '{str(response)}');")
        else:
            db_call(f"UPDATE main_data_table_response_memory SET response='{response}' where id={recipient_id};")
        a = True
        print(a)
        return a
    else:
        a = False
        print(a)
        return a


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


def user_fields_entered_in_table(recipient_id, table, purpose='default'):
    conn = psycopg2.connect(database=settings.DB['database'],
                            user=settings.DB['user'],
                            password=settings.DB['password'],
                            host=settings.DB['host'],
                            port=settings.DB['port'])
    cur = conn.cursor()
    if purpose == 'status':
        command = f"SELECT id, name, ph_no, query, add_query FROM {table} WHERE id = {recipient_id};"
    else:
        command = f"SELECT * FROM {table} WHERE id = {recipient_id};"
    cur.execute(command)
    try:
        query_result_list = cur.fetchall()
        # print(query_result_list)
        result = query_result_list[0]
        conn.commit()
        conn.close()
        try:
            index = result.index(None)
        except:
            index = len(result)
    except:
        index = 0
    return index


def check_memory_table(recipient_id):
    conn = psycopg2.connect(database=settings.DB['database'],
                            user=settings.DB['user'],
                            password=settings.DB['password'],
                            host=settings.DB['host'],
                            port=settings.DB['port'])
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM user_memory WHERE id = {recipient_id};")
    try:
        query_result_list = cur.fetchall()
        result = query_result_list[0]
        memory = result[1]
    except:
        print('db3 error')
        memory = 'None'
    return memory


def get_context(recipient_id):
    index = present_param_index(recipient_id)
    if index != 99999:
        context = contexts[index]
        next_context = contexts[index + 1]
    else:
        context = "done"
        next_context = "done"
    return context, next_context


def add_to_db(recipient_id, response, context):
    try:
        db_call(f"UPDATE main_data_table \
          SET {context}='{response}' \
          where id={recipient_id};")
        say = 0
    except:
        say = 'Please enter a valid input for this field.'
    return say


def present_param_index(recipient_id):
    conn = psycopg2.connect(database=settings.DB['database'],
                            user=settings.DB['user'],
                            password=settings.DB['password'],
                            host=settings.DB['host'],
                            port=settings.DB['port'])
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM main_data_table WHERE id = {recipient_id};")
    listed = cur.fetchall()
    try:
        result = listed[0]
        try:
            index = result.index(None)
        except:
            index = 99999
    except:
        index = 0
    conn.commit()
    conn.close()
    return index


def send_quick_reply(bot, recipient_id, text, quick_replies):
    replies_payload = []
    for item in quick_replies:
        replies_payload.append({
            "content_type": "text",
            "title": item,
            "payload": "<POSTBACK_PAYLOAD>",
            # "image_url": "http://example.com/img/red.png"
        })
    payload = {
        "recipient": {
            "id": recipient_id
        },
        "messaging_type": "RESPONSE",
        "message": {
            "text": text,
            "quick_replies": replies_payload
        }
    }
    return bot.send_raw(payload)


def multiple_lines_msg(bot, recipient_id, items):
    for item in items:
        bot.send_text_message(recipient_id, item)


def fetch_4m_db(command):
    conn = psycopg2.connect(database=settings.DB['database'],
                            user=settings.DB['user'],
                            password=settings.DB['password'],
                            host=settings.DB['host'],
                            port=settings.DB['port'])
    cur = conn.cursor()
    cur.execute(command)
    listed = cur.fetchall()
    conn.commit()
    conn.close()
    return listed


def regex_validator(regex, input1):
    m = re.match(regex, input1)
    if m:
        return True
    else:
        return False


def send_file(recipient_id, doc_id, file_type):
    """must return ''file_creation_success'' on successful upload"""
    
    file_path = os.getcwd() + f"\\document\\{recipient_id}{file_type}"

    file = open(file_path, 'rb')
    
    #### write code to upload the file to remote location

    try:
        os.remove(file_path)
        print("Found and Removed!")
    except:
        print(33)

    return status
