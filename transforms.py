"""
2D transformations written from scratch using 3x3 homogeneous matrices.

Every object in the game is a list of (x, y) points.  To move / rotate / scale
an object we multiply its points by a matrix.  Several transformations can be
combined (composite transformation) by multiplying their matrices together.

NOTE: the screen's y axis points DOWN, so a positive rotation angle turns an
object clockwise on the screen.
"""
import math


def identity():
    return [[1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]]


# ---------------------------------------------------------------- basic ones
def translate(tx, ty):
    """Translation: move by (tx, ty)."""
    return [[1, 0, tx],
            [0, 1, ty],
            [0, 0, 1]]


def scale(sx, sy):
    """Scaling about the origin (0, 0)."""
    return [[sx, 0, 0],
            [0, sy, 0],
            [0, 0, 1]]


def rotate(deg):
    """Rotation about the origin by `deg` degrees."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0],
            [s, c, 0],
            [0, 0, 1]]


def reflect_x():
    """Reflection about the x axis (flips up/down) - used for water reflections."""
    return [[1, 0, 0],
            [0, -1, 0],
            [0, 0, 1]]


def reflect_y():
    """Reflection about the y axis (flips left/right) - used to turn characters around."""
    return [[-1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]]


def shear_x(k):
    """Shear along x: x' = x + k*y - used for swaying trees and shaking bins."""
    return [[1, k, 0],
            [0, 1, 0],
            [0, 0, 1]]


def shear_y(k):
    """Shear along y: y' = y + k*x."""
    return [[1, 0, 0],
            [k, 1, 0],
            [0, 0, 1]]


# -------------------------------------------------------------- combinations
def multiply(a, b):
    """Matrix product a x b (apply b first, then a)."""
    r = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                r[i][j] += a[i][k] * b[k][j]
    return r


def compose(*mats):
    """compose(A, B, C) == A x B x C  (C is applied to the points first)."""
    result = identity()
    for m in mats:
        result = multiply(result, m)
    return result


def rotate_about(deg, cx, cy):
    """Rotate about an arbitrary pivot (cx, cy): T(c) . R . T(-c)."""
    return compose(translate(cx, cy), rotate(deg), translate(-cx, -cy))


def scale_about(sx, sy, cx, cy):
    """Scale about an arbitrary point (cx, cy)."""
    return compose(translate(cx, cy), scale(sx, sy), translate(-cx, -cy))


# ------------------------------------------------------------ applying them
def transform_point(p, m):
    x, y = p
    return (m[0][0] * x + m[0][1] * y + m[0][2],
            m[1][0] * x + m[1][1] * y + m[1][2])


def transform_points(points, m):
    return [transform_point(p, m) for p in points]


def scale_factor(m):
    """Average scale of a matrix (square root of the determinant)."""
    return math.sqrt(abs(m[0][0] * m[1][1] - m[0][1] * m[1][0]))


# ------------------------------------------------- window to viewport mapping
def window_to_viewport(x, y, window, viewport):
    """
    Map a point from a world 'window' (xmin, ymin, xmax, ymax) to a screen
    'viewport' (xmin, ymin, xmax, ymax).  Used for the route mini-map.
    """
    wxmin, wymin, wxmax, wymax = window
    vxmin, vymin, vxmax, vymax = viewport
    sx = (vxmax - vxmin) / (wxmax - wxmin)
    sy = (vymax - vymin) / (wymax - wymin)
    return vxmin + (x - wxmin) * sx, vymin + (y - wymin) * sy
