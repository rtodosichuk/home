# Pure logic for the Magic 8 Ball app: shake detection, answer choice and
# animation timing. It has no badge dependencies so it can be tested on a PC.

import math

# The 2026 badge reports about 16384 accelerometer counts per g.
COUNTS_PER_G = 16384

# (full answer, lines drawn inside the answer triangle, narrowest line first)
ANSWERS = (
    ("Most definitely!", ("Most", "definitely!")),
    ("Seems doubtful", ("Seems", "doubtful")),
    ("Signs point to yes", ("Signs", "point to yes")),
    ("Ask again later", ("Ask", "again later")),
    ("Without a doubt", ("Without", "a doubt")),
    ("Don't count on it", ("Don't", "count on it")),
    ("Outlook good", ("Outlook", "good")),
    ("My sources say no", ("My", "sources", "say no")),
)


class ShakeDetector:
    """Turns raw accelerometer samples into single shake events.

    Gravity is tracked with a low-pass filter and subtracted, leaving the
    movement part of the signal. A shake is two separate jolts above JOLT_G
    within WINDOW_MS. After a shake the detector disarms; it re-arms only
    after COOLDOWN_MS has passed and the badge has stayed calm (below QUIET_G)
    for QUIET_MS, so continuous shaking yields exactly one event.
    """

    GRAVITY_TAU_MS = 250.0
    JOLT_G = 0.75
    RESET_G = 0.35
    QUIET_G = 0.25
    WINDOW_MS = 700
    COOLDOWN_MS = 900
    QUIET_MS = 350
    MAX_DT_MS = 100
    JOLTS_NEEDED = 2
    REVERSAL_DOT = -0.3

    def __init__(self):
        self.gravity = None
        self.motion = 0.0
        self.armed = True
        self.peak_ready = True
        self.last_dir = None
        self.jolts = []
        self.now = 0
        self.cooldown_until = 0
        self.calm_ms = 0

    def update(self, ax, ay, az, dt_ms):
        """Feed one raw sample. Returns True once per detected shake."""
        dt = min(max(dt_ms, 0), self.MAX_DT_MS)
        self.now += dt
        x, y, z = ax / COUNTS_PER_G, ay / COUNTS_PER_G, az / COUNTS_PER_G

        if self.gravity is None:
            self.gravity = [x, y, z]
        elif dt:
            k = 1.0 - math.exp(-dt / self.GRAVITY_TAU_MS)
            g = self.gravity
            g[0] += (x - g[0]) * k
            g[1] += (y - g[1]) * k
            g[2] += (z - g[2]) * k

        g = self.gravity
        dx, dy, dz = x - g[0], y - g[1], z - g[2]
        self.motion = math.sqrt(dx * dx + dy * dy + dz * dz)

        if not self.armed:
            if self.motion < self.QUIET_G:
                self.calm_ms += dt
            else:
                self.calm_ms = 0
            if self.now >= self.cooldown_until and self.calm_ms >= self.QUIET_MS:
                self.armed = True
                self.peak_ready = True
                self.last_dir = None
                self.jolts = []
            return False

        self.jolts = [t for t in self.jolts if self.now - t <= self.WINDOW_MS]

        if self.motion < self.RESET_G:
            self.peak_ready = True
        elif self.motion >= self.JOLT_G:
            # A reversal (badge flung back the other way) counts as a new jolt
            # even if the motion never settles between swings, which happens
            # with fast shakes at low frame rates.
            m = self.motion
            ux, uy, uz = dx / m, dy / m, dz / m
            lj = self.last_dir
            reversed_ = lj is not None and ux * lj[0] + uy * lj[1] + uz * lj[2] < self.REVERSAL_DOT
            if self.peak_ready or reversed_:
                self.peak_ready = False
                self.last_dir = (ux, uy, uz)
                self.jolts.append(self.now)
                if len(self.jolts) >= self.JOLTS_NEEDED:
                    self.armed = False
                    self.jolts = []
                    self.last_dir = None
                    self.calm_ms = 0
                    self.cooldown_until = self.now + self.COOLDOWN_MS
                    return True
        return False


IDLE = 0
FLIPPING = 1
REVEALING = 2
SHOWING = 3


class Ball:
    """Animation state: the ball turns over, then the answer floats up."""

    FLIP_MS = 1000
    REVEAL_MS = 700

    def __init__(self):
        self.state = IDLE
        self.elapsed = 0
        self.answer = None
        self.previous = None

    def busy(self):
        return self.state == FLIPPING or self.state == REVEALING

    def ask(self, randint):
        """Start turning over to a new answer. randint(a, b) is inclusive."""
        if self.busy():
            return False
        choices = [i for i in range(len(ANSWERS)) if i != self.answer]
        self.previous = self.answer
        self.answer = choices[randint(0, len(choices) - 1)]
        self.state = FLIPPING
        self.elapsed = 0
        return True

    def advance(self, dt_ms):
        if not self.busy():
            return
        self.elapsed += max(dt_ms, 0)
        if self.state == FLIPPING and self.elapsed >= self.FLIP_MS:
            self.state = REVEALING
            self.elapsed -= self.FLIP_MS
        if self.state == REVEALING and self.elapsed >= self.REVEAL_MS:
            self.state = SHOWING
            self.elapsed = 0

    def flip_progress(self):
        if self.state == FLIPPING:
            return min(1.0, self.elapsed / self.FLIP_MS)
        return 1.0

    def reveal_progress(self):
        if self.state == FLIPPING:
            return 0.0
        if self.state == REVEALING:
            return min(1.0, self.elapsed / self.REVEAL_MS)
        return 1.0


def triangle_half_width(y, radius):
    """Half-width of an upward-pointing triangle inscribed in radius at y."""
    apex = -radius
    base = radius * 0.5
    if y < apex or y > base:
        return 0.0
    return (y - apex) / (base - apex) * radius * 0.8660254


def fit_lines(lines, radius, measure, sizes, line_gap=1.05, margin=3):
    """Pick the largest font size whose lines fit inside the triangle.

    measure(text, size) returns the text width. Returns (size, top_y, line_h)
    with top_y relative to the triangle centre. The text block sits just above
    the triangle's base where the triangle is widest.
    """
    base = radius * 0.5
    for size in sizes:
        line_h = size * line_gap
        top = base - margin - line_h * len(lines)
        ok = True
        for i, text in enumerate(lines):
            y = top + i * line_h
            if measure(text, size) > 2 * (triangle_half_width(y, radius) - margin):
                ok = False
                break
        if ok:
            return size, top, line_h
    size = sizes[-1]
    line_h = size * line_gap
    return size, base - margin - line_h * len(lines), line_h
