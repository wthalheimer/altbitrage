# Testing ccxt

import ccxt

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
bitstamp = ccxt.bitstamp()

# Exchanges without tether (cannot transfer USD between exchanges)
gdax = ccxt.gdax()
cex  = ccxt.cex()

# Load markets
bittrex.load_markets()
kraken.load_markets()
bitstamp.load_markets()
gdax.load_markets()
cex.load_markets()




foo = 1