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
verbose                = False # Do not print market fetching status

# Exchanges with tether (you can transfer USDT between exchanges)
bittrex  = ccxt.bittrex()  # 266 markets
poloniex = ccxt.poloniex() # 99 markets
kraken   = ccxt.kraken()   # 59 markets

# Exchanges without tether (cannot transfer USD between exchanges)
cex      = ccxt.cex()      # 27 markets
bitstamp = ccxt.bitstamp() # 15 markets
gdax     = ccxt.gdax()     # 10 markets

exchanges = [bittrex, kraken, poloniex, gdax, cex, bitstamp]

# Load markets and check if exchanges are working
working_exchanges = []
for exchange in exchanges:
    # Try loading the markets, if you can, add it to the working exchanges list
    try:
        exchange.load_markets()
        working_exchanges.append(exchange)
    # If you cannot, say so, and dont add it to the list
    except:
        print('%s is down! Excluding %s'%(exchange.name, exchange.name))

# Padding for printing out names
pad = max([len(exchange.name) for exchange in working_exchanges])

# Print how many markets are in each exchange
print('Analyzing...')
[print('%-*s: %i markets' %(pad,exchange.name,len(exchange.markets)) ) for exchange in working_exchanges]
print('')

#_______________________________________________________________
# Find which pairs are in common between exchanges with tether

exchanges_with_tether = [bittrex, kraken, poloniex] # All the exchanges supporting tether

# Make sure all the exchanges are working
exchanges = [exchange for exchange in exchanges_with_tether if exchange in working_exchanges]
print('Looking at exchanges:', end=' ')
[print(exchange.name, end=', ') for exchange in exchanges]
print('')

markets = [exchange.markets for exchange in exchanges]
pairs   = [[pair for pair in market.keys()] for market in markets]

# It is clear that all these markets deal with USDT, so if they explicitly name USDT, convert to USD
for i in range(len(pairs)):
    for j in range(len(pairs[i])):
        if pairs[i][j][-4:] == 'USDT':
            pairs[i][j] = pairs[i][j][:-1] # Remove the trailing T

# Find the common traded pairs between the exchanges
common_pairs = set.intersection(*[set(list) for list in pairs])

# A fetch ticker method that will handle USD/USDT naming
def fetch_ticker(exchange, pair):
    # If the pair ends with USD and the exchange uses USDT naming convention
    if (pair[-3:] == 'USD') and (exchange.name in ['Poloniex', 'Bittrex']):
        # Append T on the end of the ticker so it ends with USDT
        return exchange.fetch_ticker(common_pair+'T')['last']
    # Otherwise, just query the exchange per usual
    else:
        return exchange.fetch_ticker(common_pair)['last']



# Loop over the in-common pairs and generate list of prices for those pairs
# [ Pair1: [Exchange1_Price, Exchange2_Price, ...]
#   Pair2: [Exchange1_Price, Exchange2_Price, ...]
#   PairN: [Exchange1_Price, Exchange2_Price, ...] ]
common_pair_prices = []
for common_pair in common_pairs:
    specific_pair_prices = []
    # Loop over the exchanges
    for exchange in exchanges:
        price = 0
        # Use a while loop to keep querying the exchange if the connection is bad
        while price == 0:
            if verbose: print('Trying to fetch ticker %-9s from %-8s'%(common_pair,exchange.name), end='...')
            # Try it in case of bad connection
            try:
                price = fetch_ticker(exchange, common_pair)
                specific_pair_prices.append( price )
                if verbose: print('Success!')
            except:
                if verbose: print('Failed, trying again...')

    common_pair_prices.append(specific_pair_prices)
print('')

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
        'min_price'   : min_price,
        'max_exchange': max_exchange,
        'max_price'   : max_price,
    }
    arbitrage_opportunities.append(results)

# Sort best arbitrage opportunities (use reverse=True to sort descending)
sorted_arb_opps = sorted(arbitrage_opportunities, key=lambda k: k['arbitrage'], reverse=True)

# Print best N_pairs_with_tether arbitrage opportunities
for i in range(min(N_pairs_with_tether, len(sorted_arb_opps))):
    print('%5.2f%% : %-12s : %-*s - Buy %-5s on %-*s for %.3e %-6s, sell %-6s on %-*s for %.3e %-5s'
          %( sorted_arb_opps[i]['arbitrage']*100., # Percent arbitrage available
             sorted_arb_opps[i]['pair'],
             2*pad,
             sorted_arb_opps[i]['min_exchange'] + '/' + sorted_arb_opps[i]['max_exchange'],
             sorted_arb_opps[i]['pair'].split('/')[0], # The base currency
             pad,
             sorted_arb_opps[i]['min_exchange'],
             sorted_arb_opps[i]['min_price'],
             sorted_arb_opps[i]['pair'].split('/')[1], # The quote currency
             sorted_arb_opps[i]['pair'].split('/')[0], # The base currency
             pad,
             sorted_arb_opps[i]['max_exchange'],
             sorted_arb_opps[i]['max_price'], # Exchange rate at max exchange
             sorted_arb_opps[i]['pair'].split('/')[1], # The quote currency
            ))


