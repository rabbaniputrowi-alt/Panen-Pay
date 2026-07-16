"""Storage adapters."""

from abc import ABC, abstractmethod


class Store(ABC):
    name: str

    @abstractmethod
    def put_transaction(self, tx: dict) -> None: ...
    @abstractmethod
    def put_certificate(self, cert: dict) -> None: ...
    @abstractmethod
    def set_station_state(self, state: dict) -> None: ...
    @abstractmethod
    def get_station_state(self) -> dict | None: ...
    @abstractmethod
    def get_transaction(self, tx_id: str) -> dict | None: ...
    @abstractmethod
    def get_certificate(self, cert_id: str) -> dict | None: ...
    @abstractmethod
    def list_recent_transactions(self, n: int = 25) -> list[dict]: ...
    @abstractmethod
    def set_feedback(self, station_id: str, tone: str) -> None: ...
    @abstractmethod
    def pop_feedback(self, station_id: str) -> str: ...


class InMemoryStore(Store):
    name = "memory"

    def __init__(self) -> None:
        self._transactions: dict[str, dict] = {}
        self._certificates: dict[str, dict] = {}
        self._station_state: dict | None = None
        self._feedback: dict[str, str] = {}

    def put_transaction(self, tx: dict) -> None:
        self._transactions[tx["txId"]] = tx

    def put_certificate(self, cert: dict) -> None:
        self._certificates[cert["certId"]] = cert

    def set_station_state(self, state: dict) -> None:
        self._station_state = state

    def get_station_state(self) -> dict | None:
        return self._station_state

    def get_transaction(self, tx_id: str) -> dict | None:
        return self._transactions.get(tx_id)

    def get_certificate(self, cert_id: str) -> dict | None:
        return self._certificates.get(cert_id)

    def list_recent_transactions(self, n: int = 25) -> list[dict]:
        return list(reversed(self._transactions.values()))[:n]

    def set_feedback(self, station_id: str, tone: str) -> None:
        self._feedback[station_id] = tone

    def pop_feedback(self, station_id: str) -> str:
        return self._feedback.pop(station_id, "none")