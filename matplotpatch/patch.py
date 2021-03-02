#! /usr/bin/env python3

################################################

import importlib
import sys

import matplotlib.pyplot as plt
import matplotlib.text as mtext
import matplotlib.axes as maxes
import matplotlib.figure as mfigure

from .figure import FigurePlus
from .axes import AxesPlus
from .text import TextPlus

################################################
    
def decorator_figure(func):
    
    def wrapper(*args, **kwargs):
        
        if 'FigureClass' not in kwargs:
            kwargs.update({'FigureClass': FigurePlus})
            
        return func(*args, **kwargs)
    
    return wrapper

################################################
#### Constructor wrappers


def patch(pyplot=None):
    """
    Docstring
    """
    
    if pyplot is None:
        pyplot = plt

    elif hasattr(pyplot,'__name__'):
        if pyplot.__name__ != 'matplotlib.pyplot':
            print("Module passed to 'patch' was not matplotlib.pyplot")
            return

    # patch the classes
    mtext.Text = TextPlus
    
    # mfigure.Figure = FigurePlus
    # maxes.Axes = AxesPlus

    # Reload modules (if already loaded) that are
    # dependent on matplotlib.text.Text
    modules = ['axes', 'figure']
    for mod in modules:
        mod = f'matplotlib.{mod}'
        if mod in sys.modules.keys():
            importlib.reload(sys.modules[mod])
            
    # Patch the pyplot module with new constructor methods
    pyplot.figure = decorator_figure(pyplot.figure)
    
    # methods_to_decorate = ['figure', 'subplots']
    # for method in methods_to_decorate:
    #     func = getattr(pyplot,method)
    #     setattr(pyplot,method,decorator_figure(func))
        
    return pyplot

