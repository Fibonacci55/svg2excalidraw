from collections import UserDict
import re


class SvgStyle2Excalidraw(UserDict):
    """
    Converts an SVG style mapping (dict or CSS-like 'a:b;c:d' string) into
    Excalidraw element properties.

    Notes:
    - Excalidraw has a single 'opacity' per element; SVG can have opacity,
      fill-opacity, stroke-opacity. We approximate with:
          effective = overall_opacity * min(used_fill_opacity, used_stroke_opacity)
      (ignoring fill-opacity if fill='none', and stroke-opacity if stroke='none').
    """

    _NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")

    def __init__(self):
        super().__init__()

    @staticmethod
    def _clamp(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    @classmethod
    def _extract_number(cls, value) -> float | None:
        """
        Extract a float from values like:
          1, 1.5, '2', '2px', '0.5pt', ' 3.2 '
        Returns None if no number is found.
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        s = str(value).strip()
        if not s:
            return None

        m = cls._NUM_RE.search(s)
        if not m:
            return None

        try:
            return float(m.group(0))
        except ValueError:
            return None

    @classmethod
    def _parse_alpha(cls, value) -> float | None:
        """
        SVG opacity values are typically 0..1 (sometimes written as percentages).
        Returns alpha in [0..1] or None if not parseable.
        """
        if value is None:
            return None

        s = str(value).strip()
        if not s:
            return None

        if s.endswith("%"):
            num = cls._extract_number(s[:-1])
            if num is None:
                return None
            return cls._clamp(num / 100.0, 0.0, 1.0)

        num = cls._extract_number(s)
        if num is None:
            return None

        # If someone gave "50" assume percent-like; otherwise standard SVG 0..1.
        if num > 1.0:
            num = num / 100.0
        return cls._clamp(num, 0.0, 1.0)

    @classmethod
    def _parse_style(cls, svg_style) -> dict:
        if svg_style is None:
            return {}
        if isinstance(svg_style, dict):
            return svg_style
        if isinstance(svg_style, str):
            # Parse "fill:#fff; stroke:#000; stroke-width:2"
            out = {}
            for part in svg_style.split(";"):
                part = part.strip()
                if not part or ":" not in part:
                    continue
                k, v = part.split(":", 1)
                out[k.strip()] = v.strip()
            return out
        # Unknown container type
        return {}

    @staticmethod
    def _to_excal_color(value: str | None) -> str | None:
        """
        Excalidraw accepts color strings (e.g. '#rrggbb') and 'transparent'.
        """
        if value is None:
            return None
        s = str(value).strip()
        if not s:
            return None
        if s.lower() == "none":
            return "transparent"
        return s

    @classmethod
    def _to_excal_stroke_width(cls, value) -> int | None:
        """
        Map SVG stroke-width (often in px) to Excalidraw strokeWidth.
        Excalidraw typically uses small integer widths. We clamp to [1..4].
        """
        num = cls._extract_number(value)
        if num is None:
            return None

        # Keep it simple and predictable: round and clamp.
        w = int(round(num))
        return max(1, min(4, w))

    def __call__(self, svg_style) -> dict:
        style = self._parse_style(svg_style)
        out: dict = {}

        # Colors
        if "fill" in style:
            out["backgroundColor"] = self._to_excal_color(style.get("fill"))
        if "stroke" in style:
            out["strokeColor"] = self._to_excal_color(style.get("stroke"))

        # Stroke width
        if "stroke-width" in style:
            sw = self._to_excal_stroke_width(style.get("stroke-width"))
            if sw is not None:
                out["strokeWidth"] = sw

        # Opacity (approximate SVG rules into a single Excalidraw opacity)
        overall_alpha = self._parse_alpha(style.get("opacity"))
        fill_alpha = self._parse_alpha(style.get("fill-opacity"))
        stroke_alpha = self._parse_alpha(style.get("stroke-opacity"))

        if overall_alpha is None and fill_alpha is None and stroke_alpha is None:
            return out

        overall_alpha = 1.0 if overall_alpha is None else overall_alpha
        fill_alpha = 1.0 if fill_alpha is None else fill_alpha
        stroke_alpha = 1.0 if stroke_alpha is None else stroke_alpha

        fill_val = str(style.get("fill", "")).strip().lower()
        stroke_val = str(style.get("stroke", "")).strip().lower()

        candidates = []
        if fill_val and fill_val != "none":
            candidates.append(fill_alpha)
        if stroke_val and stroke_val != "none":
            candidates.append(stroke_alpha)

        effective_alpha = overall_alpha * (min(candidates) if candidates else 1.0)
        effective_alpha = self._clamp(effective_alpha, 0.0, 1.0)
        out["opacity"] = int(round(effective_alpha * 100))

        return out
