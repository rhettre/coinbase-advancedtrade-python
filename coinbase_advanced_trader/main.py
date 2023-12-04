from coinbase_client import listAccounts, listPortfolios, getPortfolioBreakdown
from config import set_api_credentials
def main():
    set_api_credentials()

    #List accounts
    print(listAccounts())

    #ListPortfolios
    portfolioList = listPortfolios()
    print(portfolioList)

    #Portfolio breakdown (of first portfolio)
    portfolio_uuid = portfolioList['portfolios'][0]['uuid']
    print(getPortfolioBreakdown(portfolio_uuid))

if __name__ == "__main__":
    main()
