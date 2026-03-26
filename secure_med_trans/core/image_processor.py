"""
Image Processor for Secure Medical Transmission System.

Handles ONLY:
- Lossless serialization (numpy → bytes)
- Safe reconstruction (bytes → numpy)
- Basic integrity validation

No image modification is performed.
"""

from typing import Dict, Any, Optional
import numpy as np

from secure_med_trans.utils.logger import get_logger

logger = get_logger(__name__)


class ImageProcessor:

    def __init__(self):
        self._current_image: Optional[np.ndarray] = None

    # -----------------------------
    # 🔹 LOAD METHODS
    # -----------------------------

    def load_from_array(self, image_array: np.ndarray) -> np.ndarray:
        self._validate(image_array)
        self._current_image = image_array
        return image_array

    def load_from_payload(self, payload: Dict[str, Any]) -> np.ndarray:
        image = self.from_bytes(payload)
        self._current_image = image
        return image

    # -----------------------------
    # 🔹 SERIALIZATION
    # -----------------------------

    def to_bytes(self, image_array: np.ndarray) -> Dict[str, Any]:
        """
        Convert numpy array into transport-safe payload.
        """
        self._validate(image_array)

        raw_bytes = image_array.tobytes()

        payload = {
            "data": raw_bytes,
            "shape": list(image_array.shape),   # JSON-safe
            "dtype": image_array.dtype.name,    # stable dtype
            "size": len(raw_bytes),             # integrity check
        }

        logger.debug("Image serialized")
        return payload

    def from_bytes(self, payload: Dict[str, Any]) -> np.ndarray:
        """
        Reconstruct numpy array from payload safely.
        """

        # 🔹 Required keys
        required = ["data", "shape", "dtype", "size"]
        for key in required:
            if key not in payload:
                raise ValueError(f"Missing key in payload: {key}")

        data = payload["data"]
        shape = tuple(payload["shape"])
        dtype = np.dtype(payload["dtype"])
        expected_size = payload["size"]

        # 🔹 Integrity check (basic)
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("Invalid data type in payload")

        if len(data) != expected_size:
            raise ValueError("Data size mismatch (possible corruption)")

        # 🔹 Reconstruct array
        array = np.frombuffer(data, dtype=dtype)

        expected_elements = int(np.prod(shape))
        if array.size != expected_elements:
            raise ValueError("Shape mismatch with data")

        try:
            array = array.reshape(shape)
        except Exception as e:
            raise ValueError(f"Reshape failed: {e}")

        logger.debug("Image reconstructed")
        return array

    # -----------------------------
    # 🔹 VALIDATION
    # -----------------------------

    def _validate(self, image_array: np.ndarray) -> None:
        if not isinstance(image_array, np.ndarray):
            raise ValueError("Input must be numpy array")

        if image_array.size == 0:
            raise ValueError("Empty image array")

        if not image_array.flags['C_CONTIGUOUS']:
            # 🔥 Ensure consistent memory layout
            image_array = np.ascontiguousarray(image_array)

        if image_array.dtype not in (np.uint8, np.uint16, np.int16, np.float32):
            logger.warning(f"Uncommon dtype detected: {image_array.dtype}")

    # -----------------------------
    # 🔹 DEBUG INFO
    # -----------------------------

    def get_image_info(self, image_array: np.ndarray) -> Dict[str, Any]:
        self._validate(image_array)

        return {
            "shape": image_array.shape,
            "dtype": image_array.dtype.name,
            "min": float(image_array.min()),
            "max": float(image_array.max()),
            "mean": float(image_array.mean()),
            "size": image_array.size,
        }

    # -----------------------------
    # 🔹 PROPERTY
    # -----------------------------

    @property
    def current_image(self) -> Optional[np.ndarray]:
        return self._current_image