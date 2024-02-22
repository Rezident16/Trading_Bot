from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime 
from alpaca_trade_api import REST 
from timedelta import Timedelta 
from finbert_utils import estimate_sentiment
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = os.getenv("BASE_URL")

ALPACA_CREDS = {
    "API_KEY":API_KEY, 
    "API_SECRET": API_SECRET, 
    "PAPER": False
}
class MLTrader(Strategy): 
    def initialize(self, symbols, cash_at_risk:float=.5): 
        self.symbols = symbols
        self.sleeptime = "24H" 
        self.last_trade = {symbol:None for symbol in symbols} 
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)

    def position_sizing(self, symbol): 
        cash = self.get_cash()
        last_price = self.get_last_price(symbol)
        if last_price == None:
            last_price = 0
        quantity = 0 if last_price == 0 or cash < 0 else round(cash * self.cash_at_risk / last_price, 0)
        return cash, last_price, quantity

    def get_dates(self): 
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_sentiment(self, symbol): 
        today, three_days_prior = self.get_dates()
        news = self.api.get_news(symbol=symbol, 
                                 start=three_days_prior, 
                                 end=today) 
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment, today
    
    # def before_market_opens(self):
    #     self.cancel_open_orders()

    def on_trading_iteration(self):
        for symbol in self.symbols:
            cash, last_price, quantity = self.position_sizing(symbol) 
            probability, sentiment, today = self.get_sentiment(symbol)
            if cash > last_price: 
                if sentiment == "positive" and probability > .9: 
                    if self.last_trade[symbol] == "sell": 
                        position = self.get_position(symbol)
                        if position:
                            if position.quantity < 0:
                                position.quantity = -position.quantity
                            sell_order = self.get_selling_order(position)
                            self.submit_order(sell_order)
                    if self.last_trade[symbol] != "buy":
                        if quantity > 0:
                            order = self.create_order(
                                symbol, 
                                quantity, 
                                "buy", 
                                type="bracket", 
                                take_profit_price=round(last_price*1.15, 2), 
                                stop_loss_price=round(last_price*.97,2)
                            )
                            self.submit_order(order) 
                            self.last_trade[symbol] = "buy"
                            print(today, order, 'BUY', sentiment, probability)
                elif sentiment == "negative" and probability > .999: 
                    if self.last_trade[symbol] == "buy": 
                        position = self.get_position(symbol)
                        if position and position.quantity > 0:
                            sell_order = self.get_selling_order(position)
                            self.submit_order(sell_order)
                    if self.last_trade[symbol] != "sell":
                        if abs(quantity) > 0:
                            order = self.create_order(
                                symbol, 
                                quantity, 
                                "sell", 
                                type="bracket", 
                                take_profit_price=round(last_price*.85), 
                                stop_loss_price=round(last_price*1.05)
                            )
                            self.submit_order(order) 
                            self.last_trade[symbol] = "sell"
                            print(today, order, 'SHORT', sentiment, probability)
start_date = datetime(2022,1,1)
end_date = datetime(2024,2,1) 
broker = Alpaca(ALPACA_CREDS)


