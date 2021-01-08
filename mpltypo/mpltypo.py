#! /usr/bin/env python3

# Decorate all methods
# https://stackoverflow.com/questions/6307761/how-to-decorate-all-functions-of-a-class-without-typing-it-over-and-over-for-eac

################################################
### Load Dependencies
import sys
import importlib
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox, BboxTransformTo, BboxTransformFrom, blended_transform_factory, CompositeGenericTransform
import matplotlib.lines as lines

from .text import SpacedText

################################################
# Here lies a "monkey patch" for the Text class (matplotlib.text.Text)
# Essentially, you redefine the Text class, with SpacedText.
# Then you reload the modules that depend on Text
# (axes, figure, pyplot), so they re-initialise
# with the updated version of the class.
# https://medium.com/@chipiga86/python-monkey-patching-like-a-boss-87d7ddb8098e

# fyi, I'm sure there's probaby a better way to do this,
# I just haven't found it yet.

# Redefine matplotlib.text.Text
from matplotlib import text
text.Text = SpacedText

# Reload modules (if already loaded) that are
# dependent on matplotlib.text.Text
modules = ['axes', 'figure', 'pyplot']
for mod in modules:
    mod = f'matplotlib.{mod}'
    if mod in sys.modules.keys():
        importlib.reload(sys.modules[mod])
        
################################################
### Classes

class PointTransform(CompositeGenericTransform):
    """
    Create a new imperial-unit coordinate system around a given anchor.
    """

    def __init__(self, object=None, anchor='bl', spacing=12):
        
        if isinstance(object, plt.Figure):
            fig = object
        elif hasattr(object,'figure'):
            fig = object.figure
        else:
            raise Exception('Cannot find figure from object')
                         
        self.obj = object
        self.fig = fig
        self.spacing = spacing
        self.anchor = anchor
        
        self.fig_pos = fig.bbox._points
        self.obj_pos = self.get_object_position()
        
        bbox = self.get_bbox()       
        super().__init__(BboxTransformFrom(bbox), self.fig.transFigure)

    def get_object_position(self):
        """docstring"""
        
        obj_pos = self.fig_pos
            
        if isinstance(self.obj, plt.Axes):
            axis_position = self.obj.get_position()
            obj_pos = self.fig.transFigure.transform(axis_position)
        
        return obj_pos
    
    def get_bbox(self):
        
        anchors = {
            'bl' : lambda x: x[0],
            'tl' : lambda x: x.diagonal(),
            'tr' : lambda x: x[1],
            'br' : lambda x: x.flatten()[[2,1]],
        }

        scale = self.fig._dpi / (72 / self.spacing)
        points = (self.fig_pos - anchors[self.anchor](self.obj_pos)) / scale
        bbox =  Bbox(points)
        return bbox
    

class GetTransform:
        
    def __new__(cls, object=None, system='figure', anchor='bl', spacing=12):
                
        fig = None
        ob = None
        
        # Deal with arguments        
        if object is None:
            fig = plt.gcf()
            ob = fig
        elif isinstance(object, plt.Figure):
            fig = object
            ob = fig
        elif hasattr(object, 'figure'):
            ob = object
            fig = object.figure
        else:
            raise Exception('Invalid object passed')
        
        if isinstance(system, str):
            system = [system]
        n = min(2, len(system))
        
        transforms = []
        for i in range(n):
            syst = system[i]
            
            if syst == 'figure':
                trans = fig.transFigure
            elif syst == 'axes':
                trans = ob.transAxes
            elif syst == 'data':
                trans = ob.transData
            elif syst == 'pica':
                trans = PointTransform(object=ob, anchor=anchor, spacing=12)
            elif syst == 'inch':
                trans = PointTransform(object=ob, anchor=anchor, spacing=72)
            elif syst == 'point':
                trans = PointTransform(object=ob, anchor=anchor, spacing=1)
            elif syst == 'unit':
                trans = PointTransform(object=ob, anchor=anchor, spacing=spacing)
            else:
                raise Exception('Incorrect arguments')
            
            transforms.append(trans)

        if len(transforms) == 2:
            transform = blended_transform_factory(*transforms)
        elif len(transforms) == 1:
            transform = transforms[0]
        
        return transform
    
