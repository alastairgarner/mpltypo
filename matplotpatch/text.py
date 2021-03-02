#! /usr/bin/env python3

# https://matplotlib.org/stable/gallery/text_labels_and_annotations/rainbow_text.html

################################################
### Load Dependencies

import re
import numpy as np

import matplotlib.cbook as cbook
from matplotlib.axes import Axes
from matplotlib.figure import  Figure
from matplotlib.text import Text
from matplotlib.transforms import Bbox, Affine2D
from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, HPacker

from .transforms import transform_factory

class TextPlus(Text):
    
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
        # AG edit
        if self._linewidth is not None:
            points = self._transform.transform([[self._linewidth,0],[0,0]])
            line_width = points[0][0] - points[1][0]
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

##########################################

class TextMuliColor(object):
    
    def __init__(self, x=None, y=None, string=None, flag='[:]', highlight={}, linespacing=1.2, parent=None, system='axes', anchor='bl', **kwargs):
        
        self.parent = parent
        if isinstance(parent, Axes):
            self.figure = parent.figure
        elif isinstance(parent, Figure):
            self.figure = parent
        else:
            raise Exception('Object passed must be a Figure or Axes instance')
        
        self.string = string
        assert isinstance(flag,str) & (len(flag) == 3)
        self.flag = flag
        
        self.x = x
        self.y = y
        
        self.linespacing = linespacing
        self.base = kwargs
        self.highlight = highlight
        
        self.system = system
        self.anchor = anchor
        self.transform = self._generate_transform()

        self.renderer = self.figure.canvas.get_renderer()
        self.boxes = None
        self.children = None
        
        self._generate_lines()

    def _generate_transform(self):
        
        self.transform = transform_factory(self.parent, system=self.system, anchor=self.anchor)

        return self.transform
    
    def _get_default_fontproperties(self):
        """Docstring"""
        
        default_text = TextPlus(0,0,'', **self.base)
        fp = default_text._fontproperties
        del(default_text)
        
        return fp

    def _generate_lines(self):
        """
        Docstring
        """
        opn,sep,clo = self.flag

        expr = f"([\{opn}].*?[\{clo}])"
        parts = re.split(expr, self.string)

        expr = f"[\{opn}](.*?)[\{sep}](.*?)[\{clo}]"
        lines = [[]]
        n = 0
        for part in parts:
            opts = self.base.copy()
            
            p = re.match(expr,part)
            if p:
                part,fmt = p.groups()
                fmt = int(fmt)
                opts.update(self.highlight[fmt])
                
            rows = part.split('\n')
            for i,row in enumerate(rows):
                if i != 0:
                    lines.append([])
                    n += 1
                
                txt = TextArea(row, textprops=opts)
                lines[n].append(txt)
                
        boxes  = []
        for line in lines:
            box = HPacker(children=line, align="baseline", pad=0, sep=0)
            boxes.append(box)
            
        self.boxes = boxes
        return boxes
    
    def _get_xy_px(self,x,y):
        
        # Get default font properties and text descent, in px
        fp = self._get_default_fontproperties()
        _,_,descent = self.renderer.get_text_width_height_descent("lp", fp, ismath=False)

        # Determine the x,y position in display coordinates
        xy_px = self.transform.transform([x, y]) - [0, descent]
    
        return xy_px
    
    def _get_y_increment(self):
        
        fp = self._get_default_fontproperties()

        # determine line increment, in px
        dpi = self.figure._dpi
        fs = fp.get_size()
        return (fs*self.linespacing) * (dpi/72)
    
    def _get_line_max_extent(self):

        fp = self._get_default_fontproperties()
        
        width = height = descent = 0
        for line in self.string.split('\n'):
            w,h,d = self.renderer.get_text_width_height_descent(line, fp, ismath=False)
            
            width = max(width,w)
            height = max(height,h)
            descent = max(descent,d)
        
        return width,height,descent
    
    def draw(self, x=None, y=None):
        """
        Docstring
        """
        # https://stackoverflow.com/questions/33159134/matplotlib-y-axis-label-with-multiple-colors
        
        if x is None:
            x = self.x
        if y is None:
            y = self.y
        if (x is None) and (y is None):
            raise Exception('No x,y arguments passed!')
        
        xy_px = self._get_xy_px(x,y)
        y_incr_px = self._get_y_increment()
        boxes = self.boxes

        for box in boxes[::-1]:
            x,y = self.transform.inverted().transform(xy_px)
            anchored_xbox = AnchoredOffsetbox(loc=3, child=box, pad=0, frameon=False,
                                        bbox_to_anchor=(x,y), bbox_transform=self.transform, borderpad=0)
            self.parent.add_artist(anchored_xbox)
            xy_px[1] += y_incr_px
            
        self.children = [textarea.get_children() for box in boxes for textarea in box.get_children()]
        
        return self.children