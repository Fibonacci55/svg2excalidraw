from enum import Enum
from typing import Dict, List, Optional, Tuple, Protocol
import logging
import math
from excalidraw_writer import Excalidraw_Element

log = logging.getLogger('excalidraw_writer')


# ------------------------------------------------------------------
#  Enums
# ------------------------------------------------------------------
class TangramObject(Enum):
    """Enumeration of the five tangram piece shapes."""
    SQUARE = 1
    BIG_TRIANGLE = 2
    MEDIUM_TRIANGLE = 3
    SMALL_TRIANGLE = 4
    PARALLELOGRAM = 5


# ------------------------------------------------------------------
#  Protocol
# ------------------------------------------------------------------
class ColorTweaker(Protocol):
    """Protocol for objects that apply colors to Excalidraw elements."""

    def apply_colors(self, elements: List['Excalidraw_Element']) -> None:
        """Set ``backgroundColor`` on each element appropriately."""
        ...


# ------------------------------------------------------------------
#  KeepColorTweaker – leaves existing colors untouched
# ------------------------------------------------------------------
class KeepColorTweaker:
    """A no‑op color tweaker that preserves the elements' current colors."""

    def apply_colors(self, elements: List['Excalidraw_Element']) -> None:
        """Intentionally does nothing."""
        pass


