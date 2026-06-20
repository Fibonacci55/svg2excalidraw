# svg2excalidraw.py

import argparse
import re
from collections import UserDict
from dataclasses import replace
from pathlib import Path

import jsonpickle

import svg_reader
import excalidraw_writer
from path_handler import PathHandler

import svg2exc_logging

log = svg2exc_logging.getLogger("svg2excalidraw")


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


class Converter:
    def __init__(self):
        self.elements = []
        self.path_handler = PathHandler()
        self.style_converter = SvgStyle2Excalidraw()
        self.groups: list[str] = []
        self._auto_id = 0

    def _new_id(self, prefix: str) -> str:
        self._auto_id += 1
        return f"{prefix}_{self._auto_id}"

    def _group_ids_copy(self) -> list[str]:
        return list(self.groups)

    def visit_group(self, group):
        gid = getattr(group, "id", None) or self._new_id("group")
        log.debug(">>>>> %s", gid)

        self.groups.append(gid)
        for el in getattr(group, "group_elements", []):
            el.visit(self)
        self.groups.pop()

        log.debug("<<<<< %s", gid)

    def visit_rectangle(self, rectangle):
        log.debug("visiting rectangle")

        rid = getattr(rectangle, "id", None) or self._new_id("rect")
        style = self.style_converter(getattr(rectangle, "style", None))

        def _f(v, default=0.0):
            try:
                return float(v)
            except (TypeError, ValueError):
                return float(default)

        r = excalidraw_writer.Rectangle(
            id=rid,
            x=_f(getattr(rectangle, "x", 0)),
            y=_f(getattr(rectangle, "y", 0)),
            width=_f(getattr(rectangle, "width", 0)),
            height=_f(getattr(rectangle, "height", 0)),
            groupIds=self._group_ids_copy(),
            **style,
        )
        self.elements.append(r)

    def visit_path(self, path):
        pid = getattr(path, "id", None) or self._new_id("path")
        pdata = getattr(path, "path_data", None)
        log.debug(">>>>> %s %s", pid, pdata)

        style = self.style_converter(getattr(path, "style", None))
        line_list = self.path_handler(pdata) if pdata else []

        if not line_list:
            log.debug("path %s produced no drawable segments", pid)
            log.debug("<<<<< %s", pid)
            return

        if len(line_list) > 1:
            group_id = f"g_{pid}"
            self.groups.append(group_id)

            for i, l in enumerate(line_list):
                nl = replace(
                    l,
                    id=f"{pid}_{i}",
                    groupIds=self._group_ids_copy(),
                    **style,
                )
                self.elements.append(nl)

            self.groups.pop()
        else:
            nl = replace(
                line_list[0],
                id=pid,
                groupIds=self._group_ids_copy(),
                **style,
                from_init=False,
            )
            self.elements.append(nl)

        log.debug("<<<<< %s", pid)

    def convert(self, svg_elements):
        for el in svg_elements:
            el.visit(self)


def convert(inpath: Path, outpath: Path, pattern: str = "*.svg") -> None:
    inpath = Path(inpath)
    outpath = Path(outpath)

    if inpath.is_dir():
        svg_files = sorted(inpath.glob(pattern))
        outpath.mkdir(parents=True, exist_ok=True)
        output_is_dir = True
    elif inpath.is_file():
        svg_files = [inpath]
        # If outpath is a directory (or looks like one), keep original naming.
        output_is_dir = (outpath.exists() and outpath.is_dir()) or (outpath.suffix == "")
        if output_is_dir:
            outpath.mkdir(parents=True, exist_ok=True)
    else:
        raise FileNotFoundError(f"Input path not found: {inpath}")

    for filename in svg_files:
        try:
            w = svg_reader.My_Doc_Walker(filename)
            w.walk()

            c = Converter()
            c.convert(w.elements)

            if output_is_dir:
                outf_name = outpath / f"{filename.stem}.excalidraw"
            else:
                # Single input file -> single output file
                outf_name = outpath

            painting = excalidraw_writer.Excalidraw_Painting(elements=c.elements)
            payload = jsonpickle.encode(painting, unpicklable=False, indent=3)
            outf_name.write_text(payload, encoding="utf-8")

            log.info("wrote %s", outf_name)
        except Exception:
            # Keep batch conversion going even if one file fails
            log.exception("failed converting %s", filename)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert SVG files to Excalidraw JSON.")
    parser.add_argument("inpath", type=Path, help="Input SVG file or directory")
    parser.add_argument("outpath", type=Path, help="Output .excalidraw file or directory")
    parser.add_argument("--pattern", default="*.svg", help="Glob pattern when inpath is a directory")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity",
    )
    args = parser.parse_args()

    # If svg2exc_logging doesn't globally configure levels, this is still harmless.
    try:
        log.setLevel(args.log_level)
    except Exception:
        pass

    convert(args.inpath, args.outpath, pattern=args.pattern)


if __name__ == "__main__":
    main()
