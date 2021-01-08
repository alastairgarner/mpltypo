#! /usr/bin/env python3

# Decorate all methods
# https://stackoverflow.com/questions/6307761/how-to-decorate-all-functions-of-a-class-without-typing-it-over-and-over-for-eac

# Advanced Annotation
# https://matplotlib.org/3.1.1/api/text_api.html#matplotlib.text.Text

################################################
### Load Dependencies

import numpy as np

from matplotlib import rcParams
import matplotlib.pyplot as plt

from mpltypo import PointFigure

################################################
### Scripting

plt.style.use('./point.mplstyle')

rcParams["font.serif"] = 'Merriweather'
rcParams["font.sans-serif"] = 'Open Sans'
rcParams["font.size"] = 8

### Dots test
fig = plt.figure(figsize=(8,4), FigureClass=PointFigure)
fig.show_dotgrid(system='pica')

# Add axes
axL = fig.add_axes([6,6,12,12], margin=True, projection='pointaxes')

axL.text(-2, 3, 'Title for figure left', size=16, weight='bold', anchor='tl', system='pica', fontfamily='serif')
axL.text(-2, 2, 'Subtitle for figure left', size=10, anchor='tl', system='pica', fontfamily='serif')
axL.text(-2, -4, 'x axis label', size=10, anchor='bl', system='pica')

axL.align_ticklabels(axis='x', y=-2, ha='center', va='baseline')
axL.align_ticklabels(axis='y', x=-2, ha='left')

axR = fig.add_axes([30,6,12,12], margin=True, projection='pointaxes')

axR.text(-2, 3, 'Title for figure right', size=16, weight='bold', anchor='tl', system='pica', fontfamily='serif')
axR.text(-2, 2, 'Subtitle for figure right', size=10, anchor='tl', system='pica', fontfamily='serif')

# Align tick labels
axR.align_ticklabels(axis='x', y=-2, ha='center', va='baseline')
axR.align_ticklabels(axis='y', x=-2, ha='left')

fig.savefig("figs/demo_axes.svg")
fig.savefig("figs/demo_axes.png", dpi=450)

plt.show(block=False)

###############

large_str = "Large fonts"
med_str = "can be perfectly aligned with smaller fonts"
small_str = "as long as the line spacing of each font is a multiple of the smallest line spacing. Here, the line spacing is 6, 12 and 24."

### Dots test
fig = plt.figure(figsize=(4,2), FigureClass=PointFigure)
fig.show_dotgrid(system='pica')

fig.text(2,8,large_str, system='pica', size=20, linespacing=24/20, linewidth=6, va='first_baseline', fontfamily='serif')
fig.text(9,8,med_str, system='pica', size=10, linespacing=12/10, linewidth=6, va='first_baseline', fontfamily='serif')
fig.text(16,8,small_str, system='pica', size=4, linespacing=6/4, linewidth=6, style='italic', va='first_baseline', fontfamily='serif')

fig.text(2,2,'20/24', system='pica', c=(0.8,0,0), size=10, fontfamily='serif')
fig.text(9,2,'10/12', system='pica', c=(0.8,0,0), size=10, fontfamily='serif')
fig.text(16,2,'4/6', system='pica', c=(0.8,0,0), size=10, fontfamily='serif')

fig.line([2,22],[8,8], system='pica', c=(0.8,0.8,0.8), lw=0.5)
fig.line([2,22],[6,6], system='pica', c=(0.8,0.8,0.8), lw=0.5)

fig.savefig("figs/demo_wrap.svg")
fig.savefig("figs/demo_wrap.png", dpi=450)

plt.show(block=False)


###############

plt.style.use('./point.mplstyle')
rcParams["font.size"] = 8

para = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam vitae porta nulla, eu accumsan justo. Aenean nec semper massa, ultrices congue nulla. Sed tempus sed lorem et consectetur. Cras id varius lorem. Aenean sodales eu felis id rhoncus. Vivamus scelerisque vestibulum erat sit amet semper. Nunc id magna a nunc volutpat varius. Mauris et libero a orci tincidunt viverra. Maecenas suscipit turpis erat, eu accumsan nunc laoreet et. Suspendisse dolor augue, mollis vitae hendrerit vel, iaculis vitae ante. Ut pellentesque mollis nisl, ut scelerisque mauris auctor at. Sed a efficitur elit, sit amet egestas augue."
para = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam vitae porta nulla, eu accumsan justo. Aenean nec semper massa, ultrices congue nulla. Sed tempus sed lorem et consectetur. Cras id varius lorem."

### Dots test
fig = plt.figure(figsize=(5,5), FigureClass=PointFigure)
fig.show_dotgrid(system='pica')

axL = fig.add_axes([4, 4, 9, 22], margin=True, projection='pointaxes')
axL.align_ticklabels(axis='x', y=-1, system='pica', va='baseline')
axL.align_ticklabels(axis='y', x=-2, system='pica', ha='left')

axL.text(-2,2, 'Title for tall figure', system='pica', anchor='tl', size=12, weight='bold', fontfamily='serif')
axL.text(-2,1, 'Subtitle is not bold', system='pica', anchor='tl', size=8, fontfamily='serif')

axR = fig.add_axes([17, 17, 9, 9], margin=True, projection='pointaxes')
axR.align_ticklabels(axis='x', y=-1, system='pica', va='baseline')
axR.align_ticklabels(axis='y', x=-2, system='pica', ha='left')

axR.text(-2,2, 'Title for square figure', system='pica', anchor='tl', size=12, weight='bold', fontfamily='serif')
axR.text(-2,1, 'Subtitle is not bold', system='pica', anchor='tl', size=8, fontfamily='serif')

fig.text(17, 12, para, system='pica', fontsize=8, linespacing=12/8, linewidth=9, va='first_baseline', fontfamily='serif')

fig.savefig("figs/demo_mix.svg")
fig.savefig("figs/demo_mix.png", dpi=450)

plt.show(block=False)

###############

