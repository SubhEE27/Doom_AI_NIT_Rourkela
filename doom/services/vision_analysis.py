from __future__ import annotations

import json
import mimetypes
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types


@dataclass
class ImageFinding:
    finding: str
    confidence: float | None = None


@dataclass
class ImageAnalysisResult:
    """
    Result produced by the vision layer.

    IMPORTANT:
    This object contains image observations and possible
    concerns only. It NEVER contains an ESI assignment.
    """

    image_quality: str = "unknown"

    visible_findings: list[ImageFinding] = field(
        default_factory=list
    )

    possible_concerns: list[str] = field(
        default_factory=list
    )

    cannot_determine: list[str] = field(
        default_factory=list
    )

    clinician_review_required: bool = True

    model_name: str = ""

    raw_response: str = ""


class GeminiVisionAnalysisService:
    """
    Multimodal image-analysis service.

    Recommended hackathon backend:
        Gemini 2.5 Flash-Lite

    The model is deliberately constrained to:
        1. describe visible findings,
        2. identify possible concerns,
        3. state what cannot be determined.

    It is NOT allowed to assign ESI.
    """

    DEFAULT_MODEL = "gemini-2.5-flash-lite"

    SYSTEM_INSTRUCTION = """
You are the image-observation component of a hospital
emergency-department clinical decision-support system.

Your task is ONLY to analyze what is visually observable
in the supplied image.

You MUST NOT:
- assign ESI;
- assign a triage category;
- recommend treatment;
- claim that a diagnosis is confirmed;
- infer internal injuries that cannot be seen;
- infer hemodynamic stability from appearance alone;
- replace clinician examination.

You SHOULD:
- describe visible injuries or abnormalities;
- describe visible bleeding, bruising, swelling, deformity,
  lacerations, burns, discoloration, asymmetry or other
  observable features when genuinely visible;
- describe possible clinical concerns conservatively;
- explicitly state important things that cannot be determined
  from the image;
- use uncertainty when image quality or visual evidence is poor.

For skin appearance, report observable visual appearance
such as "bluish discoloration" or "marked pallor" only when
visually apparent. Do not convert that observation into a
diagnosis such as hypoxemia.

For chest images, you may report visible asymmetry,
depression, bruising or apparent chest-wall deformity, but
do not confirm pneumothorax, flail chest, internal bleeding,
fracture or other internal pathology from a photograph alone.

Return ONLY valid JSON matching the requested schema.
"""

    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "image_quality": {
                "type": "string",
            },
            "visible_findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "finding": {
                            "type": "string",
                        },
                        "confidence": {
                            "type": "number",
                        },
                    },
                    "required": [
                        "finding",
                        "confidence",
                    ],
                },
            },
            "possible_concerns": {
                "type": "array",
                "items": {
                    "type": "string",
                },
            },
            "cannot_determine": {
                "type": "array",
                "items": {
                    "type": "string",
                },
            },
            "clinician_review_required": {
                "type": "boolean",
            },
        },
        "required": [
            "image_quality",
            "visible_findings",
            "possible_concerns",
            "cannot_determine",
            "clinician_review_required",
        ],
    }

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> None:

        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
        )

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Set it as an environment variable."
            )

        self.model_name = (
            model_name
            or os.getenv(
                "DOOM_AI_VISION_MODEL",
                self.DEFAULT_MODEL,
            )
        )

        self.client = genai.Client(
            api_key=self.api_key
        )

    # ========================================================
    # ANALYZE IMAGE
    # ========================================================

    def analyze(
        self,
        image_path: str,
    ) -> ImageAnalysisResult:

        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Image does not exist: {image_path}"
            )

        mime_type, _ = mimetypes.guess_type(
            str(path)
        )

        if not mime_type:
            raise ValueError(
                "Unable to determine image MIME type."
            )

        with path.open("rb") as file:
            image_bytes = file.read()

        prompt = """
Analyze this image strictly as a visual-observation aid
for an emergency-department clinician.

Return:
- visible findings;
- possible concerns based only on visible evidence;
- important things that cannot be determined from the image.

Do not assign ESI or a treatment decision.
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                prompt,
            ],
            config=types.GenerateContentConfig(
                system_instruction=(
                    self.SYSTEM_INSTRUCTION
                ),
                response_mime_type="application/json",
                response_schema=(
                    self.RESPONSE_SCHEMA
                ),
                temperature=0.0,
            ),
        )

        raw_text = (
            response.text
            if response.text
            else ""
        )

        if not raw_text.strip():
            raise RuntimeError(
                "Vision model returned an empty response."
            )

        try:
            parsed = json.loads(
                raw_text
            )

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Vision model returned invalid JSON."
            ) from exc

        visible_findings = []

        for item in parsed.get(
            "visible_findings",
            [],
        ):

            confidence = item.get(
                "confidence"
            )

            try:
                confidence = float(
                    confidence
                )
            except (
                TypeError,
                ValueError,
            ):
                confidence = None

            if confidence is not None:
                confidence = max(
                    0.0,
                    min(
                        1.0,
                        confidence,
                    ),
                )

            visible_findings.append(
                ImageFinding(
                    finding=str(
                        item.get(
                            "finding",
                            "",
                        )
                    ).strip(),
                    confidence=confidence,
                )
            )

        return ImageAnalysisResult(
            image_quality=str(
                parsed.get(
                    "image_quality",
                    "unknown",
                )
            ),
            visible_findings=(
                visible_findings
            ),
            possible_concerns=[
                str(item).strip()
                for item in parsed.get(
                    "possible_concerns",
                    [],
                )
                if str(item).strip()
            ],
            cannot_determine=[
                str(item).strip()
                for item in parsed.get(
                    "cannot_determine",
                    [],
                )
                if str(item).strip()
            ],
            clinician_review_required=bool(
                parsed.get(
                    "clinician_review_required",
                    True,
                )
            ),
            model_name=self.model_name,
            raw_response=raw_text,
        )

    # ========================================================
    # FORMAT FOR IMAGE-FINDINGS BOX
    # ========================================================

    @staticmethod
    def format_for_clinician(
        result: ImageAnalysisResult,
    ) -> str:

        lines = [
            "AI-ASSISTED IMAGE FINDINGS",
            "",
            f"Image quality: {result.image_quality}",
            "",
            "VISIBLE FINDINGS",
        ]

        if result.visible_findings:

            for item in result.visible_findings:

                if item.confidence is None:

                    lines.append(
                        f"• {item.finding}"
                    )

                else:

                    lines.append(
                        f"• {item.finding} "
                        f"[visual confidence "
                        f"{item.confidence * 100:.0f}%]"
                    )

        else:

            lines.append(
                "• No reliable visible finding identified."
            )

        lines.extend(
            [
                "",
                "POSSIBLE CONCERNS",
            ]
        )

        if result.possible_concerns:

            for item in result.possible_concerns:

                lines.append(
                    f"⚠ {item}"
                )

        else:

            lines.append(
                "• No specific concern identified."
            )

        lines.extend(
            [
                "",
                "CANNOT DETERMINE FROM IMAGE",
            ]
        )

        if result.cannot_determine:

            for item in result.cannot_determine:

                lines.append(
                    f"• {item}"
                )

        else:

            lines.append(
                "• None stated."
            )

        lines.extend(
            [
                "",
                "CLINICIAN REVIEW REQUIRED",
                "The above are visual observations only. "
                "Confirm, edit or reject them before "
                "triage evaluation.",
            ]
        )

        return "\n".join(
            lines
        )