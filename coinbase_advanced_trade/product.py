from typing import Dict, Optional, List, Any
from colorama import Fore, Style


class Product:
    def __init__(self, data: Dict[str, Any]) -> None:
        # Validate the presence of required keys in the input dictionary
        required_keys: list[str] = [
            "product_id",
            "price",
            "price_percentage_change_24h",
            "volume_24h",
            "volume_percentage_change_24h",
            "base_increment",
            "quote_increment",
            "quote_min_size",
            "quote_max_size",
            "base_min_size",
            "base_max_size",
            "base_name",
            "quote_name",
            "watched",
            "is_disabled",
            "new",
            "status",
            "cancel_only",
            "limit_only",
            "post_only",
            "trading_disabled",
            "auction_mode",
            "product_type",
            "quote_currency_id",
            "base_currency_id",
        ]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing key '{key}' in input data")

        # Initialize attributes
        self.product_id: str = data["product_id"]
        self.price: float = float(data["price"])
        self.price_percentage_change_24h: float = float(
            data["price_percentage_change_24h"]
        )
        self.volume_24h: float = float(data["volume_24h"])
        self.volume_percentage_change_24h: float = float(
            data["volume_percentage_change_24h"]
        )
        self.base_increment: float = float(data["base_increment"])
        self.quote_increment: float = float(data["quote_increment"])
        self.quote_min_size: float = float(data["quote_min_size"])
        self.quote_max_size: float = float(data["quote_max_size"])
        self.base_min_size: float = float(data["base_min_size"])
        self.base_max_size: float = float(data["base_max_size"])
        self.base_name: str = data["base_name"]
        self.quote_name: str = data["quote_name"]
        self.watched: bool = data["watched"]
        self.is_disabled: bool = data["is_disabled"]
        self.new: bool = data["new"]
        self.status: str = data["status"]
        self.cancel_only: bool = data["cancel_only"]
        self.limit_only: bool = data["limit_only"]
        self.post_only: bool = data["post_only"]
        self.trading_disabled: bool = data["trading_disabled"]
        self.auction_mode: bool = data["auction_mode"]
        self.product_type: str = data["product_type"]
        self.quote_currency_id: str = data["quote_currency_id"]
        self.base_currency_id: str = data["base_currency_id"]
        self.fcm_trading_session_details: Optional[str] = data.get(
            "fcm_trading_session_details"
        )
        self.mid_market_price: Optional[str] = data.get("mid_market_price")
        self.alias: Optional[str] = data.get("alias")
        self.alias_to: Optional[List[str]] = data.get("alias_to")
        self.base_display_symbol: Optional[str] = data.get("base_display_symbol")
        self.quote_display_symbol: Optional[str] = data.get("quote_display_symbol")
        self.view_only: Optional[bool] = data.get("view_only")
        self.price_increment: Optional[str] = data.get("price_increment")
        self.display_name: Optional[str] = data.get("display_name")

    def __str__(self) -> str:
        try:
            price_change = float(self.price_percentage_change_24h)
            if price_change < 0:
                price_change_color = Fore.RED
            else:
                price_change_color = Fore.GREEN
        except ValueError:
            price_change_color = Fore.WHITE

        description = [
            f"{Fore.CYAN}Product ID:{Style.RESET_ALL} {self.product_id}",
            f"{Fore.CYAN}Name:{Style.RESET_ALL} {self.base_name} - {self.quote_name}",
            f"{Fore.CYAN}Price:{Style.RESET_ALL} {self.price}",
            f"{Fore.CYAN}24h Price Change:{Style.RESET_ALL} {price_change_color}{self.price_percentage_change_24h}%{Style.RESET_ALL}",
            f"{Fore.CYAN}24h Volume:{Style.RESET_ALL} {self.volume_24h}",
        ]

        # Adding boolean attributes only if they are True
        if self.watched:
            description.append(f"{Fore.GREEN}Watched{Style.RESET_ALL}")
        if self.is_disabled:
            description.append(f"{Fore.RED}Disabled{Style.RESET_ALL}")
        if self.new:
            description.append(f"{Fore.GREEN}New{Style.RESET_ALL}")
        if self.cancel_only:
            description.append(f"{Fore.YELLOW}Cancel Only{Style.RESET_ALL}")
        if self.limit_only:
            description.append(f"{Fore.YELLOW}Limit Only{Style.RESET_ALL}")
        if self.post_only:
            description.append(f"{Fore.YELLOW}Post Only{Style.RESET_ALL}")
        if self.trading_disabled:
            description.append(f"{Fore.RED}Trading Disabled{Style.RESET_ALL}")
        if self.auction_mode:
            description.append(f"{Fore.MAGENTA}Auction Mode{Style.RESET_ALL}")
        if self.view_only:
            description.append(f"{Fore.BLUE}View Only{Style.RESET_ALL}")

        return ", ".join(description)
