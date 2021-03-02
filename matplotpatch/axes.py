#! /usr/bin/env python3

################################################
### Load Dependencies

import numpy as np

from matplotlib.axes import Axes
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, HPacker, VPacker

from .text import TextPlus, TextMuliColor
from .transforms import transform_factory, decorator_custom_transform

################################################

class AxesPlus(Axes):
    """
    
    """
    name = "axesplus"
    
    def __init__(self, fig, rect, system=None, **kwargs):
        
        if system is not None:
            if 'figure' in kwargs.keys():
                fig = kwargs['figure']
            else:
                fig = plt.gcf()
                            
            trans = transform_factory(object=fig, system=system)
            
            margins = np.reshape(rect,(-1,2))
            bbox = fig.bbox._points[1]
            points = trans.transform(margins)
            rect = points.flatten() / np.tile(bbox,2)
        
        super().__init__(fig, rect, **kwargs)
        
    @decorator_custom_transform
    def plot(self, *args, **kwargs):
        return super().plot(*args, **kwargs)

    @decorator_custom_transform
    def text(self, *args, **kwargs):
        return super().text(*args, **kwargs)

    def set_yticklabel_pad(self, pad=0, system='pt', **kwargs):
        
        tickdir = self.yaxis.majorTicks[0]._tickdir

        ticklen = 0
        if tickdir != 'in':
            ticklen = self.yaxis.majorTicks[0]._size
        
        transform = transform_factory(self, system=system)
        coords = transform.transform([0,0]) - transform.transform([pad,0])
        pad_pt,_ = (coords * 72) / self.figure.dpi
        
        offset = pad_pt - ticklen
        self.tick_params(axis='y', pad=offset)
        
        for label in self.get_yticklabels():
            label.update(kwargs)

    def set_xticklabel_pad(self, pad=0, system='pt', va='baseline', **kwargs):
    
        tickdir = self.xaxis.majorTicks[0]._tickdir

        ticklen = 0
        if tickdir != 'in':
            ticklen = self.xaxis.majorTicks[0]._size
        
        transform = transform_factory(self, system=system)
        coords = transform.transform([0,0]) - transform.transform([0,pad])
        _,pad_pt = (coords * 72) / self.figure.dpi
        
        offset = pad_pt - ticklen
        self.tick_params(axis='x', pad=offset)
        
        for label in self.get_xticklabels():
            label.update(dict(va=va, **kwargs))
    
    def inset_yticklabels(self):
        
        self.set_yticklabel_pad(pad=0, ha='left')
        
    def inset_xticklabels(self):
        
        self.set_xticklabel_pad(pad=0, va='bottom')
        
    def set_margin(self, rect=None, system='axes', left=None, bottom=None, right=None, top=None):
        """
        Set the margins around the axes.
        """
        # Handle arguments
        exception = Exception("'rect' must be a list of length 2 or 4")
        if rect:
            if not isinstance(rect,list):
                raise exception
            
            if len(rect) == 4:
                left,bottom,right,top = rect
            elif len(rect) == 2:
                left,bottom = rect
                right,top = left,bottom
            else:
                raise exception
        
        # Get the current data limits
        datalims = np.array([
            self.xaxis.get_data_interval(),
            self.yaxis.get_data_interval()
        ]).T
        drange = np.diff(datalims,1,0)

        arr = np.array([left,bottom,right,top], dtype=float).reshape(-1,2)
        tf = np.isnan(arr)
        arr[tf] = 0

        # Calculate the margins as a proportion of axes area
        trans = transform_factory(self, system=system)
        ax_pos = self.get_position()._points
        width_height_px = self.figure.transFigure.transform(np.diff(ax_pos,1,0))
        pad_px = trans.transform(arr) - trans.transform([[0,0],[0,0]])
        margin_prop = pad_px / width_height_px

        # Translate margin proportions to data coordinate system
        box_prop = 1 / (1 - margin_prop.sum(0))
        prange = box_prop * drange
        margin_data = margin_prop * prange

        # Calculate new axis limits, exclusive to those specified in method arguments
        lims_old = np.array([self.get_xlim(),self.get_ylim()]).T
        lims_new = datalims + margin_data*[[-1],[1]]
        lims_new[tf] = lims_old[tf]

        # Set new aces limits
        self.set_xlim(lims_new[:,0])
        self.set_ylim(lims_new[:,1])

    def text_multicolor(self, *args, **kwargs):
        """
        Docstring
        """
        
        kwargs.update(parent=self)
        text = TextMuliColor(*args, **kwargs)
        return text.draw()

import matplotlib.projections as proj
proj.register_projection(AxesPlus)

################################################

def decorator_axes(func):

    def wrapper(self, *args, **kwargs):
        
        if 'projection' not in kwargs.keys():
            kwargs.update({'projection': 'axesplus'})
        return func(self, *args, **kwargs)
    
    return wrapper
