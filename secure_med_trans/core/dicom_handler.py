"""
Robust DICOM Handler for Secure Medical Transmission System.

Handles:
- Safe loading
- Pixel extraction
- Metadata preservation
- Standards-compliant reconstruction
"""

from pathlib import Path
from typing import Dict, Any, Union
import numpy as np
from pydicom import dcmread, dcmwrite
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from secure_med_trans.utils.logger import get_logger
from secure_med_trans.utils.exceptions import DICOMHandlerException

logger = get_logger(__name__)


class DICOMHandler:

    # -----------------------------
    # 🔹 LOAD
    # -----------------------------
    def load_dicom(self, file_path: Union[str, Path]) -> Dataset:
        path = Path(file_path)

        if not path.exists():
            raise DICOMHandlerException(f"File not found: {path}")

        try:
            ds = dcmread(path)
        except Exception as e:
            raise DICOMHandlerException(f"Invalid DICOM file: {e}")

        logger.info(f"Loaded DICOM: {path.name}")
        return ds

    # -----------------------------
    # 🔹 PIXEL DATA
    # -----------------------------
    def extract_pixel_data(self, dicom: Dataset) -> np.ndarray:
        if not hasattr(dicom, "pixel_array"):
            raise DICOMHandlerException("No pixel data found")

        return dicom.pixel_array

    # -----------------------------
    # 🔹 HEADER EXTRACTION
    # -----------------------------
    def extract_header(self, dicom: Dataset) -> Dict[str, Any]:
        """
        Extract critical metadata required for reconstruction.
        """

        header = {}

        # 🔥 Preserve essential attributes
        important_fields = [
            # Patient info
            "PatientName", "PatientID", "PatientBirthDate", "PatientSex",

            # Study/Series
            "StudyInstanceUID", "SeriesInstanceUID", "StudyID",
            "SeriesNumber", "InstanceNumber",

            # Image identity
            "SOPClassUID", "SOPInstanceUID",

            # Image properties
            "Modality", "Rows", "Columns",
            "BitsAllocated", "BitsStored", "HighBit",
            "SamplesPerPixel", "PhotometricInterpretation",
            "PixelRepresentation",

            # Spatial info (IMPORTANT)
            "PixelSpacing",
            "ImagePositionPatient",
            "ImageOrientationPatient",
        ]

        for attr in important_fields:
            if hasattr(dicom, attr):
                value = getattr(dicom, attr)
                if value is not None:
                    header[attr] = value

        return header

    # -----------------------------
    # 🔹 RECONSTRUCTION
    # -----------------------------
    def reconstruct_dicom(
        self,
        header: Dict[str, Any],
        pixel_data: np.ndarray
    ) -> Dataset:

        if pixel_data.size == 0:
            raise DICOMHandlerException("Empty pixel data")

        ds = Dataset()

        # Restore metadata
        for key, value in header.items():
            setattr(ds, key, value)

        # Dimensions
        ds.Rows = header.get("Rows", pixel_data.shape[-2])
        ds.Columns = header.get("Columns", pixel_data.shape[-1])

        # Multi-frame support
        if pixel_data.ndim == 3:
            ds.NumberOfFrames = pixel_data.shape[0]

        # Pixel format
        if pixel_data.dtype == np.uint16:
            ds.BitsAllocated = 16
            ds.BitsStored = 16
            ds.HighBit = 15
        elif pixel_data.dtype == np.uint8:
            ds.BitsAllocated = 8
            ds.BitsStored = 8
            ds.HighBit = 7
        else:
            raise DICOMHandlerException(f"Unsupported dtype: {pixel_data.dtype}")

        ds.PixelRepresentation = 0

        # Safe defaults if missing
        if not hasattr(ds, "SamplesPerPixel"):
            ds.SamplesPerPixel = 1

        if not hasattr(ds, "PhotometricInterpretation"):
            ds.PhotometricInterpretation = "MONOCHROME2"

        # 🔥 Critical: assign pixel data
        ds.PixelData = pixel_data.tobytes()

        # -----------------------------
        # 🔹 FILE META (MANDATORY)
        # -----------------------------
        file_meta = FileMetaDataset()

        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        file_meta.MediaStorageSOPClassUID = getattr(
            ds, "SOPClassUID", generate_uid()
        )
        file_meta.MediaStorageSOPInstanceUID = getattr(
            ds, "SOPInstanceUID", generate_uid()
        )
        file_meta.ImplementationClassUID = generate_uid()

        ds.file_meta = file_meta

        ds.is_little_endian = True
        ds.is_implicit_VR = False

        logger.info("DICOM reconstructed successfully")

        return ds

    # -----------------------------
    # 🔹 SAVE
    # -----------------------------
    def save_dicom(
        self,
        file_path: Union[str, Path],
        dicom: Dataset
    ) -> bool:

        try:
            dcmwrite(str(file_path), dicom, write_like_original=False)
            logger.info(f"Saved DICOM: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Save failed: {e}")
            return False