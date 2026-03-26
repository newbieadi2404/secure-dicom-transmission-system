#!/usr/bin/env python3
"""
Security Metrics for Medical Image Encryption Evaluation.
"""

import time
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any
from scipy.stats import pearsonr
import hashlib

from secure_med_trans.utils.logger import get_logger
from secure_med_trans.security.security_visualization import generate_full_report

logger = get_logger(__name__)


class SecurityMetrics:
    """
    Encryption strength evaluation metrics for IEE paper and system analysis.
    Supports uint8 and uint16 images.
    """

    # ---------------------------------------------------
    # Shannon Entropy
    # ---------------------------------------------------
    @staticmethod
    def calculate_entropy(image: np.ndarray) -> float:
        """
        Calculates the Shannon entropy of an image.
        Supports uint8 and uint16.
        """
        if image.dtype == np.uint8:
            bins = 256
            range_val = (0, 256)
        elif image.dtype == np.uint16:
            bins = 65536
            range_val = (0, 65536)
        else:
            # Fallback for other dtypes
            unique, counts = np.unique(image, return_counts=True)
            probabilities = counts / counts.sum()
            return -np.sum(probabilities * np.log2(probabilities))

        hist, _ = np.histogram(image.flatten(), bins=bins, range=range_val)
        hist = hist.astype(float)
        hist /= np.sum(hist)
        hist = hist[hist > 0]
        entropy = -np.sum(hist * np.log2(hist))
        return float(entropy)

    # ---------------------------------------------------
    # NPCR (Number of Pixels Change Rate)
    # ---------------------------------------------------
    @staticmethod
    def calculate_npcr(original: np.ndarray, encrypted: np.ndarray) -> float:
        """
        Number of Pixels Change Rate (NPCR).
        """
        if original.shape != encrypted.shape:
            # Attempt to reshape encrypted if it's flat
            if encrypted.ndim == 1:
                encrypted = SecurityMetrics.reshape_to_match(encrypted, original.shape, original.dtype)
            else:
                raise ValueError(f"Shape mismatch: {original.shape} vs {encrypted.shape}")

        diff = (original != encrypted).astype(int)
        npcr = (np.sum(diff) / original.size) * 100
        return float(npcr)

    # ---------------------------------------------------
    # UACI (Unified Average Changing Intensity)
    # ---------------------------------------------------
    @staticmethod
    def calculate_uaci(original: np.ndarray, encrypted: np.ndarray) -> float:
        """
        Unified Average Changing Intensity (UACI).
        """
        if original.shape != encrypted.shape:
            if encrypted.ndim == 1:
                encrypted = SecurityMetrics.reshape_to_match(encrypted, original.shape, original.dtype)
            else:
                raise ValueError(f"Shape mismatch: {original.shape} vs {encrypted.shape}")

        if original.dtype == np.uint8:
            max_val = 255.0
        elif original.dtype == np.uint16:
            max_val = 65535.0
        else:
            max_val = float(np.iinfo(original.dtype).max)

        diff = np.abs(original.astype(np.float32) - encrypted.astype(np.float32))
        uaci = (np.sum(diff) / (original.size * max_val)) * 100
        return float(uaci)

    # ---------------------------------------------------
    # Correlation Coefficient
    # ---------------------------------------------------
    @staticmethod
    def calculate_correlation(original: np.ndarray, encrypted: np.ndarray) -> float:
        """
        Calculates the Pearson correlation coefficient between two images.
        """
        if original.shape != encrypted.shape:
            if encrypted.ndim == 1:
                encrypted = SecurityMetrics.reshape_to_match(encrypted, original.shape, original.dtype)
            else:
                # Flat versions for correlation
                x = original.flatten().astype(float)
                y = encrypted.flatten().astype(float)
                # Pad/truncate y to match x
                if y.size > x.size:
                    y = y[:x.size]
                elif y.size < x.size:
                    y = np.pad(y, (0, x.size - y.size), 'constant')
                corr, _ = pearsonr(x, y)
                if not isinstance(corr, float):
                    return 0.0
                return float(corr)

        corr, _ = pearsonr(original.flatten().astype(float), encrypted.flatten().astype(float))
        if not isinstance(corr, float):
            return 0.0
        return float(corr)

    # ---------------------------------------------------
    # Reshaping Utility
    # ---------------------------------------------------
    @staticmethod
    def reshape_to_match(data: np.ndarray, target_shape: tuple, target_dtype: np.dtype) -> np.ndarray:
        """
        Reshapes a flat array to match a target shape and dtype.
        Pads or truncates as necessary.
        """
        expected_size = np.prod(target_shape)
        
        # If the input is bytes/uint8 (e.g. from ciphertext), convert to the target dtype
        if data.dtype != target_dtype:
            # We treat data as bytes and convert to target_dtype
            raw_bytes = data.tobytes()
            data = np.frombuffer(raw_bytes, dtype=target_dtype)

        if data.size > expected_size:
            data = data[:expected_size]
        elif data.size < expected_size:
            data = np.pad(data, (0, int(expected_size - data.size)), 'constant')
            
        return data.reshape(target_shape)

    # ---------------------------------------------------
    # PSNR
    # ---------------------------------------------------
    @staticmethod
    def calculate_psnr(original: np.ndarray, encrypted: np.ndarray) -> float:
        """
        Peak Signal-to-Noise Ratio.
        """
        if original.shape != encrypted.shape:
            encrypted = SecurityMetrics.reshape_to_match(encrypted, original.shape, original.dtype)

        mse = np.mean((original.astype(np.float32) - encrypted.astype(np.float32)) ** 2)

        if mse == 0:
            return float("inf")

        max_pixel = 255.0 if original.dtype == np.uint8 else 65535.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))

        return float(psnr)

    # ---------------------------------------------------
    # Whirlpool Entropy
    # ---------------------------------------------------
    @staticmethod
    def whirlpool_entropy(data: bytes) -> float:
        """
        Whirlpool entropy for data integrity verification.
        """
        w_hash = hashlib.new("whirlpool", data).digest()

        hist, _ = np.histogram(
            np.frombuffer(w_hash, dtype=np.uint8),
            bins=256,
            range=(0, 256)
        )

        hist = hist.astype(float)
        hist /= hist.sum()
        hist = hist[hist > 0]

        entropy = -np.sum(hist * np.log2(hist))

        return float(entropy)

    # ---------------------------------------------------
    # Performance Measurement
    # ---------------------------------------------------
    @staticmethod
    def measure_time(func, *args, **kwargs) -> Tuple[float, Any]:
        """
        Measure execution time of a function in milliseconds.
        """
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        return elapsed_ms, result

    # ---------------------------------------------------
    # Comprehensive Analysis
    # ---------------------------------------------------
    @staticmethod
    def comprehensive_analysis(original_image: np.ndarray,
                               encrypted_data: bytes,
                               save_plots: bool = True) -> Dict[str, Any]:
        """
        Conducts a full security analysis comparing the original image with its encrypted counterpart.
        """
        # View encrypted data as original shape/dtype for metric calculation
        encrypted_image = SecurityMetrics.reshape_to_match(
            np.frombuffer(encrypted_data, dtype=np.uint8),
            original_image.shape,
            original_image.dtype
        )

        metrics = {
            "entropy_original": SecurityMetrics.calculate_entropy(original_image),
            "entropy_encrypted": SecurityMetrics.calculate_entropy(encrypted_image),
            "npcr": SecurityMetrics.calculate_npcr(original_image, encrypted_image),
            "uaci": SecurityMetrics.calculate_uaci(original_image, encrypted_image),
            "correlation": SecurityMetrics.calculate_correlation(original_image, encrypted_image),
            "psnr": SecurityMetrics.calculate_psnr(original_image, encrypted_image),
            "whirlpool_entropy": SecurityMetrics.whirlpool_entropy(original_image.tobytes())
        }

        if save_plots:
            reports_dir = Path("output/security_reports")
            reports_dir.mkdir(exist_ok=True)
            try:
                generate_full_report(
                    original_image, 
                    encrypted_image, 
                    reports_dir,
                    npcr=metrics["npcr"],
                    uaci=metrics["uaci"]
                )
            except Exception as e:
                logger.warning(f"Report generation failed: {e}")

        # 🔥 LOGGING OUTPUT
        SecurityMetrics.log_metrics(metrics)

        return metrics

    @staticmethod
    def log_metrics(metrics: Dict[str, Any]):
        """
        Log metrics clearly for debugging and paper reporting.
        """
        logger.info("=" * 60)
        logger.info("🛡️  ENCRYPTION EVALUATION METRICS (IEE Paper Standards)")
        logger.info("-" * 60)
        logger.info(f"Entropy (Encrypted): {metrics.get('entropy_encrypted', 0):.6f}")
        logger.info(f"NPCR:                {metrics.get('npcr', 0):.6f}%")
        logger.info(f"UACI:                {metrics.get('uaci', 0):.6f}%")
        logger.info(f"Correlation:         {metrics.get('correlation', 0):.6f}")
        logger.info(f"PSNR:                {metrics.get('psnr', 0):.4f}dB")
        logger.info("-" * 60)
        logger.info("Good Values Checklist:")
        logger.info("- Entropy: Close to 8.0 (8-bit) or 16.0 (16-bit)")
        logger.info("- NPCR:    Close to 99.6% (8-bit)")
        logger.info("- UACI:    Close to 33.4% (8-bit)")
        logger.info("- Correlation: Close to 0.0")
        logger.info("=" * 60)

    # ---------------------------------------------------
    # Pretty Report
    # ---------------------------------------------------
    @staticmethod
    def print_security_report(metrics: Dict[str, Any]):

        print("\n" + "=" * 60)
        print("🔐 ENCRYPTION SECURITY REPORT")
        print("=" * 60)

        print(f"📊 Entropy (Encrypted):     {metrics['entropy_encrypted']:.3f} bits")
        print(f"📊 PSNR:                   {metrics['psnr_db']:.2f} dB")

        print("\n--- Original Image Correlation ---")
        print(f"H: {metrics['correlation']['original_horizontal']:.4f}")
        print(f"V: {metrics['correlation']['original_vertical']:.4f}")

        print("\n--- Encrypted Image Correlation ---")
        print(f"H: {metrics['correlation']['encrypted_horizontal']:.4f}")
        print(f"V: {metrics['correlation']['encrypted_vertical']:.4f}")

        print(f"\n📈 Correlation (Overall):  {metrics['correlation']['overall']:.4f}")

        print(f"\n🌪️  Whirlpool Entropy:     {metrics['whirlpool_entropy']:.3f}")

        status = "✅ EXCELLENT" if metrics["entropy_encrypted"] > 7.5 else "⚠️ REVIEW"

        print(f"\n{status} encryption quality!")

        print("=" * 60)