# Testing ccxt

import ccxt

# Manual here:
# https://github.com/ccxt/ccxt/wiki/Manual

# Base vs Quote
# Base is before the /
# Quote is after the /
# Base currency represents how much of the quote currency is needed
#    for you to get one unit of the base currency
# You are "buying" the base currency with the quote currency
# The quote currency is the denomination of the price
#     If quote is USD, price will be in dollars
#
# Ex: BTC/USD = 16000 means you need $16000 USD to buy 1 BTC
#     Note that BTC = 16000 USD, so by minipulating the fraction,
#     you can make it BTC/USD = 16000.
#     By using fraction multiplication:
#     (LTC/BTC)/(BTC/USD) = (LTC/USD)     - In an efficient market, no arb.
#
# The "taker" BUYS the base with the quote
# The "maker" SELLS the base for the quote

# Code inputs:
N_pairs_with_tether    = 10 # Number of pairs to print in exchanges possibly with tether
N_pairs_without_tether = 10 # Number of pairs to print in exchanges without tether

# Exchanges with tether (you can transfer USDT between exchanges)
bittrex  = ccxt.bittrex()  # 266 markets
poloniex = ccxt.poloniex() # 99 markets
kraken   = ccxt.kraken()   # 59 markets

# Exchanges without tether (cannot transfer USD between exchanges)
cex      = ccxt.cex()      # 27 markets
bitstamp = ccxt.bitstamp() # 15 markets
gdax     = ccxt.gdax()     # 10 markets

exchanges = [bittrex, kraken, poloniex, gdax, cex, bitstamp]

# Load markets
[exchange.load_markets() for exchange in exchanges]

# Print how many markets are in each exchange
print('Analyzing...')
[print('%-10s: %i markets' %(exchange.name,len(exchange.markets)) ) for exchange in exchanges]
print('')

#_______________________________________________________________
# Find which pairs are in common between exchanges with tether
exchanges = [bittrex, kraken, poloniex]

markets = [exchange.markets for exchange in exchanges]
pairs   = [[pair for pair in market.keys()] for market in markets]

# It is clear that all these markets deal with USDT, so if they explicitly name USDT, convert to USD
for i in range(len(pairs)):
    for j in range(len(pairs[i])):
        if pairs[i][j][-4:] == 'USDT':
            pairs[i][j] = pairs[i][j][:-1] # Remove the trailing T

# Find the common traded pairs between the exchanges
common_pairs = set.intersection(*[set(list) for list in pairs])

# Loop over the in-common pairs and generate list of prices for those pairs
# [ Pair1: [Exchange1_Price, Exchange2_Price, ...]
#   Pair2: [Exchange1_Price, Exchange2_Price, ...]
#   PairN: [Exchange1_Price, Exchange2_Price, ...] ]

common_pair_prices = []
for common_pair in common_pairs:
    specific_pair_prices = []
    # Loop over the exchanges
    for exchange in exchanges:
        # Append the last price from the exchange ticker
        # First try the pair as listed (might end with USD)
        try:
            specific_pair_prices.append( exchange.fetch_ticker(common_pair)['last'] )
        # Didnt work because either connection was bad, or you tried accessing USDT with the name USD
        except:
            price = 0
            while price == 0:
                print('Trying to fetch ticker %s from %s'%(common_pair,exchange.name), end='...')
                # Try it again in case of bad connection
                try:
                    price = exchange.fetch_ticker(common_pair)['last']
                    specific_pair_prices.append( price )
                    print('Success!')
                except:
                    # Try with 'T' appended
                    try:
                        print('with ''T'' appended''', end='...')
                        price = exchange.fetch_ticker(common_pair+'T')['last']
                        specific_pair_prices.append( price )
                        print('Success!')
                    except:
                        print('Failed, trying again...')


    common_pair_prices.append(specific_pair_prices)

# Loop over the prices for the in-common pairs and generate list of dictionaries for price differentials
# [ Pair1: {'pair', 'arbitrage', 'min_exchange', 'max_exchange'}
#   Pair2: {'pair', 'arbitrage', 'min_exchange', 'max_exchange'}
#   PairN: {'pair', 'arbitrage', 'min_exchange', 'max_exchange'} ]

arbitrage_opportunities = []
for price_list, pair in zip(common_pair_prices, common_pairs):
    # If the pair includes USD, name it USD(T) since we are technically dealing with tether
    if pair[-3:] == 'USD':
        pair += '(T)'

    min_price = min(price_list)
    max_price = max(price_list)

    min_exchange_index = price_list.index(min_price)
    max_exchange_index = price_list.index(max_price)

    min_exchange = exchanges[min_exchange_index].name
    max_exchange = exchanges[max_exchange_index].name

    arbitrage = max_price/min_price - 1.

    # Throw results into a dict and append to arbitrage_opportunities list
    results = {
        'pair'        : pair,
        'arbitrage'   : arbitrage,
        'min_exchange': min_exchange,
        'max_exchange': max_exchange,
    }
    arbitrage_opportunities.append(results)

# Print top 3 arbitrage opportunities (use reverse=True to sort descending)
sorted_arbitrage_opportunities = sorted(arbitrage_opportunities, key=lambda k: k['arbitrage'], reverse=True)
[print(sorted_arbitrage_opportunities[i]) for i in range(N_pairs_with_tether)]

#_______________________________________________________________
# Find which pairs are in common between exchanges without tether
#  -> this means fiat currencies cannot be part of the trade as you cannot transfer them to close arbitrage loop


# Ranking of coins by transaction speed
# You want to buy the faster coin first so you can send it to the other exchange
# Basically, just avoid sending BTC at all costs...
# 1. RaiBlocks (XRB)
# 2. Ripple (XRP)
# 3. Arkcoin (ARK)
# 4. Nav Coin (NAV)
# 5. NEM (XEM)
# 6. Steem (STEEM)
# 7. Stratis (STRAT)
# 8. Monero (XMR)
# 9. Litecoin (LTC)
# 10. Dash (DASH)
# 11. Ethereum (ETH)
coins_by_speed = ['XRB', 'XRP', 'ARK', 'NAV', 'XEM', 'STEEM', 'STRAT', 'XMR', 'LTC', 'DASH', 'ETH']


foo = 1