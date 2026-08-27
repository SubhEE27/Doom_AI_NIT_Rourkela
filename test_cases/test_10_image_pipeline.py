from __future__ import annotations

import base64
import os
from pathlib import Path

from .common import load_modules, run_case, skip_case, is_api_configured, project_root

# 1x1 PNG fixture (transparent/neutral image)
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def run():
    mods = load_modules()
    if mods["image"] is None:
        return [skip_case("H10", "Image parser / vision pipeline", "ImageParser not present in current checkout.")]

    fixture = project_root() / "hackathon_tests" / "fixtures" / "sample_image.png"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_bytes(PNG_1X1)

    def local_parser():
        parser = mods["image"].ImageParser()
        meta = parser.parse(str(fixture))
        return (meta.get("readable", False), f"Local image parser accepted {meta.get('format')} {meta.get('width')}Ã—{meta.get('height')} image.")

    results = [run_case("H10A", "Local image ingestion / metadata", local_parser, "Image upload must work independently of external AI availability.")]

    # Live vision is optional so judges can run the suite without an API key.
    if os.getenv("GEMINI_API_KEY") and hasattr(mods["image"], "ImageParser"):
        def live_vision():
            parser = mods["image"].ImageParser()
            if not getattr(parser, "vision_service", None):
                return (False, "ImageParser exists but vision service is not configured.")
            result = parser.analyze(str(fixture))
            no_esi = not hasattr(result, "esi_level")
            return (no_esi and result.clinician_review_required, f"Vision result returned findings-only schema using model={result.model_name}.")
        results.append(run_case("H10B", "Live multimodal image findings (Gemini)", live_vision, "Image model writes findings/concerns/cannot-determine; it does not assign ESI."))
    else:
        results.append(skip_case("H10B", "Live multimodal image findings (Gemini)", "GEMINI_API_KEY not configured; live vision test skipped."))
    return results


