import logging
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, PollAnswerHandler, CallbackContext
import requests
import schedule
import time
import threading

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants (Insert Your KEYS)
# Use coinmarketcap or whatever you prefer
TOKEN = 'INSERT_KEY'
COINMARKETCAP_API_KEY = 'INSERT_KEY'
CRYPTO_API_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={coin}&convert=USD'
VOTES = {}
COIN = 'INSERT_YOUR_COIN'  # Set the specific coin here

def get_coin_data():
    response = requests.get(CRYPTO_API_URL)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]  # The first item contains data for the coin
        else:
            return None
    else:
        return None

# Function to get current crypto price
def get_crypto_price():
    headers = {
        'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
        'Accepts': 'application/json'
    }
    response = requests.get(CRYPTO_API_URL.format(coin=COIN), headers=headers)
    data = response.json()
    return data['data'][COIN]['quote']['USD']['price']

def get_market_cap():
    coin_data = get_coin_data()
    if coin_data:
        price = coin_data['current_price']
        market_cap = coin_data['market_cap']
        return price, market_cap
    else:
        return None, None

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f'Hi! Use /price to get the current price of {COIN}.')

# Price command
async def price(update: Update, context: CallbackContext) -> None:
    try:
        current_price = get_crypto_price()
        # Adjust the number of decimal places to show the full price
        await update.message.reply_text(f'The current price of {COIN} is ${current_price:.10f}\n Use /poll to start a poll!')
    except Exception as e:
        await update.message.reply_text(f'Failed to fetch the price. Please try again. Error: {e}')

# Market cap command
async def market_cap_command(update: Update, context: CallbackContext) -> None:
    price, market_cap = get_market_cap()
    if market_cap:
        message = f"The current market cap of {COIN} is ${market_cap:,.2f} and the price is ${price:,.12f}."
    else:
        message = "Failed to retrieve market cap data."
    await update.message.reply_text(message)
# Poll command
async def poll(update: Update, context: CallbackContext) -> None:
    poll_options = ['Up 10%', 'Up 50%', 'Up 100%', 'Moon', 'Down']
    await update.message.reply_poll(question='Price Prediction', options=poll_options, is_anonymous=False)

# Poll answer handler
async def receive_poll_answer(update: Update, context: CallbackContext) -> None:
    answer = update.poll_answer
    poll_id = answer.poll_id
    user_id = answer.user.id
    option_ids = answer.option_ids

    if poll_id not in VOTES:
        VOTES[poll_id] = {}
    VOTES[poll_id][user_id] = option_ids

# Periodic task to announce poll results
def announce_results(context: CallbackContext) -> None:
    for poll_id, votes in VOTES.items():
        results = {option: 0 for option in range(5)}
        for user_id, option_ids in votes.items():
            for option_id in option_ids:
                results[option_id] += 1

        results_message = 'Poll Results:\n'
        results_message += '\n'.join([f'{key}: {value} votes' for key, value in results.items()])
        context.bot.send_message(chat_id='INSERT_YOUR_CHAT_ID', text=results_message)
    VOTES.clear()

def main() -> None:
    # NAME YOUR COMMAND HANDLERS | ALSO MAKE SURE IT CORRELATES WITH THEIR FUNCTIONS

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("poll", poll))
    application.add_handler(CommandHandler("mcap", market_cap_command))
    application.add_handler(PollAnswerHandler(receive_poll_answer))

    # Start the Bot
    application.run_polling()

    # Schedule the weekly result announcement
    schedule.every().week.do(announce_results, context=application.job_queue)

    # Run the scheduler in a separate thread
    threading.Thread(target=lambda: schedule.run_pending()).start()

if __name__ == '__main__':
    main()