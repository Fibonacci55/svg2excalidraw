# svg2excalidraw.py

import argparse
from dataclasses import replace
from pathlib import Path
from style_converter import SvgStyle2Excalidraw
from excalidraw_colors import ColorTweaker, KeepColorTweaker, AreaColorTweak, TangramObject

import jsonpickle

import svg_reader
import excalidraw_writer
from path_handler import PathHandler

import svg2exc_logging

log = svg2exc_logging.getLogger("svg2excalidraw")

class Converter:
    def __init__(self, style_converter : SvgStyle2Excalidraw=SvgStyle2Excalidraw(), color_tweak: ColorTweaker = KeepColorTweaker()):
        self.elements = []
        self.path_handler = PathHandler()
        self.groups: list[str] = []
        self._auto_id = 0
        self.style_converter = style_converter
        self.color_tweak = color_tweak

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


def convert(inpath: Path, outpath: Path, pattern: str = "*.svg",
            style_converter: SvgStyle2Excalidraw=SvgStyle2Excalidraw(),
            color_tweak: ColorTweaker=KeepColorTweaker) -> None:
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

            c = Converter(style_converter=style_converter, color_tweak=color_tweak)
            c.convert(w.elements)

            if output_is_dir:
                outf_name = outpath / f"{filename.stem}.excalidraw"
            else:
                # Single input file -> single output file
                outf_name = outpath

            color_tweak.apply_colors(c.elements)
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

    colors = {
        TangramObject.SQUARE : '#4EE203',
        TangramObject.BIG_TRIANGLE : '#115AB8',
        TangramObject.PARALLELOGRAM : '#FF9F03',
        TangramObject.SMALL_TRIANGLE : '#4EE203',
        TangramObject.MEDIUM_TRIANGLE : '#F29F03',
    }
    convert(args.inpath, args.outpath, pattern=args.pattern, color_tweak=AreaColorTweak(colors))


if __name__ == "__main__":
    main()
