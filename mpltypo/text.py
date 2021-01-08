#! /usr/bin/env python3

################################################
### Load Dependencies

import numpy as np

import matplotlib.cbook as cbook
from matplotlib.text import Text
from matplotlib.transforms import Bbox, Affine2D
        
class SpacedText(Text):
    
    def __init__(self, *args, linewidth=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._linewidth = linewidth
        if linewidth:
            self._wrap = True
            
    def set_verticalalignment(self, align):
        """
        Set the vertical alignment

        Parameters
        ----------
        align : {'center', 'top', 'bottom', 'baseline', 'center_baseline'}
        """
        cbook._check_in_list(
            ['top', 'bottom', 'center', 'baseline', 'center_baseline', 'first_baseline'],
            align=align)
        self._verticalalignment = align
        self.stale = True
    
    def _get_wrap_line_width(self):
        """
        Return the maximum line width for wrapping text based on the current
        orientation.
        """
        # AG edita
        if self._linewidth is not None:
            line_width = self._transform.transform([self._linewidth, 0])[0]
            return line_width
        
        x0, y0 = self.get_transform().transform(self.get_position())
        figure_box = self.get_figure().get_window_extent()

        # Calculate available width based on text alignment
        alignment = self.get_horizontalalignment()
        self.set_rotation_mode('anchor')
        rotation = self.get_rotation()

        left = self._get_dist_to_box(rotation, x0, y0, figure_box)
        right = self._get_dist_to_box(
            (180 + rotation) % 360, x0, y0, figure_box)

        if alignment == 'left':
            line_width = left
        elif alignment == 'right':
            line_width = right
        else:
            line_width = 2 * min(left, right)

        return line_width
    
    def _get_layout(self, renderer):
        """
        return the extent (bbox) of the text together with
        multiple-alignment information. Note that it returns an extent
        of a rotated text when necessary.
        """
        key = self.get_prop_tup(renderer=renderer)
        if key in self._cached:
            return self._cached[key]

        thisx, thisy = 0.0, 0.0
        lines = self.get_text().split("\n")  # Ensures lines is not empty.

        ws = []
        hs = []
        xs = []
        ys = []

        # Full vertical extent of font, including ascenders and descenders:
        _, lp_h, lp_d = renderer.get_text_width_height_descent(
            "lp", self._fontproperties,
            ismath="TeX" if self.get_usetex() else False)
        min_dy = (lp_h - lp_d) * self._linespacing
        
        # AG edit
        pixels_per_pt = 1/72*self.figure._dpi
        line_height = (pixels_per_pt * self.get_fontsize()) * self._linespacing

        for i, line in enumerate(lines):
            clean_line, ismath = self._preprocess_math(line)
            if clean_line:
                w, h, d = renderer.get_text_width_height_descent(
                    clean_line, self._fontproperties, ismath=ismath)
            else:
                w = h = d = 0

            # For multiline text, increase the line spacing when the text
            # net-height (excluding baseline) is larger than that of a "l"
            # (e.g., use of superscripts), which seems what TeX does.
            h = max(h, lp_h)
            d = max(d, lp_d)

            ws.append(w)
            hs.append(h)

            # Metrics of the last line that are needed later:
            baseline = (h - d) - thisy

            if i == 0:
                # position at baseline
                thisy = -(h - d)
            else:
                # put baseline a good distance from bottom of previous line
                # thisy -= max(min_dy, (h - d) * self._linespacing)
                
                # AG edit - define change in y independent of font dimensions
                thisy -= line_height - d # reduce by d, because d is minus'd 3 lines later anyway

            xs.append(thisx)  # == 0.
            ys.append(thisy)

            thisy -= d

        # Metrics of the last line that are needed later:
        descent = d

        # Bounding box definition:
        width = max(ws)
        xmin = 0
        xmax = width
        ymax = 0
        ymin = ys[-1] - descent  # baseline of last line minus its descent
        height = ymax - ymin
        yprop = (ys[0]-ymin) / height # AG edit

        # get the rotation matrix
        M = Affine2D().rotate_deg(self.get_rotation())

        # now offset the individual text lines within the box
        malign = self._get_multialignment()
        if malign == 'left':
            offset_layout = [(x, y) for x, y in zip(xs, ys)]
        elif malign == 'center':
            offset_layout = [(x + width / 2 - w / 2, y)
                             for x, y, w in zip(xs, ys, ws)]
        elif malign == 'right':
            offset_layout = [(x + width - w, y)
                             for x, y, w in zip(xs, ys, ws)]

        # the corners of the unrotated bounding box
        corners_horiz = np.array(
            [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)])

        # now rotate the bbox
        corners_rotated = M.transform(corners_horiz)
        # compute the bounds of the rotated box
        xmin = corners_rotated[:, 0].min()
        xmax = corners_rotated[:, 0].max()
        ymin = corners_rotated[:, 1].min()
        ymax = corners_rotated[:, 1].max()
        width = xmax - xmin
        height = ymax - ymin

        # Now move the box to the target position offset the display
        # bbox by alignment
        halign = self._horizontalalignment
        valign = self._verticalalignment

        rotation_mode = self.get_rotation_mode()
        if rotation_mode != "anchor":
            # compute the text location in display coords and the offsets
            # necessary to align the bbox with that location
            if halign == 'center':
                offsetx = (xmin + xmax) / 2
            elif halign == 'right':
                offsetx = xmax
            else:
                offsetx = xmin

            if valign == 'center':
                offsety = (ymin + ymax) / 2
            elif valign == 'top':
                offsety = ymax
            elif valign == 'baseline':
                offsety = ymin + descent
            elif valign == 'first_baseline':
                offsety = ymin  + (yprop * height)
            elif valign == 'center_baseline':
                offsety = ymin + height - baseline / 2.0
            else:
                offsety = ymin
        else:
            xmin1, ymin1 = corners_horiz[0]
            xmax1, ymax1 = corners_horiz[2]

            if halign == 'center':
                offsetx = (xmin1 + xmax1) / 2.0
            elif halign == 'right':
                offsetx = xmax1
            else:
                offsetx = xmin1

            if valign == 'center':
                offsety = (ymin1 + ymax1) / 2.0
            elif valign == 'top':
                offsety = ymax1
            elif valign == 'baseline':
                offsety = ymax1 - baseline
            elif valign == 'center_baseline':
                offsety = ymax1 - baseline / 2.0
            else:
                offsety = ymin1

            offsetx, offsety = M.transform_point((offsetx, offsety))

        xmin -= offsetx
        ymin -= offsety

        bbox = Bbox.from_bounds(xmin, ymin, width, height)

        # now rotate the positions around the first x,y position
        xys = M.transform(offset_layout) - (offsetx, offsety)

        ret = bbox, list(zip(lines, zip(ws, hs), *xys.T)), descent
        self._cached[key] = ret
        return ret
