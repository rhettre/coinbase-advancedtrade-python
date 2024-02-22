from coinbase_client import (
    listAccounts,
    listPortfolios
)
from config import set_api_credentials

def main():
    set_api_credentials()

    # List accounts
    print(listAccounts())

    #ListPortfolios
    print(listPortfolios())

if __name__ == "__main__":
    main()
