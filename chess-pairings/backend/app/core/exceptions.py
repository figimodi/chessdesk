from dataclasses import dataclass


class PairingEngineError(Exception):
    pass


@dataclass
class ApiErrorPayload:
    code: str
    message: str