# ------------------------------------------------------------------
#  AreaColorTweak – sets colors based on tangram shape classification
# ------------------------------------------------------------------
class AreaColorTweak:
    """
    Categorizes Excalidraw_Element objects into tangram shapes and sets their
    background colors according to a provided color map.

    Usage:
        color_map = {
            TangramObject.SQUARE: '#ff0000',
            TangramObject.BIG_TRIANGLE: '#00ff00',
            TangramObject.MEDIUM_TRIANGLE: '#0000ff',
            TangramObject.SMALL_TRIANGLE: '#ffff00',
            TangramObject.PARALLELOGRAM: '#ff00ff',
        }
        tweaker = AreaColorTweak(color_map)
        tweaker.apply_colors(list_of_elements)
    """

    # ------------------------------------------------------------------
    #  Square / triangle size heuristics (tunable)
    # ------------------------------------------------------------------
    _RATIO_BIG_MEDIUM = 0.375     # midway between 0.5 and 0.25
    _RATIO_MEDIUM_SMALL = 0.1875  # midway between 0.25 and 0.125
    _POINT_TOLERANCE = 1e-6

    def __init__(self, color_map: Dict[TangramObject, str]) -> None:
        if not all(k in color_map for k in TangramObject):
            raise ValueError(
                "color_map must contain entries for all five TangramObject members."
            )
        self.color_map = color_map

        # Cached values computed during _analyze_elements()
        self._square_area: Optional[float] = None
        self._triangle_thresholds: Optional[Tuple[float, float]] = None

    # ------------------------------------------------------------------
    #  Geometry helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_polygon_area(points: List[List[float]]) -> float:
        """Shoelace formula for any simple polygon (auto‑closes last→first)."""
        n = len(points)
        if n < 3:
            return 0.0
        area = 0.0
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            area += x1 * y2 - x2 * y1
        return abs(area) / 2.0

    def _points_close(self, p1: List[float], p2: List[float]) -> bool:
        return (
            math.isclose(p1[0], p2[0], abs_tol=self._POINT_TOLERANCE)
            and math.isclose(p1[1], p2[1], abs_tol=self._POINT_TOLERANCE)
        )

    def _get_absolute_points(self, element: 'Excalidraw_Element') -> List[List[float]]:
        """
        Convert element‑relative points to absolute canvas coordinates.

        Excalidraw stores ``points`` relative to the element's ``x``/``y``
        anchor, with the first point always being ``[0, 0]``. Closed
        shapes typically repeat the start point ``[0, 0]`` one or more
        times at the end of the list to explicitly close the loop.
        These trailing duplicates of the start point carry no additional
        vertex information and are dropped here — the shoelace formula
        already closes the polygon implicitly by connecting the last
        point back to the first.
        """
        pts = getattr(element, 'points', None)
        if not pts:
            return []

        abs_pts = [[element.x + p[0], element.y + p[1]] for p in pts]
        start = abs_pts[0]

        # Strip all trailing points that coincide with the start point.
        while len(abs_pts) > 1 and self._points_close(abs_pts[-1], start):
            abs_pts.pop()

        return abs_pts

    # ------------------------------------------------------------------
    #  Shape identification (single element)
    # ------------------------------------------------------------------
    def _identify_shape(self, element: 'Excalidraw_Element') -> Tuple[Optional[str], float]:
        """
        Classify a single element by its geometric shape.

        Returns:
            (shape_kind, area) where *shape_kind* is one of:
                'square' | 'triangle' | 'parallelogram' | None.
        """
        #if element.type == 'rectangle':
        #    w, h = element.width, element.height
        #    if w > 0 and h > 0 and max(w, h) / min(w, h) <= 1.15:
        #        return ('square', w * h)

        def _is_square(el: Excalidraw_Element ) -> bool:
            pass

        if element.type == 'line':
            abs_pts = self._get_absolute_points(element)
            n = len(abs_pts)
            area = self._compute_polygon_area(abs_pts)
            if n == 3:
                return ('triangle', area)
            if n == 4 and not _is_square(element):
                return ('parallelogram', area)

        return (None, 0.0)

    # ------------------------------------------------------------------
    #  Categorisation (single element)
    # ------------------------------------------------------------------
    def _categorize_element(self, element: 'Excalidraw_Element') -> Optional[TangramObject]:
        """
        Map a single element to its TangramObject enum value using
        structural pattern matching on the shape kind returned by
        ``_identify_shape``.
        """
        kind, area = self._identify_shape(element)

        match kind:
            case 'square':
                return TangramObject.SQUARE
            case 'parallelogram':
                return TangramObject.PARALLELOGRAM
            case 'triangle':
                return self._categorize_triangle(area)
            case _:
                return None

    def _categorize_triangle(self, area: float) -> TangramObject:
        """Assign a triangle to BIG / MEDIUM / SMALL based on its area."""
        # Strategy 1: square area as reference
        if self._square_area is not None and self._square_area > 0:
            ratio = area / self._square_area
            if ratio >= self._RATIO_BIG_MEDIUM:
                return TangramObject.BIG_TRIANGLE
            if ratio >= self._RATIO_MEDIUM_SMALL:
                return TangramObject.MEDIUM_TRIANGLE
            return TangramObject.SMALL_TRIANGLE

        # Strategy 2: pre‑computed clustering thresholds
        if self._triangle_thresholds is not None:
            small_max, medium_max = self._triangle_thresholds
            if area > medium_max:
                return TangramObject.BIG_TRIANGLE
            if area > small_max:
                return TangramObject.MEDIUM_TRIANGLE
            return TangramObject.SMALL_TRIANGLE

        # Fallback
        log.warning('No reference for triangle sizing – defaulting to MEDIUM_TRIANGLE.')
        return TangramObject.MEDIUM_TRIANGLE

    # ------------------------------------------------------------------
    #  Bulk analysis
    # ------------------------------------------------------------------
    def _analyze_elements(self, elements: List['Excalidraw_Element']) -> None:
        """Scan all elements to determine square area and triangle thresholds."""
        triangle_areas: List[float] = []
        self._square_area = None

        for elem in elements:
            kind, area = self._identify_shape(elem)
            if kind == 'square' and self._square_area is None:
                self._square_area = area
            elif kind == 'triangle' and area > 0:
                triangle_areas.append(area)

        if self._square_area is None and len(triangle_areas) >= 2:
            triangle_areas.sort()
            n = len(triangle_areas)
            idx_small = n // 3
            idx_medium = 2 * n // 3
            self._triangle_thresholds = (
                triangle_areas[idx_small],
                triangle_areas[idx_medium],
            )
        else:
            self._triangle_thresholds = None

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------
    def apply_colors(self, elements: List['Excalidraw_Element']) -> None:
        """
        Categorize every element and set its ``backgroundColor`` to the
        corresponding color from the color map.

        Elements that cannot be categorized are left untouched.
        """
        self._analyze_elements(elements)

        for elem in elements:
            category = self._categorize_element(elem)
            if category is not None:
                elem.backgroundColor = self.color_map[category]