strategy = MLTrader(name='mlstrat', broker=broker, 
                    parameters={"symbols":["SPY", "QQQ", "TQQQ", "SOXL", "MSFT", "AAPL", "GOOG", "GOOGL", "AMZN", "NVDA", "META", "LLY", "TSLA",
"AVGO", "V", "JPM", "UNH", "WMT", "MA", "XOM", "JNJ", "PG", "HD", "MRK", "ORCL", "COST", "ABBV", "CVX",
"CRM", "ADBE", "AMD", "BAC", "KO", "NFLX", "PEP", "ACN", "TMO", "MCD", "CSCO", "LIN", "ABT", "TMUS",
"DHR", "DIS", "INTC", "INTU", "WFC", "CMCSA", "VZ", "IBM", "CAT", "QCOM", "NOW", "AMGN", "NKE", "PFE",
"AXP", "BX", "UNP", "GE", "SPGI", "UBER", "TXN", "AMAT", "PM", "MS", "ISRG", "COP", "SYK", "BA", "LMT",
"MDT", "GS", "FDX", "TGT", "HON", "MMM", "RTX", "DE", "SO", "C", "NET", "ANET", "PANW", "DDOG", "CDNS",
"CMG", "SNPS", "SOFI", "QLD", "RBLX", "SNOW", "CPRT", "FTEC", "METV", "QQQM", "KNSL", "MPWR", "SOXX",
"PTC", "BRO", "TWLO", "TYL", "FTNT", "ADSK", "APH", "CDW", "VEEV", "SPYG", "VTI", "VOO", "EQIX", "MSI",
"ON", "BLK", "WM", "QQQJ", "ADI", "SCHD", "CSGP", "JEPI", "PLTR", "TLRY", "TDOC", "SAVE", "CHPT", "DHI",
"EOG", "LRCX", "KLAC", "FI", "MU", "WDAY", "CRWD", "DELL", "ROP", "MRVL", "TEAM", "SMCI", "MCHP", "REGN",
"VRTX", "ELV", "SCHW", "PGR", "MMC", "APO", "KKR", "ICE", "NEE", "DUK", "PLD", "AMT", "WELL", "UPS", "APD",
"EW", "AJG", "COF", "EL", "OXY", "ZTS", "F", "ET", "WBD", "HPE", "SNAP", "ZM", "ROKU", "PYPL", "SQ"
    ],
                                "cash_at_risk":.25})

# strategy.backtest(
#     YahooDataBacktesting, 
#     start_date, 
#     end_date, 
#     parameters={"symbols":[
# "SPY", "QQQ", "TQQQ", "SOXL", "MSFT", "AAPL", "GOOG", "GOOGL", "AMZN", "NVDA", "META", "LLY", "TSLA",
# "AVGO", "V", "JPM", "UNH", "WMT", "MA", "XOM", "JNJ", "PG", "HD", "MRK", "ORCL", "COST", "ABBV", "CVX",
# "CRM", "ADBE", "AMD", "BAC", "KO", "NFLX", "PEP", "ACN", "TMO", "MCD", "CSCO", "LIN", "ABT", "TMUS",
# "DHR", "DIS", "INTC", "INTU", "WFC", "CMCSA", "VZ", "IBM", "CAT", "QCOM", "NOW", "AMGN", "NKE", "PFE",
# "AXP", "BX", "UNP", "GE", "SPGI", "UBER", "TXN", "AMAT", "PM", "MS", "ISRG", "COP", "SYK", "BA", "LMT",
# "MDT", "GS", "FDX", "TGT", "HON", "MMM", "RTX", "DE", "SO", "C", "NET", "ANET", "PANW", "DDOG", "CDNS",
# "CMG", "SNPS", "SOFI", "QLD", "RBLX", "SNOW", "CPRT", "FTEC", "METV", "QQQM", "KNSL", "MPWR", "SOXX",
# "PTC", "BRO", "TWLO", "TYL", "FTNT", "ADSK", "APH", "CDW", "VEEV", "SPYG", "VTI", "VOO", "EQIX", "MSI",
# "ON", "BLK", "WM", "QQQJ", "ADI", "SCHD", "CSGP", "JEPI", "PLTR", "TLRY", "TDOC", "SAVE", "CHPT", "DHI",
# "EOG", "LRCX", "KLAC", "FI", "MU", "WDAY", "CRWD", "DELL", "ROP", "MRVL", "TEAM", "SMCI", "MCHP", "REGN",
# "VRTX", "ELV", "SCHW", "PGR", "MMC", "APO", "KKR", "ICE", "NEE", "DUK", "PLD", "AMT", "WELL", "UPS", "APD",
# "EW", "AJG", "COF", "EL", "OXY", "ZTS", "F", "ET", "WBD", "HPE", "SNAP", "ZM", "ROKU", "PYPL", "SQ"
#     ], "cash_at_risk":.25}
# )
trader = Trader()
trader.add_strategy(strategy)
trader.run_all()
