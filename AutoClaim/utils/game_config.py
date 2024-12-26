# Game list configuration
GAME_LIST = {
    'BLUM': {
        'name': 'Blum',
        'username': '@BlumCryptoBot',
        'description': 'Blum Crypto Game Bot',
        'assets_path': 'assets/blum/',
        # UI Elements
        'buttons': {
            'launch_game': 'Launch Blum',
            'join_community': 'Join community',
            'play': 'Start farming points now',
        },
        # Game settings
        'button_confidence': 0.7,
        'scan_interval': 0.1,
        'game_duration': 35,
        # Game specific messages
        'messages': {
            'welcome': 'Here\'s what you can do with Blum now:',
            'farm_points': '🎮 Farm Blum Points: Play our Drop Game',
            'invite_friends': '👥 Invite Friends: Bring your friends',
        }
    },
    'LITECOIN': {
        'name': 'Litecoin',
        'username': '@Litecoin_click_bot',
        'description': 'Litecoin Faucet Bot',
        'assets_path': 'assets/litecoin/',
        # UI Elements
        'buttons': {
            'start': '/start',
            'visit_sites': '🌐 Visit Sites',
            'balance': '💰 Balance',
            'withdraw': '🏧 Withdraw',
        },
        'button_confidence': 0.7,
        'scan_interval': 0.1,
        'game_duration': 3600,
        # Game specific messages
        'messages': {
            'welcome': 'Welcome to Litecoin Faucet Bot!',
            'balance': 'Your current balance is:',
            'minimum_withdraw': 'Minimum withdrawal:',
        }
    }
    # Template untuk menambah game baru:
    # 'GAME_KEY': {
    #     'name': 'Game Name',
    #     'username': '@GameUsername',
    #     'description': 'Game Description',
    #     'assets_path': 'assets/game/',
    #     'buttons': {
    #         'button_key': 'Button Text',
    #         ...
    #     },
    #     'button_confidence': 0.7,
    #     'scan_interval': 0.1,
    #     'game_duration': 0,
    #     'messages': {
    #         'message_key': 'Message Text',
    #         ...
    #     }
    # }
}

def get_game_config(game_key):
    """
    Mendapatkan konfigurasi game berdasarkan key
    """
    return GAME_LIST.get(game_key)

def get_all_games():
    """
    Mendapatkan list semua game yang tersedia
    """
    return [(key, game['name'], game['username']) for key, game in GAME_LIST.items()]

def get_button_text(game_key, button_key):
    """
    Mendapatkan teks button berdasarkan game dan key button
    """
    game_config = get_game_config(game_key)
    if game_config and 'buttons' in game_config:
        return game_config['buttons'].get(button_key)
    return None

def get_game_message(game_key, message_key):
    """
    Mendapatkan teks pesan berdasarkan game dan key pesan
    """
    game_config = get_game_config(game_key)
    if game_config and 'messages' in game_config:
        return game_config['messages'].get(message_key)
    return None 
    return [(key, game['name'], game['username']) for key, game in GAME_LIST.items()] 