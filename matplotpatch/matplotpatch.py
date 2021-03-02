#! /usr/bin/env python3

################################################

import matplotlib.pyplot as plt

from .base import FigurePlus

################################################
    
def decorator_figure(func):
    
    def wrapper(*args, **kwargs):
        
        if 'FigureClass' not in kwargs:
            print('FigureClass not passed')
            kwargs.update({'FigureClass': FigurePlus})
        else:
            print('FigureClass was passed')
            
        return func(*args, **kwargs)
    
    return wrapper

################################################
#### Constructor wrappers

@decorator_figure
def figure(*args, **kwargs):
    return plt.figure(*args, **kwargs)

@decorator_figure
def subplots(*args, **kwargs):
    return plt.subplots(*args, **kwargs)