#! /usr/bin/env python3

################################################

import numpy as np

from matplotlib.figure import Figure
import matplotlib.lines as mlines

from .axes import decorator_axes
from .text import TextMuliColor
from .transforms import transform_factory, decorator_custom_transform

################################################


class FigurePlus(Figure):
    """
    Docstring
    """
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._dotgrid = None     

    @decorator_axes
    def add_axes(self, *args, **kwargs):
        return super().add_axes(*args, **kwargs)
        
    @decorator_axes
    def add_subplot(self, *args, **kwargs):
        return super().add_subplot(*args, **kwargs)
    
    @decorator_custom_transform
    def text(self, *args, **kwargs):
        return super().text(*args, **kwargs)
    
    @decorator_custom_transform
    def line(self, *args, **kwargs):
        
        line = mlines.Line2D(*args, **kwargs)
        self.lines.append(line)
        
        return line
    
    def text_multicolor(self, *args, **kwargs):
        """
        Docstring
        """
        
        kwargs.update(parent=self)
        text = TextMuliColor(*args, **kwargs)
        return text.draw()

    def draw_dotgrid(self, system='inch', interval=1, **kwargs):
        
        kwargs = {
            'c': (0.8,0.8,0.8),
            'lw': 0,
            'marker': '.',
            'ms': 1,
            'zorder': -1,
            **kwargs,
        }
        
        trans = transform_factory(self, system=system)

        bbox = self.bbox._points
        coords = trans.inverted().transform(bbox)
        string = f"""Transformation has units: 
            (Horizontal) {coords[0,0]} --> {coords[1,0]} 
            (Vertical)   {coords[0,1]} --> {coords[1,1]}"""
        print(string)

        x = np.arange(*coords[:,0], interval)[1:]
        y = np.arange(*coords[:,1], interval)[1:]

        line_x = np.tile(x,len(y))
        line_y = np.repeat(y, len(x))

        self._dotgrid = mlines.Line2D(line_x, line_y, transform=trans, figure=self, **kwargs)
        self.lines.append(self._dotgrid)
        self.hide_dotgrid()
        
    def show_dotgrid(self, *args, **kwargs):
        if self._dotgrid is None:
            self.draw_dotgrid(*args, **kwargs)
        
        self._dotgrid.set_visible(True)
        
    def hide_dotgrid(self):
        self._dotgrid.set_visible(False)
    
    
