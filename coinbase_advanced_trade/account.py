from typing import Dict, Optional, Any
from colorama import Fore, Style


class Account:
    def __init__(self, data: Dict[str, Any]) -> None:
        # Validate the presence of required keys in the input dictionary
        required_keys: list[str] = [
            "uuid",
            "name",
            "currency",
            "available_balance",
            "default",
            "active",
            "created_at",
            "updated_at",
            "type",
            "ready",
            "hold",
            "current_value",
        ]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing key '{key}' in input data")

        # Initialize attributes
        self.uuid: str = data["uuid"]
        self.name: str = data["name"]
        self.currency: str = data["currency"]
        self.available_balance: Dict[str, str] = data["available_balance"]
        self.default: bool = data["default"]
        self.active: bool = data["active"]
        self.created_at: str = data["created_at"]
        self.updated_at: str = data["updated_at"]
        self.deleted_at: Optional[str] = data.get("deleted_at")
        self.type: str = data["type"]
        self.ready: bool = data["ready"]
        self.hold: Dict[str, str] = data["hold"]
        self.current_value: float = float(data["current_value"])

    def __str__(self) -> str:
        description: list[str] = [
            f"{Fore.CYAN}UUID:{Style.RESET_ALL} {self.uuid}",
            f"{Fore.CYAN}Name:{Style.RESET_ALL} {self.name}",
            f"{Fore.CYAN}Available Balance:{Style.RESET_ALL} {self.available_balance['value']} {self.available_balance['currency']}",
            # f"{Fore.CYAN}Active:{Style.RESET_ALL} {'Yes' if self.active else 'No'}",
            # f"{Fore.CYAN}Ready:{Style.RESET_ALL} {'Yes' if self.ready else 'No'}",
            # f"{Fore.CYAN}Hold:{Style.RESET_ALL} {self.hold['value']}",
            f"{Fore.CYAN}Current Value USD:{Style.RESET_ALL} {self.current_value}",
        ]

        if self.deleted_at:
            description.append(
                f"{Fore.CYAN}Deleted At:{Style.RESET_ALL} {self.deleted_at}"
            )
        if float(self.hold["value"]) != 0.0:
            description.append(
                f"{Fore.RED}Hold:{Style.RESET_ALL} {self.hold['value']} {self.hold['currency']}"
            )

        return ", ".join(description)
