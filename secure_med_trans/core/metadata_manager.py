"""
Metadata Manager for Secure Medical Transmission System.

Handles:
- Attribute classification (protected/public/required)
- Policy-based transformation
- Structured output for encryption layer
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
from copy import deepcopy

from pydicom.dataset import Dataset, FileMetaDataset

from secure_med_trans.utils.logger import get_logger

logger = get_logger(__name__)


# -----------------------------
# 🔐 ENUMS
# -----------------------------

class ProtectionLevel(Enum):
    ENCRYPTED = "encrypted"
    HASHED = "hashed"
    PUBLIC = "public"
    REMOVED = "removed"


# -----------------------------
# 🔐 DATA CLASS
# -----------------------------

@dataclass
class MetadataTransformation:
    original_value: Any
    transformed_value: Any
    transformation_type: str
    timestamp: str


# -----------------------------
# 🔐 MAIN CLASS
# -----------------------------

class MetadataManager:

    DEFAULT_PROTECTED: Set[str] = {
        "PatientName", "PatientID", "PatientBirthDate", "PatientSex",
        "PatientAge", "PatientWeight", "PatientAddress",
        "PatientTelephoneNumbers", "PatientInsurancePlanCodeSequence",
        "StudyDate", "StudyTime", "AccessionNumber",
        "ReferringPhysicianName", "ReferringPhysicianAddress",
        "ReferringPhysicianTelephoneNumbers", "InstitutionName",
        "InstitutionAddress", "PhysiciansOfRecord",
        "PerformingPhysicianName", "OperatorsName",
        "AdmittingDiagnosesDescription", "MedicalRecordLocator",
    }

    DEFAULT_PUBLIC: Set[str] = {
        "Modality", "Rows", "Columns", "BitsAllocated",
        "BitsStored", "HighBit", "PhotometricInterpretation",
        "SamplesPerPixel", "PixelRepresentation",
        "PlanarConfiguration", "RescaleIntercept",
        "RescaleSlope", "ImageType", "SOPClassUID",
        "SOPInstanceUID", "StudyInstanceUID",
        "SeriesInstanceUID", "StudyID", "SeriesNumber",
        "InstanceNumber",
    }

    REQUIRED_ATTRIBUTES: Set[str] = {
        "SOPClassUID", "SOPInstanceUID", "Rows", "Columns",
    }

    def __init__(self):
        self._protected_attributes = deepcopy(self.DEFAULT_PROTECTED)
        self._public_attributes = deepcopy(self.DEFAULT_PUBLIC)
        self._transformation_history: List[MetadataTransformation] = []

    # -----------------------------
    # 🔹 ATTRIBUTE SELECTION
    # -----------------------------

    def select_protected_attributes(
        self,
        dataset: Dataset,
        custom_list: Optional[List[str]] = None,
    ) -> Dict[str, str]:

        attrs = custom_list if custom_list else self._protected_attributes
        protected = {}

        for attr in attrs:
            if hasattr(dataset, attr):
                value = getattr(dataset, attr)
                if value is not None:
                    protected[attr] = self._serialize(value)

        return protected

    def select_public_attributes(
        self,
        dataset: Dataset,
        custom_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:

        attrs = custom_list if custom_list else self._public_attributes
        public = {}

        for attr in attrs:
            if hasattr(dataset, attr):
                value = getattr(dataset, attr)
                if value is not None:
                    public[attr] = value

        return public

    def get_required_attributes(self, dataset: Dataset) -> Dict[str, Any]:
        required = {}

        for attr in self.REQUIRED_ATTRIBUTES:
            if hasattr(dataset, attr):
                value = getattr(dataset, attr)
                if value is not None:
                    required[attr] = value

        return required

    # -----------------------------
    # 🔐 POLICY APPLICATION
    # -----------------------------

    def apply_protection_policy(
        self,
        dataset: Dataset,
        policy: Dict[str, ProtectionLevel],
    ) -> Dict[str, Any]:

        result = {}

        for attr, level in policy.items():
            if not hasattr(dataset, attr):
                continue

            value = getattr(dataset, attr)
            if value is None:
                continue

            serialized = self._serialize(value)

            if level == ProtectionLevel.REMOVED:
                self._record(attr, value, None, "removed")
                continue

            elif level == ProtectionLevel.ENCRYPTED:
                result[attr] = {
                    "type": "encrypted",
                    "algorithm": "AES-256-GCM",   # placeholder
                    "value": serialized
                }

            elif level == ProtectionLevel.HASHED:
                result[attr] = {
                    "type": "hash",
                    "algorithm": "SHA-256",
                    "value": self._hash(serialized)
                }

            elif level == ProtectionLevel.PUBLIC:
                result[attr] = {
                    "type": "public",
                    "value": value
                }

            self._record(attr, value, result.get(attr), level.value)

        return result

    # -----------------------------
    # 🔐 MERGE + RECONSTRUCTION
    # -----------------------------

    def merge_attributes(
        self,
        protected: Dict[str, Any],
        public: Dict[str, Any],
        required: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        merged = {}

        merged.update(public)
        merged.update(protected)

        if required:
            merged.update(required)

        for attr in self.REQUIRED_ATTRIBUTES:
            if attr not in merged:
                logger.warning(f"Missing required attribute: {attr}")

        return merged

    def reconstruct_dataset(
        self,
        protected: Dict[str, Any],
        public: Dict[str, Any],
        required: Optional[Dict[str, Any]] = None,
        file_meta: Optional[FileMetaDataset] = None,
    ) -> Dataset:

        ds = Dataset()

        if file_meta:
            ds.file_meta = file_meta

        merged = self.merge_attributes(protected, public, required)

        for attr, wrapper in merged.items():
            try:
                # unwrap structured values
                if isinstance(wrapper, dict) and "value" in wrapper:
                    setattr(ds, attr, wrapper["value"])
                else:
                    setattr(ds, attr, wrapper)
            except Exception as e:
                logger.warning(f"Failed to set {attr}: {e}")

        return ds

    # -----------------------------
    # 🔐 JSON
    # -----------------------------

    def export_metadata_json(
        self,
        protected: Dict[str, Any],
        public: Dict[str, Any],
    ) -> str:

        return json.dumps({
            "protected": protected,
            "public": public,
        })

    def import_metadata_json(self, json_str: str):
        data = json.loads(json_str)
        return data.get("protected", {}), data.get("public", {})

    # -----------------------------
    # 🔐 HELPERS
    # -----------------------------

    def _serialize(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return ",".join(map(str, value))
        elif hasattr(value, "value"):
            return str(value.value)
        return str(value)

    def _hash(self, value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def _record(self, attr, original, transformed, ttype):
        from datetime import datetime

        self._transformation_history.append(
            MetadataTransformation(
                original_value=original,
                transformed_value=transformed,
                transformation_type=ttype,
                timestamp=datetime.utcnow().isoformat(),
            )
        )

    def get_transformation_history(self):
        return self._transformation_history.copy()

    def clear_history(self):
        self._transformation_history.clear()