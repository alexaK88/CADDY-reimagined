from __future__ import annotations

from pathlib import Path
from typing import TextIO

from logger import get_logger
from ..schemas import RawWearablePacket


logger = get_logger(__name__)


class PacketLogger:
    """
    Writes generated RawWearablePacket objects to a JSONL file.

    JSONL means:
    - one JSON object per line
    - easy to append
    - easy to replay later
    - easy to inspect manually
    """

    def __init__(self, output_path: str | Path):
        self.output_path = Path(output_path)
        self._file: TextIO | None = None

    def __enter__(self) -> "PacketLogger":
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.output_path.open("w", encoding="utf-8")
        logger.info("Packet logger opened: %s", self.output_path)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._file is not None:
            self._file.close()
            logger.info("Packet logger closed: %s", self.output_path)

    def write(self, packet: RawWearablePacket) -> None:
        if self._file is None:
            raise RuntimeError("PacketLogger is not open. Use it with a context manager.")

        self._file.write(packet.model_dump_json() + "\n")
        self._file.flush()
