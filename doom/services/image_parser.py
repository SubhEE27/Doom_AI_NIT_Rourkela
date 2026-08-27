
from __future__ import annotations

from pathlib import Path
from typing import Dict

from PySide6.QtGui import QImageReader

from doom.services.vision_analysis import (
    GeminiVisionAnalysisService,
    ImageAnalysisResult,
)


class ImageParser:
    """
    Image ingestion + optional multimodal analysis.

    Metadata parsing is always local.

    AI analysis is optional and is performed only when
    a Gemini API key is configured.
    """

    SUPPORTED_FORMATS = {
        "PNG",
        "JPG",
        "JPEG",
        "BMP",
        "WEBP",
        "DICOM",
    }

    def __init__(
        self,
        vision_service: GeminiVisionAnalysisService | None = None,
    ) -> None:

        self.vision_service = (
            vision_service
        )

    # ========================================================
    # BASIC IMAGE METADATA
    # ========================================================

    def parse(
        self,
        path: str,
    ) -> Dict:

        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Image file does not exist: {path}"
            )

        reader = QImageReader(
            str(file_path)
        )

        readable = reader.canRead()

        size = reader.size()

        raw_format = bytes(
            reader.format()
        ).decode(
            errors="ignore"
        ).upper()

        if not raw_format:

            raw_format = (
                file_path.suffix
                .replace(".", "")
                .upper()
            )

        return {
            "filename":
                file_path.name,

            "format":
                raw_format,

            "width":
                max(
                    size.width(),
                    0,
                ),

            "height":
                max(
                    size.height(),
                    0,
                ),

            "size_kb":
                round(
                    file_path.stat().st_size
                    / 1024,
                    1,
                ),

            "readable":
                readable,

            "supported":
                (
                    raw_format
                    in self.SUPPORTED_FORMATS
                ),

            "clinical_interpretation":
                (
                    "NOT PERFORMED BY METADATA "
                    "PARSER"
                ),
        }

    # ========================================================
    # AI IMAGE ANALYSIS
    # ========================================================

    def analyze(
        self,
        path: str,
    ) -> ImageAnalysisResult:

        if self.vision_service is None:
            raise RuntimeError(
                "Vision analysis is not configured. "
                "Configure GeminiVisionAnalysisService "
                "before calling analyze()."
            )

        metadata = self.parse(
            path
        )

        if not metadata["readable"]:
            raise ValueError(
                "Image cannot be read."
            )

        if not metadata["supported"]:
            raise ValueError(
                "Image format is not supported."
            )

        return self.vision_service.analyze(
            path
        )

    # ========================================================
    # FORMAT FINDINGS FOR UI
    # ========================================================

    def format_findings(
        self,
        result: ImageAnalysisResult,
    ) -> str:

        return (
            self.vision_service
            .format_for_clinician(
                result
            )
            if self.vision_service is not None
            else ""
        )
