HOOK = "HOOK"
BIND = "BIND"
SAVE = "SAVE"
WIDTH = "WIDTH"
HEIGHT = "HEIGHT"
OFFSET = "OFFSET"
WHEN = "WHEN"
COMPONENTS = "COMPONENTS"

HEADERS = [HOOK, BIND, SAVE, WIDTH, HEIGHT, OFFSET, WHEN, COMPONENTS]

HOOKED = "HOOKED"


class UserHook:
    def __init__(self,
                 hook=[],
                 bind=[],
                 save=[],
                 cond=None,
                 components=None,
                 target_tex=None,
                 max_downscaling_ratio=None):
        if HOOKED not in bind:
            bind.append(HOOKED)

        self.cond = cond
        self.target_tex = target_tex
        self.max_downscaling_ratio = max_downscaling_ratio

        self.header = {}
        self.header[HOOK] = list(hook)
        self.header[BIND] = list(bind)
        self.header[SAVE] = list(save)
        if components:
            self.headers[COMPONENTS] = [str(components)]
        self.clear_glsl()

    def add_glsl(self, line):
        self.glsl.append(line.strip())

    def clear_glsl(self):
        self.glsl = []
        self.header[WIDTH] = None
        self.header[HEIGHT] = None
        self.header[OFFSET] = None
        self.header[WHEN] = self.cond

    def add_cond(self, cond_str):
        if self.header[WHEN] == None:
            self.header[WHEN] = cond_str
        else:
            # Use boolean AND to apply multiple condition check.
            self.header[WHEN] = "%s %s *" % (self.header[WHEN], cond_str)

    def set_transform(self, mul_x, mul_y, offset_x, offset_y, skippable=False):
        if mul_x != 1:
            self.header[WIDTH] = "%d %s.w *" % (mul_x, HOOKED)
        if mul_y != 1:
            self.header[HEIGHT] = "%d %s.h *" % (mul_y, HOOKED)
        if skippable and self.target_tex and self.max_downscaling_ratio:
            # This step can be independently skipped, add WHEN condition.
            if mul_x > 1:
                self.add_cond(
                    "HOOKED.w %d * %s.w / %f <" %
                    (mul_x, self.target_tex, self.max_downscaling_ratio))
            if mul_y > 1:
                self.add_cond(
                    "HOOKED.h %d * %s.h / %f <" %
                    (mul_y, self.target_tex, self.max_downscaling_ratio))
        self.header[OFFSET] = ["%f %f" % (offset_x, offset_y)]

    def generate(self):
        headers = []
        for name in HEADERS:
            if name in self.header:
                value = self.header[name]
                if isinstance(value, list):
                    for arg in value:
                        headers.append("//!%s %s" % (name, arg.strip()))
                elif isinstance(value, str):
                    headers.append("//!%s %s" % (name, value.strip()))

        return "\n".join(headers + self.glsl + [""])

    def max_components(self):
        s = set(self.header[HOOK])
        s -= {"LUMA", "ALPHA", "ALPHA_SCALED"}
        if len(s) == 0:
            return 1
        s -= {"CHROMA", "CHROMA_SCALED"}
        if len(s) == 0:
            return 2
        return 4
