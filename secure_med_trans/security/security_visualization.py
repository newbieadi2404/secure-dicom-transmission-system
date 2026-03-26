#!/usr/bin/env python3
"""
Security Visualization for SecureMedTrans.
Generates encryption analysis graphs.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# -----------------------------
# Image Normalization (IMPORTANT for DICOM)
# -----------------------------
def normalize_image(img: np.ndarray) -> np.ndarray:
    img = img.astype(np.float32)
    img = (img - img.min()) / (img.max() - img.min() + 1e-12)
    img = (img * 255).astype(np.uint8)
    return img


# -----------------------------
# Histogram Comparison
# -----------------------------
def generate_histogram_comparison(original_pixels: np.ndarray,
                                  encrypted_pixels: np.ndarray,
                                  output_dir: Path):

    original_pixels = normalize_image(original_pixels)
    encrypted_pixels = normalize_image(encrypted_pixels)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.hist(original_pixels.flatten(), bins=256, density=True,
             alpha=0.7, color='blue')
    ax1.set_title('Original Image Histogram')
    ax1.set_xlabel('Pixel Intensity')
    ax1.set_ylabel('Density')

    ax2.hist(encrypted_pixels.flatten(), bins=256, density=True,
             alpha=0.7, color='red')
    ax2.set_title('Encrypted Image Histogram')
    ax2.set_xlabel('Pixel Intensity')
    ax2.set_ylabel('Density')

    plt.tight_layout()

    plt.savefig(output_dir / 'histogram_comparison.png',
                dpi=300, bbox_inches='tight')
    plt.close()


# -----------------------------
# Adjacent Pixel Correlation
# -----------------------------
def plot_pixel_correlation(image_pixels: np.ndarray,
                           title: str,
                           output_dir: Path):

    image_pixels = normalize_image(image_pixels)

    # Horizontal neighbors
    x_h = image_pixels[:, :-1].flatten()
    y_h = image_pixels[:, 1:].flatten()

    # Vertical neighbors
    x_v = image_pixels[:-1, :].flatten()
    y_v = image_pixels[1:, :].flatten()

    corr_h = np.corrcoef(x_h, y_h)[0, 1]
    corr_v = np.corrcoef(x_v, y_v)[0, 1]

    # Random sampling for scatter
    sample_size = min(5000, len(x_h))
    idx = np.random.choice(len(x_h), sample_size, replace=False)

    x_sample = x_h[idx]
    y_sample = y_h[idx]

    plt.figure(figsize=(8, 8))

    plt.scatter(x_sample, y_sample,
                s=3,
                alpha=0.4)

    # Perfect correlation reference
    plt.plot([0, 255], [0, 255],
             'r--',
             label="Perfect Correlation")

    plt.title(f'{title} Adjacent Pixel Correlation\n'
              f'(H: {corr_h:.4f}, V: {corr_v:.4f})')

    plt.xlabel('Pixel n')
    plt.ylabel('Pixel n+1')

    plt.grid(True, alpha=0.3)
    plt.legend()

    filename = f'correlation_{title.lower().replace(" ", "_")}.png'

    plt.savefig(output_dir / filename,
                dpi=300,
                bbox_inches='tight')

    plt.close()


# -----------------------------
# Local Entropy Heatmap
# -----------------------------
def plot_entropy_distribution(image_pixels: np.ndarray,
                              output_dir: Path):

    image_pixels = normalize_image(image_pixels)

    h, w = image_pixels.shape
    radius = 4   # 9x9 window
    step = 8     # Optimization: compute every 8th pixel to avoid hang

    # Adjust output dimensions for step
    out_h = (h - 2 * radius) // step
    out_w = (w - 2 * radius) // step
    entropies = np.zeros((out_h, out_w))

    for i_idx, i in enumerate(range(radius, h - radius, step)):
        for j_idx, j in enumerate(range(radius, w - radius, step)):
            if i_idx >= out_h or j_idx >= out_w: continue

            window = image_pixels[
                i - radius:i + radius + 1,
                j - radius:j + radius + 1
            ].flatten()

            hist, _ = np.histogram(window,
                                   bins=256,
                                   range=(0, 255))

            prob = hist / np.sum(hist)
            prob = prob[prob > 0]

            entropy_val = -np.sum(prob * np.log2(prob))

            entropies[i_idx, j_idx] = entropy_val

    plt.figure(figsize=(10, 8))

    plt.imshow(entropies,
               cmap='hot',
               interpolation='nearest')

    plt.colorbar(label='Local Entropy')

    plt.title('Local Entropy Heatmap (9x9 sliding window)')
    plt.axis('off')

    plt.savefig(output_dir / 'entropy_heatmap.png',
                dpi=300,
                bbox_inches='tight')

    plt.close()


# -----------------------------
# NPCR + UACI Graph
# -----------------------------
def plot_npcr_uaci(npcr: float,
                   uaci: float,
                   output_dir: Path):

    plt.figure(figsize=(6, 4))

    plt.bar(["NPCR (%)", "UACI (%)"],
            [npcr, uaci],
            color=['green', 'orange'])

    plt.title('NPCR and UACI Analysis')
    plt.ylabel('Percentage (%)')

    plt.ylim(0, 110)

    plt.savefig(output_dir / 'npcr_uaci_report.png',
                dpi=300,
                bbox_inches='tight')

    plt.close()


# -----------------------------
# Full Security Report
# -----------------------------
def generate_full_report(original_pixels: np.ndarray,
                         encrypted_pixels: np.ndarray,
                         output_dir: Path,
                         npcr: float = None,
                         uaci: float = None):

    output_dir.mkdir(exist_ok=True)

    generate_histogram_comparison(
        original_pixels,
        encrypted_pixels,
        output_dir
    )

    plot_pixel_correlation(
        original_pixels,
        "Original Image",
        output_dir
    )

    plot_pixel_correlation(
        encrypted_pixels,
        "Encrypted Image",
        output_dir
    )

    plot_entropy_distribution(
        encrypted_pixels,
        output_dir
    )

    if npcr is not None and uaci is not None:
        plot_npcr_uaci(
            npcr,
            uaci,
            output_dir
        )

    print("Encryption Security Report Generated")
    print("Graphs saved to output/security_reports/")