class PointAxes(plt.Axes):
    """
    Axes wrapper for easy application of transforms to text/plot methods.
    """
    
    name = "pointaxes"

    _methods_to_decorate = [
        'text', 'plot',
    ]   
         
    def __init__(self, fig, rect, spacing=12, margin=False, **kwargs):
        
        if margin:
            if 'figure' in kwargs.keys():
                fig = kwargs['figure']
            else:
                fig = plt.gcf()
                            
            trans = GetTransform(object=fig, system='unit', spacing=spacing)
            
            margins = np.reshape(rect,(-1,2))
            bbox = fig.bbox._points[1]
            points = trans.transform(margins)
            rect = points.flatten() / np.tile(bbox,2)
        
        super().__init__(fig, rect, **kwargs)
        
        self._saved_transforms = []

        self._decorate_methods()        
    
    def decorator(self, func):
                
        def wrapper(*args, system='axes', anchor='bl', spacing=12, **kwargs):
            
            trans = GetTransform(object=self, system=system, anchor=anchor, spacing=spacing)
            self._saved_transforms.append(trans)
            
            handles = func(*args, **kwargs, transform=trans)
            # print(f'Ran {func.__name__} function')

            return handles
        
        return wrapper
        
    def _decorate_methods(self):
        """Decorate methods with the transformation wrapper"""
        
        for method in self._methods_to_decorate:
            fn = getattr(self, method)
            setattr(self, method, self.decorator(fn))
            
    def align_ticklabels(self, axis=None, system='pica', anchor='bl', spacing=12, **kwargs):
        """Docstring"""

        if axis == 'x':
            trans = GetTransform(self, system=('data', system), anchor=anchor, spacing=spacing)
        elif axis == 'y':
            trans = GetTransform(self, system=(system, 'data'), anchor=anchor, spacing=spacing)
        else:
            raise Exception('Please specify axis')

        kwargs.update(transform=trans)

        axis_handle = getattr(self, axis.lower()+'axis')    

        locs = axis_handle.get_ticklocs()
        strings = [str(round(loc,2)) for loc in locs]
        axis_handle.set_ticklabels(strings, **kwargs)

import matplotlib.projections as proj
proj.register_projection(PointAxes)


class PointFigure(plt.Figure):
    
    _methods_to_decorate = [
        'text',
    ]   

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._saved_transforms = []
        self._dotgrid = None

        self._decorate_methods()        

    def decorator(self, func):
                
        def wrapper(*args, system='figure', anchor='bl', spacing=12, **kwargs):
            
            trans = GetTransform(object=self, system=system, anchor=anchor, spacing=spacing)
            self._saved_transforms.append(trans)
            
            handles = func(*args, **kwargs, transform=trans)
            # print(f'Ran {func.__name__} function')

            return handles
        
        return wrapper
        
    def _decorate_methods(self):
        """Decorate methods with the transformation wrapper"""
        
        for method in self._methods_to_decorate:
            fn = getattr(self, method)
            setattr(self, method, self.decorator(fn))

    def draw_dotgrid(self, system='inch', interval=1, **kwargs):
        
        kwargs = {
            'c': (0.8,0.8,0.8),
            'lw': 0,
            'marker': '.',
            'ms': 1,
            'zorder': -1,
            **kwargs,
        }
        
        trans = GetTransform(self, system=system)

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

        self._dotgrid = lines.Line2D(line_x, line_y, transform=trans, figure=self, **kwargs)
        self.lines.append(self._dotgrid)
        self.hide_dotgrid()
        
    def show_dotgrid(self, *args, **kwargs):
        if self._dotgrid is None:
            self.draw_dotgrid(*args, **kwargs)
        
        self._dotgrid.set_visible(True)
        
    def hide_dotgrid(self):
        self._dotgrid.set_visible(False)
        
    def line(self, *args, system='pica', anchor='bl', spacing=12, **kwargs):
        
        trans = GetTransform(object=self, system=system, anchor=anchor, spacing=spacing)
            
        line = lines.Line2D(*args, transform=trans, **kwargs)
        self.lines.append(line)
        
        return line

# class TypoTransform(CompositeGenericTransform):
#     """
#     Create a new imperial-unit coordinate system around a given anchor.
#     """

#     _anchor_funcs = {
#         'bl' : lambda f,a: (f-a[0]),
#         'tl' : lambda f,a: (f-a.diagonal()),
#         'tr' : lambda f,a: (f-a[1]),
#         'br' : lambda f,a: (f-a.flatten()[[2,1]]),
#     }

