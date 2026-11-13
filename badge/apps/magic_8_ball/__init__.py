import math
import os
import random
import sys

APP_DIR = "/system/apps/magic_8_ball"
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

from oracle import ANSWERS, FLIPPING, IDLE, Ball, ShakeDetector, fit_lines

badge.mode(HIRES | VSYNC)

W = screen.width
H = screen.height
CX = W // 2
CY = H // 2 - 8
BALL_R = min(W, H) * 0.42
WINDOW_R = BALL_R * 0.62
TRI_R = WINDOW_R * 0.92
FACE_R = BALL_R * 0.44

BACKGROUND = color.rgb(14, 18, 36)
GLOW = color.rgb(40, 52, 110, 90)
SHADOW = color.rgb(0, 0, 0, 110)
BALL = color.rgb(14, 14, 18)
BALL_EDGE = color.rgb(46, 46, 58)
SHINE = color.rgb(255, 255, 255, 40)
SHINE_DOT = color.rgb(255, 255, 255, 110)
FACE = color.rgb(245, 245, 240)
EIGHT = color.rgb(14, 14, 18)
WINDOW = color.rgb(6, 8, 26)
WINDOW_RIM = color.rgb(60, 64, 80)
HINT = color.rgb(150, 160, 200)

# Upward-pointing unit triangle inscribed in a unit circle.
TRIANGLE = [vec2(0, -1), vec2(0.8660254, 0.5), vec2(-0.8660254, 0.5)]
TRI_SIZES = (17, 16, 15, 14, 13, 12, 11, 10)

try:
    TEXT_FONT = font.load("/system/assets/fonts/MonaSans-Medium.af")
    VECTOR = True
except Exception:
    TEXT_FONT = font.sins
    VECTOR = False

detector = ShakeDetector()
ball = Ball()
layouts = {}


def set_text_style():
    screen.font = TEXT_FONT
    screen.fill_rule = image.EVEN_ODD
    screen.antialias = image.X4


def measure(text, size):
    if VECTOR:
        try:
            return screen.measure_text(text, font_size=size)[0]
        except TypeError:
            pass
    return screen.measure_text(text)[0]


def draw_text(text, x, y, w, h, size):
    box = rect(int(x), int(y), int(w), int(h))
    if VECTOR:
        screen.text(text, box, align=(CENTER, MIDDLE), font_size=size)
    else:
        screen.text(text, box, align=(CENTER, MIDDLE))


def layout_for(index):
    if index not in layouts:
        set_text_style()
        layouts[index] = fit_lines(ANSWERS[index][1], TRI_R, measure, TRI_SIZES)
    return layouts[index]


def ease_out(t):
    return 1 - (1 - t) * (1 - t) * (1 - t)


def draw_ball(ox, oy):
    screen.pen = GLOW
    screen.shape(shape.circle(CX, CY, BALL_R + 10))
    screen.pen = SHADOW
    screen.shape(shape.ellipse(CX, CY + BALL_R + 6, BALL_R * 0.7, 7))
    screen.pen = BALL_EDGE
    screen.shape(shape.circle(CX + ox, CY + oy, BALL_R + 1))
    screen.pen = BALL
    screen.shape(shape.circle(CX + ox, CY + oy, BALL_R - 1))
    screen.pen = SHINE
    screen.shape(shape.ellipse(CX + ox - BALL_R * 0.35, CY + oy - BALL_R * 0.5, BALL_R * 0.38, BALL_R * 0.2))
    screen.pen = SHINE_DOT
    screen.shape(shape.circle(CX + ox - BALL_R * 0.45, CY + oy - BALL_R * 0.55, BALL_R * 0.06))


def draw_eight_face(x, y, squash):
    if squash <= 0.02:
        return
    screen.pen = FACE
    screen.shape(shape.ellipse(x, y, FACE_R * squash, FACE_R))
    if squash < 0.75:
        return
    screen.pen = EIGHT
    s = 0.85  # overall scale of the "8" relative to the white face
    w = 0.18 * FACE_R * s
    # Two slightly-squashed circles stacked and touching at the middle, like
    # a stylised "8" (a smaller top loop and a slightly larger bottom loop).
    screen.shape(shape.ellipse(x, y - FACE_R * 0.44 * s, FACE_R * 0.38 * s, FACE_R * 0.27 * s).stroke(w))
    screen.shape(shape.ellipse(x, y + FACE_R * 0.33 * s, FACE_R * 0.44 * s, FACE_R * 0.33 * s).stroke(w))


def draw_answer_face(x, y, squash, index, reveal):
    if squash <= 0.02:
        return
    screen.pen = WINDOW_RIM
    screen.shape(shape.ellipse(x, y, (WINDOW_R + 3) * squash, WINDOW_R + 3))
    screen.pen = WINDOW
    screen.shape(shape.ellipse(x, y, WINDOW_R * squash, WINDOW_R))
    if index is None:
        return

    # The answer die floats up out of the dark liquid while it brightens.
    e = ease_out(reveal)
    rise = (1 - e) * WINDOW_R * 0.45
    level = 0.25 + 0.75 * e
    tri = shape.custom(TRIANGLE)
    tri.transform = mat3().translate(x, y + rise).scale(TRI_R * squash, TRI_R)
    screen.pen = color.rgb(int(28 * level), int(70 * level), int(205 * level))
    screen.shape(tri)

    if squash < 0.98 or reveal <= 0:
        return
    size, top, line_h = layout_for(index)
    set_text_style()
    screen.pen = color.rgb(240, 246, 255, int(255 * e))
    for i, line in enumerate(ANSWERS[index][1]):
        ly = y + rise + top + i * line_h
        draw_text(line, x - TRI_R, ly - 3, TRI_R * 2, line_h + 6, size)


def draw_hint():
    if ball.busy():
        return
    set_text_style()
    screen.pen = HINT
    text = "Shake me or press SELECT" if ball.state == IDLE else "Shake again to ask another question"
    draw_text(text, 0, H - 22, W, 18, 13)


def update():
    dt = badge.ticks_delta
    ax, ay, az, _gx, _gy, _gz = badge.imu()
    shaken = detector.update(ax, ay, az, dt)

    if shaken or badge.pressed(BUTTON_SELECT):
        ball.ask(random.randint)

    ball.advance(dt)

    screen.antialias = image.X4
    screen.pen = BACKGROUND
    screen.clear()

    ox = oy = 0
    if ball.state == FLIPPING:
        p = ball.flip_progress()
        wobble = max(0.0, 1 - p * 2.5)
        ox = math.sin(p * 40) * 6 * wobble
        oy = -math.sin(p * math.pi) * 6
    draw_ball(ox, oy)

    x, y = CX + ox, CY + oy
    if ball.state == IDLE:
        draw_eight_face(x, y, 1.0)
    elif ball.state == FLIPPING:
        p = ball.flip_progress()
        squash = abs(math.cos(p * math.pi))
        if p < 0.5:
            if ball.previous is None:
                draw_eight_face(x, y, squash)
            else:
                draw_answer_face(x, y, squash, ball.previous, 1.0)
        else:
            draw_answer_face(x, y, squash, ball.answer, 0.0)
    else:
        draw_answer_face(x, y, 1.0, ball.answer, ball.reveal_progress())

    draw_hint()


run(update)
