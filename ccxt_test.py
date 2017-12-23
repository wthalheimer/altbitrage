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

# Exchanges with tether (you can transfer USDT between exchanges)
bittrex  = ccxt.bittrex()
kraken   = ccxt.kraken()

# Exchanges without tether (cannot transfer USD between exchanges)
gdax = ccxt.gdax()
cex  = ccxt.cex()
bitstamp = ccxt.bitstamp()

# Load markets
bittrex.load_markets()
kraken.load_markets()
# bitstamp.load_markets()
# gdax.load_markets()
# cex.load_markets()

#_______________________________________________________________
# Find which pairs are in common between exchanges with tether
exchanges = [bittrex, kraken]

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
        except:
            # Otherwise, try with USDT instead if the pair ends with USD
            if common_pair[-3:]=='USD':
                specific_pair_prices.append( exchange.fetch_ticker(common_pair+'T')['last'] )
            # Or, just try the pair again in case of bad connection
            else:
                specific_pair_prices.append( exchange.fetch_ticker(common_pair)['last'] )

    common_pair_prices.append(specific_pair_prices)

# Loop over the prices for the in-common pairs and generate list of dictionaries for price differentials
# [ Pair1: {'pair', 'arbitrage', 'min_exchange', 'max_exchange'}
#   Pair2: {'pair', 'arbitrage', 'min_exchange', 'max_exchange'}
#   PairN: {'pair', 'arbitrage', 'min_exchange', 'max_exchange'} ]

arbitrage_opportunities = []
for price_list, pair in zip(common_pair_prices, common_pairs):
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

foo = 1