#     def __init__(self, figure=None, axes=None, anchor='bl', spacing=12, bbox=None):
        
#         if figure is None:
#             if axes is None:
#                 raise Exception('No figure specified')
#             figure = axes.figure
        
#         elif isinstance(figure, plt.Axes):
#             axes = figure
#             figure = axes.figure
        
#         self._ax = axes
#         self._fig = figure
#         self._spacing = spacing
        
#         fpos,apos = self._get_positions()
#         if bbox is not None:
#             apos = bbox
            
#         self._anchor = self._anchor_funcs[anchor](fpos, apos)
                
#         a,b = self._trans()
#         super().__init__(a,b)
        
#     def _get_positions(self):
#         """docstring"""
        
#         fpos = self._fig.bbox._points
#         apos = fpos
        
#         if self._ax is not None:
#             axis_position = self._ax.get_position()
#             apos = self._fig.transFigure.transform(axis_position)
        
#         return fpos,apos
            
#     def _trans(self):
#         """docstring"""
        
#         scale = self._fig._dpi / (72 / self._spacing)
#         points = self._anchor / scale
#         bbox = Bbox(points)
#         return BboxTransformFrom(bbox), self._fig.transFigure

# class TransformCompiler(object):
#     """
#     Create custom single/blended transform across coordinate systems.
#     """
    
#     def __init__(self, figure=None, axes=None, system='figure', anchor='bl', spacing=12):
        
#         if figure is None:
#             if axes is None:
#                 raise Exception('No figure specified')
                
#             figure = axes.figure
        
#         self.ax = axes
#         self.fig = figure
#         self.system = system
#         self.anchor = anchor
#         self.spacing = spacing
                
#         self._generate_types()
        
#         self.trans = None
#         self._generate_transform()
                
#     def _generate_types(self):
        
#         self.types = {
#             'figure': getattr(self.fig, 'transFigure', None),
#             'axes': getattr(self.ax, 'TransformAxes', None),
#             'data': getattr(self.ax, 'transData', None),
#             'inch': TypoTransform(figure=self.fig, axes=self.ax, anchor=self.anchor, spacing=72),
#             'pica': TypoTransform(figure=self.fig, axes=self.ax, anchor=self.anchor, spacing=12),
#             'point': TypoTransform(figure=self.fig, axes=self.ax, anchor=self.anchor, spacing=1),
#             'unit': TypoTransform(figure=self.fig, axes=self.ax, anchor=self.anchor, spacing=self.spacing),
#         }
        
#     def _generate_transform(self):
        
#         system = self.system
#         types = self.types

#         if isinstance(system, str):
#             trans = types[system]
#         else:
#             h,v,*_ = system
#             trans = blended_transform_factory(types[h], types[v])

#         self.trans = trans

# class TransformAxes(plt.Axes):
#     """
#     Axes wrapper for easy application of transforms to text/plot methods.
#     """
    
#     name = "transformaxes"

#     _methods_to_decorate = [
#         'text', 'plot',
#     ]   
         
#     def __init__(self, *args, spacing=12, margins=None, **kwargs):
        
#         if margins is not None:
#             if 'figure' in kwargs.keys():
#                 fig = kwargs['figure']
#             else:
#                 fig = plt.gcf()
                
#             trans = TransformCompiler(figure=fig, system='unit', spacing=spacing).trans
            
#             bbox = fig.bbox._points[1]
#             points = trans.transform(margins)
#             rect = points / np.tile(bbox,2)
            
#             kwargs.update(rect=list(rect))
        
#         super().__init__(*args, **kwargs)
        
#         self._saved_transforms = []

#         self._decorate_methods()        
    
#     def decorator(self, func):
                
#         def wrapper(*args, system='axes', anchor='bl', spacing=12, **kwargs):
            
#             transformer = TransformCompiler(axes=self, system=system, anchor=anchor, spacing=spacing)
#             trans = transformer.trans
            
#             self._saved_transforms.append(trans)
            
#             handles = func(*args, **kwargs, transform=trans)
#             print(f'Ran {func.__name__} function')

#             return handles
        
#         return wrapper
        
#     def _decorate_methods(self):
#         """Decorate methods with the transformation wrapper"""
        
#         for method in self._methods_to_decorate:
#             fn = getattr(self, method)
#             setattr(self, method, self.decorator(fn))
