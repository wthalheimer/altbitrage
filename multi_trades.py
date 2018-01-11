import ccxt
import itertools

# Manual here:
# https://github.com/ccxt/ccxt/wiki/Manual

# Exchanges
bittrex = ccxt.bittrex() # 271 markets
binance = ccxt.binance() # 238 markets
poloniex = ccxt.poloniex()  # 99 markets
kraken   = ccxt.kraken()  # 59 markets
cex      = ccxt.cex()  # 27 markets
bitstamp = ccxt.bitstamp()  # 15 markets
gdax     = ccxt.gdax()  # 10 markets

exchanges = [bittrex, binance]

# Load markets and check if exchanges are working
working_exchanges = []
for exchange in exchanges:
    # Try loading the markets, if you can, add it to the working exchanges list
    try:
        exchange.load_markets()
        working_exchanges.append(exchange)
    # If you cannot, say so, and dont add it to the list
    except:
        print('%s is down! Excluding %s' % (exchange.name, exchange.name))

# Padding for printing out names
pad = max([len(exchange.name) for exchange in working_exchanges])

# Print how many markets are in each exchange
print('Analyzing...')
[print('%-*s: %i markets' % (pad, exchange.name, len(exchange.markets))) for exchange in working_exchanges]
print('')


# A fetch ticker method that will handle USD/USDT naming
def fetch_ticker(exchange, pair):
    # If the pair ends with USD and the exchange uses USDT naming convention
    if (pair[-3:] == 'USD') and (exchange.name in ['Poloniex', 'Bittrex']):
        # Append T on the end of the ticker so it ends with USDT
        pair = pair + 'T'

    # Get the information
    maker_fee = exchange.markets[pair]['maker']
    taker_fee = exchange.markets[pair]['taker']
    rate = exchange.fetch_ticker(pair)['last']

    # Simplify the fee as average of maker and taker
    fee = (maker_fee + taker_fee) / 2.

    return rate, fee

# A method to get the intersection of 2 lists
def intersection(list1, list2):
    return list(set(list1).intersection(set(list2)))


# The Trade class groups helpful information
# Using example: BCH/ETH
class Trade:
    def __init__(self, pair, hi_trade_list, hi_value, hi_fee, lo_trade_list, lo_value, lo_fee):
        self.pair = pair
        self.hi_trades = hi_trade_list  # Highest value trade list: ['BCH/USD','ETH/USD'] Value: 3.5
        self.hi_value  = hi_value
        self.hi_fee    = hi_fee
        self.lo_trades = lo_trade_list  # Lowest  value trade list: ['BCH/BTC','ETH/BTC'] Value: 3.4
        self.lo_value  = lo_value
        self.lo_fee    = lo_fee
        # TODO: Must account for bid/ask
        # TODO: Must account for transaction fees


# List of slow moving coins
slow_coins = ['BTC', 'ETH']

# List of fast moving coins
fast_coins = ['XRB', 'XRP', 'ARK', 'NAV', 'XEM', 'STEEM', 'STRAT', 'XMR', 'LTC', 'DASH']

# List (over each exchange) of lists of trades (of all base-to-base pairs)
master_trade_list = []

# Determine the list of pairs that can be used
base_to_base_pairs_per_exchange = []

# Loop over the exchanges
for exchange in exchanges:
    # List of all the pairs
    pairs = list(exchange.markets.keys())

    # List of all the bases
    bases = [pair.split('/')[0] for pair in pairs]

    # Find all the fast coins that the exchange uses (so you can transfer quickly)
    fast_bases = intersection(bases, fast_coins)

    # List of all the combinations of fast bases
    base_to_base_pairs = list(itertools.combinations(fast_bases, 2))

    base_to_base_pairs_per_exchange.append(base_to_base_pairs)

# Find common pairs between exchanges
common_pairs = base_to_base_pairs_per_exchange[0]
for i in range(1,len(base_to_base_pairs_per_exchange)):
    common_base_to_base_pairs = intersection(common_pairs, base_to_base_pairs_per_exchange[i])

# Loop over the exchanges
for exchange in exchanges:
    print('Analyzing %s pairs:' %(exchange.name))

    # List of all the pairs
    pairs = list(exchange.markets.keys())

    # List of all the trades at the specific exchange
    exchange_trade_list = []

    # Loop over the base_pairs
    i = 0
    for base_to_base_pair in common_base_to_base_pairs:
        # Get the "new" base and quote
        new_base = base_to_base_pair[0]
        new_quote = base_to_base_pair[1]

        # Name the pair as if it were to appear on the exchange
        pair_name = new_base + '/' + new_quote

        # Print pair
        if i < 10:
            i += 1
        else:
            i = 1
            print('')
        print('%-14s' %(pair_name), end='')

        # List of all the pairs involving the "new" base and pair
        pairs_with_base = [pair for pair in pairs if pair.split('/')[0] == new_base]
        pairs_with_quote = [pair for pair in pairs if pair.split('/')[0] == new_quote]

        # Make lists of the quotes involved with each of the above trades
        quotes_from_pairs_with_base = [pair.split('/')[1] for pair in pairs_with_base]
        quotes_from_pairs_with_quote = [pair.split('/')[1] for pair in pairs_with_quote]

        # Find the in-common quotes (these are the currencies you can bounce between within a single exchange)
        common_coins = intersection(quotes_from_pairs_with_base, quotes_from_pairs_with_quote)

        # Empty list for names and values of the double-trades
        double_trade_names = []
        double_trade_values = []
        fees = []

        # Loop over the different "paths", where a path is 2 trades
        # Example: New base is DOGE, new quote is ETH, common coin is BTC
        #          Path is DOGE->BTC->ETH
        for common_coin in common_coins:
            # Name the trades (the common coin is the quote in both trades)
            first_pair = new_base + '/' + common_coin  # You will SELL this pair
            secnd_pair = new_quote + '/' + common_coin  # You will BUY this pair

            # Find the values of the pairs
            first_rate, first_fee = fetch_ticker(exchange, first_pair)
            secnd_rate, secnd_fee = fetch_ticker(exchange, secnd_pair)

            # Lists for the Trade class
            trade_list = [first_pair, secnd_pair]
            trade_value = first_rate * (1. / secnd_rate)  # TODO: Add fees, dont worry about them for now

            double_trade_names.append(trade_list)
            double_trade_values.append(trade_value)
            fees.append((first_fee+secnd_fee)/2.) # Use the average of the fees

        # Find max and min values
        hi_value      = max(double_trade_values)
        hi_trade_list = double_trade_names[double_trade_values.index(hi_value)]
        hi_fee        = fees              [double_trade_values.index(hi_value)]

        lo_value      = min(double_trade_values)
        lo_trade_list = double_trade_names[double_trade_values.index(lo_value)]
        lo_fee        = fees              [double_trade_values.index(hi_value)]

        # Make a Trade object to track the highest and lowest trades
        new_trade = Trade(pair_name, hi_trade_list, hi_value, hi_fee, lo_trade_list, lo_value, lo_fee)

        # Add the Trade to the exchange-specific trade list
        exchange_trade_list.append(new_trade)

    # Add the list of Trades to the master trade list
    master_trade_list.append(exchange_trade_list)
    print('\n')

foo = 1
