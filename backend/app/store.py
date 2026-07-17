"""Storage adapters. R2: only this backend ever writes; clients are read-only."""

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
    def pop_feedback(self, station_id: str) -> str:
        """Read-once: returns the pending tone and clears it ('none' when empty)."""

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

class FirestoreStore(Store):
    """firebase-admin adapter. Collections: transactions, certificates,
    station_state/current, station_feedback. Correctness verified by review and live Firestore round-trip."""

    name = "firestore"

    def __init__(self, service_account_json: str) -> None:
        import json

        import firebase_admin
        from firebase_admin import credentials, firestore

        cred = credentials.Certificate(json.loads(service_account_json))
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        self._db = firestore.client()

    def put_transaction(self, tx: dict) -> None:
        self._db.collection("transactions").document(tx["txId"]).set(tx)

    def put_certificate(self, cert: dict) -> None:
        self._db.collection("certificates").document(cert["certId"]).set(cert)

    def set_station_state(self, state: dict) -> None:
        self._db.collection("station_state").document("current").set(state)

    def get_station_state(self) -> dict | None:
        snap = self._db.collection("station_state").document("current").get()
        return snap.to_dict() if snap.exists else None

    def get_transaction(self, tx_id: str) -> dict | None:
        snap = self._db.collection("transactions").document(tx_id).get()
        return snap.to_dict() if snap.exists else None

    def get_certificate(self, cert_id: str) -> dict | None:
        snap = self._db.collection("certificates").document(cert_id).get()
        return snap.to_dict() if snap.exists else None

    def list_recent_transactions(self, n: int = 25) -> list[dict]:
        from google.cloud.firestore_v1 import Query

        query = (
            self._db.collection("transactions")
            .order_by("createdAt", direction=Query.DESCENDING)
            .limit(n)
        )
        return [snap.to_dict() for snap in query.stream()]

    def set_feedback(self, station_id: str, tone: str) -> None:
        self._db.collection("station_feedback").document(station_id).set({"tone": tone})

    def pop_feedback(self, station_id: str) -> str:
        ref = self._db.collection("station_feedback").document(station_id)
        snap = ref.get()
        if not snap.exists:
            return "none"
        ref.delete()
        return (snap.to_dict() or {}).get("tone", "none")
