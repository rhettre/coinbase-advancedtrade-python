from coinbase_advanced_trade.CBAClient import CBAClient
from coinbase_advanced_trade.product import Product
from coinbase_advanced_trade.account import Account
from coinbase_advanced_trade.strategies.fear_and_greed_strategies import trade_based_on_fgi_simple, trade_based_on_fgi_pro
my_client = CBAClient(simulate=True) # setting this to false will actually make trades if it's false
my_accounts: dict[str, Account] = my_client.getAccountsDict()
for account_key in my_accounts:
    print(my_accounts[account_key])    
products: dict[str, Product] = my_client.getProductsDict() #type: ignore kwargs
for product_key in products:
    print(products[product_key])
print(f"you currently have ${my_client.get_current_funds()} to trade with")
sol: Product = products['SOL-USD']
print(sol)
my_client.buy(sol, fiat_amount=10.00)
my_client.buy(sol,quantity=0.1)
my_client.buy(sol,percentage_of_funds=0.1)
my_client.buy(sol,fiat_amount=10.00, current_price_ratio=0.9)
my_client.buy(sol,fiat_amount=10.0,price=85.0)
my_client.sell(sol,fiat_amount=10.00)
my_client.sell(sol,quantity=0.1)
my_client.sell(sol,percentage_of_currency=0.1)
my_client.sell(sol,fiat_amount=10.00, current_price_ratio=1.1)
my_client.sell(sol,fiat_amount=10.0,price=110.0)
my_client.sell(sol,quantity=0.1,price=110.0)
trade_based_on_fgi_simple("SOL-USD",fiat_amount=1.00,client=my_client)
shib: Product = my_client.getProduct("SHIB-USD")
trade_based_on_fgi_pro("SHIB-USD",fiat_amount=10.00,client=my_client)


accounts: dict[str, Account] = my_client.getAccountsDict()
total_value:float = sum([accounts[account_key].current_value for account_key in accounts])

print(f"Total Value: {total_value}")    