#_______________________________________________________________
# Find which pairs are in common between exchanges without tether
#  -> this means fiat currencies cannot be part of the trade as you cannot transfer them to close arbitrage loop

# Ranking of coins by transaction speed
# You want to buy the faster coin first so you can send it to the other exchange
# Basically, just avoid sending BTC at all costs...
# 1. RaiBlocks (XRB)
# 2. Ripple (XRP) (On the order of seconds)
# 3. Arkcoin (ARK)
# 4. Nav Coin (NAV)
# 5. NEM (XEM)
# 6. Steem (STEEM)
# 7. Stratis (STRAT)
# 8. Monero (XMR) (4 mins for first confirmation, 26 mins for 10 confirmations)
# 9. Litecoin (LTC) (10-30 minutes)
# 10. Dash (DASH)
# 11. Ethereum (ETH)
coins_by_speed = ['XRB', 'XRP', 'ARK', 'NAV', 'XEM', 'STEEM', 'STRAT', 'XMR', 'LTC', 'DASH', 'ETH']

# Exchanges sorted number of markets supported, most to least
exchanges_without_tether = [cex, bitstamp, gdax]

# Make sure all the exchanges are working
exchanges_without_tether = [exchange for exchange in exchanges_without_tether if exchange in working_exchanges]

# Loop over the echanges without tether, adding a new exchange to the exchange list on each iteration
for exchange in exchanges_without_tether:
    print('\nAdding exchange: %s' %(exchange.name))

    # Add next most inclusive exchange
    exchanges.append(exchange)

    markets = [exchange.markets for exchange in exchanges]
    pairs   = [[pair for pair in market.keys()] for market in markets]

    # Cannot quickly transfer fiat currencies between exchanges, so remove them
    fiat_currencies = ['USD','EUR','GBP','RUB']
    # Loop through the exchanges
    for i in range(len(pairs)):
        # Loop through the pairs traded on that exchange
        j = 0
        while j < len(pairs[i]):
            # If the quote is in fiat currency, remove that market
            if pairs[i][j][-3:] in fiat_currencies:
                pairs[i].remove(pairs[i][j])
            else:
                # Increment counter
                j += 1

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
            price = 0
            # Use a while loop to keep querying the exchange if the connection is bad
            while price == 0:
                if verbose: print('Trying to fetch ticker %-9s from %-8s'%(common_pair,exchange.name), end='...')
                # Try it in case of bad connection
                try:
                    price = fetch_ticker(exchange, common_pair)
                    specific_pair_prices.append( price )
                    if verbose: print('Success!')
                except:
                    if verbose: print('Failed, trying again...')

        common_pair_prices.append(specific_pair_prices)
    print('')

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
            'min_price'   : min_price,
            'max_exchange': max_exchange,
            'max_price'   : max_price,
        }
        arbitrage_opportunities.append(results)

    # Sort best arbitrage opportunities (use reverse=True to sort descending)
    sorted_arb_opps = sorted(arbitrage_opportunities, key=lambda k: k['arbitrage'], reverse=True)

    # Print best N_pairs_without_tether arbitrage opportunities
    for i in range(min(N_pairs_without_tether, len(sorted_arb_opps))):
        print('%5.2f%% : %-8s : %-*s - Buy %-5s on %-*s for %.3e %-6s, sell %-6s on %-*s for %.3e %-5s'
              %( sorted_arb_opps[i]['arbitrage']*100., # Percent arbitrage available
                 sorted_arb_opps[i]['pair'],
                 2*pad,
                 sorted_arb_opps[i]['min_exchange'] + '/' + sorted_arb_opps[i]['max_exchange'],
                 sorted_arb_opps[i]['pair'].split('/')[0], # The base currency
                 pad,
                 sorted_arb_opps[i]['min_exchange'],
                 sorted_arb_opps[i]['min_price'],
                 sorted_arb_opps[i]['pair'].split('/')[1], # The quote currency
                 sorted_arb_opps[i]['pair'].split('/')[0], # The base currency
                 pad,
                 sorted_arb_opps[i]['max_exchange'],
                 sorted_arb_opps[i]['max_price'], # Exchange rate at max exchange
                 sorted_arb_opps[i]['pair'].split('/')[1], # The quote currency
                ))


foo = 1