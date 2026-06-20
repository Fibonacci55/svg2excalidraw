# path_handler.py

from excalidraw_writer import Line
from path_common import Point
from path_parser import svg_path
from path_commands import Command_Factory, ClosePath, Move

import svg2exc_logging
log = svg2exc_logging.getLogger("path_handler")


class PathHandler:
    def __init__(self):
        # Keep a single factory instance per handler (reduces shared/global access patterns)
        self._command_factory = Command_Factory()
        self._reset_state()

    def _reset_state(self) -> None:
        self.points = []
        self.cmd_list = []
        self.sub_path_list = []
        # Use numeric origin instead of None to avoid arithmetic errors in command execution
        self.current_point = Point(0, 0)

    def _parse_commands(self, path_data: str):
        Command_Factory.clear_cmd_list()
        parse_fn = getattr(svg_path, "parse_string", None) or getattr(svg_path, "parseString")
        parse_fn(path_data)
        return list(Command_Factory.command_list)

    def _determine_sub_paths(self, path_data: str) -> None:
        log.info(">>>>> %s", path_data)

        try:
            self.cmd_list = self._parse_commands(path_data)
        except Exception:
            log.exception("Failed to parse SVG path data")
            self.cmd_list = []
            self.sub_path_list = []
            return

        self.sub_path_list = []
        if not self.cmd_list:
            log.debug("No commands parsed from path data")
            log.info("<<<<<")
            return

        if not isinstance(self.cmd_list[0], Move):
            # Don’t try to synthesize a Move without knowing constructor signature;
            # just warn and rely on current_point=(0,0) as implicit origin.
            log.warning(
                "Path does not start with Move; execution will start from origin (0,0). "
                "First command type: %s",
                type(self.cmd_list[0]).__name__,
            )

        current_subpath = [self.cmd_list[0]]
        for cmd in self.cmd_list[1:]:
            if isinstance(cmd, Move):
                if current_subpath:
                    self.sub_path_list.append(current_subpath)
                current_subpath = [cmd]
            else:
                current_subpath.append(cmd)

        if current_subpath:
            self.sub_path_list.append(current_subpath)

        log.debug("cmd list %s", self.cmd_list)
        log.info("<<<<<")

    def __call__(self, path_data: str):
        log.debug(">>>>>")

        self._reset_state()
        self._determine_sub_paths(path_data)

        if not self.sub_path_list:
            log.debug("<<<<<<")
            return []

        line_list = []

        # Keep current_point across subpaths (relative Move depends on prior current point)
        for subpath in self.sub_path_list:
            sub_path_point_list = []

            for cmd in subpath:
                if isinstance(cmd, ClosePath):
                    # Close the current subpath only if we have points to close
                    if sub_path_point_list:
                        sub_path_point_list.append(sub_path_point_list[0])
                        # SVG semantics: current point becomes the start point after close
                        self.current_point = sub_path_point_list[0]
                    else:
                        log.warning("ClosePath encountered before any points were generated")
                    continue

                new_points = cmd.execute(self.current_point) or []
                if new_points:
                    sub_path_point_list.extend(new_points)
                    self.current_point = sub_path_point_list[-1]
                else:
                    # Avoid IndexError and keep current_point unchanged if command produced nothing
                    log.debug(
                        "Command %s produced no points; current_point unchanged (%s)",
                        type(cmd).__name__,
                        self.current_point,
                    )

                log.debug("sub path %s", sub_path_point_list)
                log.debug("current point %s", self.current_point)

            # Don’t create a Line if the subpath generated no points
            if not sub_path_point_list:
                log.debug("Skipping empty subpath (no points generated)")
                continue

            line = Line(
                x=sub_path_point_list[0].x,
                y=sub_path_point_list[0].y,
                points=sub_path_point_list,
            )
            line_list.append(line)

        log.debug("<<<<<<")
        return line_list


if __name__ == "__main__":
    ho = "m4673.6 4123h-250.5v-250.5l250.5 250.5z"
    p = PathHandler()
    result = p(ho)
    print(result)
