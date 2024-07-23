import http.client
import json

# Substitua 'YOUR_BOT_TOKEN' pelo token do seu bot
BOT_TOKEN = 'BOT-TOKEN'
COMMANDS = {}
WELCOME_FUNCTION = None

def send_request(method, params=None):
    conn = http.client.HTTPSConnection("api.telegram.org")
    url = f"/bot{BOT_TOKEN}/{method}"
    headers = {'Content-Type': 'application/json'}

    if params:
        conn.request("POST", url, body=json.dumps(params), headers=headers)
    else:
        conn.request("GET", url)
    
    response = conn.getresponse()
    data = response.read()
    return json.loads(data.decode())

def send_message(chat_id, text, parse_mode=None):
    params = {
        'chat_id': chat_id,
        'text': text
    }
    if parse_mode:
        params['parse_mode'] = parse_mode
    return send_request('sendMessage', params)

def get_updates(offset=None):
    params = {'timeout': 100}
    if offset:
        params['offset'] = offset
    return send_request('getUpdates', params)

def command(cmd):
    def decorator(func):
        COMMANDS[cmd] = func
        return func
    return decorator

def welcome(func):
    global WELCOME_FUNCTION
    WELCOME_FUNCTION = func
    return func

@command('/start')
def start_command(chat_id, message):
    send_message(chat_id, "Olá! Bem-vindo ao bot. Use /help para ver os comandos disponíveis.")

@command('/help')
def help_command(chat_id, message):
    help_text = (
        "Aqui estão os comandos disponíveis:\n"
        "/start - Iniciar conversa com o bot\n"
        "/help - Mostrar os comandos disponíveis"
    )
    send_message(chat_id, help_text)

@welcome
def welcome_new_members(chat_id, message):
    welcome_messages = []
    for member in message['new_chat_members']:
        if 'username' in member:
            mention = f"@{member['username']}"
        else:
            mention = f"[{member['first_name']}](tg://user?id={member['id']})"
        welcome_messages.append(f"Bem-vindo(a), {mention}!")
    
    welcome_message = "\n".join(welcome_messages)
    send_message(chat_id, welcome_message, parse_mode='Markdown')

def handle_updates(updates):
    for update in updates['result']:
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')

            if 'new_chat_members' in message and WELCOME_FUNCTION:
                WELCOME_FUNCTION(chat_id, message)
            elif text.startswith('/'):
                command_text = text.split()[0]
                try:
                    command_text = command_text.split('@')[0]  # Remove the bot's username
                except:
                    pass
                if command_text in COMMANDS:
                    COMMANDS[command_text](chat_id, message)

def main():
    offset = None
    while True:
        updates = get_updates(offset)
        if 'result' in updates and updates['result']:
            offset = updates['result'][-1]['update_id'] + 1
            handle_updates(updates)

if __name__ == "__main__":
    main()
