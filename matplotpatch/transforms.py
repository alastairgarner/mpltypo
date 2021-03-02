#! /usr/bin/env python3

################################################
### Load Dependencies
import re

import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox, BboxTransformFrom, blended_transform_factory, CompositeGenericTransform

################################################
### Classes

class PointTransform(CompositeGenericTransform):
    """
    Create a new imperial-unit coordinate system around a given anchor.
    """

    def __init__(self, object=None, anchor:str='bl', system:str='12pt'):
        
        if isinstance(object, plt.Figure):
            fig = object
        elif hasattr(object,'figure'):
            fig = object.figure
        else:
            raise Exception('Cannot find figure from object')
                         
        self.obj = object
        self.fig = fig
        self.system = str(system)
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

        # scale = self.fig._dpi / (72 / self.system)
        scale = self.get_scale()
        points = (self.fig_pos - anchors[self.anchor](self.obj_pos)) / scale
        bbox =  Bbox(points)
        return bbox
    
    def get_scale(self):
        
        string = self.system
        dpi = self.fig._dpi
        
        res = re.match("([0-9.]+)(\w+)", string)
        if res is not None:
            spacing,unit,*_ = res.groups()
            spacing = float(spacing)
            
            if unit in ['pt', 'point', 'points']:
                val = dpi * spacing / 72
            elif unit in ['pc','pica','picas']:
                val = dpi * spacing / 6
            elif unit in ['in', 'inch', 'inches']:
                val = dpi * spacing
            elif unit in ['mm']:
                val = dpi * spacing / 25.4
            elif unit in ['cm']:
                val = dpi * spacing / 2.54
            else:
                raise Exception(f"'{string}' is not a valid argument for spacing")
            
        return val

def transform_factory(object=None, system='figure', anchor='bl'):
    
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
        elif syst in ['ax','axes','axis']:
            trans = ob.transAxes
        elif syst == 'data':
            trans = ob.transData
        elif syst in ['pc','pica','picas']:
            trans = PointTransform(object=ob, anchor=anchor, system='12pt')
        elif syst in ['in', 'inch', 'inches']:
            trans = PointTransform(object=ob, anchor=anchor, system='1in')
        elif syst in ['pt', 'point', 'points']:
            trans = PointTransform(object=ob, anchor=anchor, system='1pt')
        else:
            trans = PointTransform(object=ob, anchor=anchor, system=syst)
        
        transforms.append(trans)

    if len(transforms) == 2:
        transform = blended_transform_factory(*transforms)
    elif len(transforms) == 1:
        transform = transforms[0]
        
    return transform
    
def decorator_custom_transform(func):
                
    def wrapper(self, *args, system=None, anchor='bl', **kwargs):
        
        if system is not None:
            trans = transform_factory(object=self, system=system, anchor=anchor)
            kwargs.update({'transform': trans})
        
        # output = func(self, *args, **kwargs, transform=trans)
        output = func(self, *args, **kwargs)
        # print(f'Ran {func.__name__} function')

        return output
    
    return wrapper