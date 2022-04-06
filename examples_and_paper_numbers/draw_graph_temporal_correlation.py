# script used to draw the graph from Figure 4, where the temporal
# correlation between the location of fixations and the mentions of 
# abnormalities. The script generate_temporal_correlation_numbers.py has to be
# run before running this script

import numpy as np
import matplotlib
matplotlib.use('Agg')
matplotlib.use("pgf")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import AutoMinorLocator, LinearLocator
import math
from matplotlib import rc
from matplotlib.backends.backend_pgf import FigureCanvasPgf
import matplotlib.font_manager

matplotlib.backend_bases.register_backend('pdf', FigureCanvasPgf)

pgf_with_custom_preamble = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica"],
    "text.usetex": False,
    "pgf.rcfonts": True, 
    "pgf.texsystem" : 'pdflatex'
}
rc('font', **{'family': 'sans-serif', 'serif': ['Helvetica']})
rc('text', usetex=False)
matplotlib.rcParams.update(pgf_with_custom_preamble)

def plot_robust(xt, yt, yts_min, yts_max,nta, xs, ys, yss_min, yss_max, nsa, filepath=None):
    colourWheel =['#99cc0033',
            '#008080',
            '#333399',
            '#993366',
            '#ff0000',
            '#ff9900']
    
    #repeat data in the beginning and end of arrays such that bins plotted with
    # the step function show full bins instead of half bins in the beginning 
    # and the end of ranges
    xt = np.insert(xt,0,0.)
    xt = np.insert(xt,len(xt),xt[-1]+xt[1])
    yt = np.insert(yt,0,yt[0])
    yt = np.insert(yt,len(yt),yt[-1])
    nta = np.insert(nta,0,nta[0])
    nta = np.insert(nta,len(nta),nta[-1])
    xs = np.insert(xs,0,0.)
    xs = np.insert(xs,len(xs),xs[-1]+xs[1])
    nsa = np.insert(nsa,0,nsa[0])
    nsa = np.insert(nsa,len(nsa),nsa[-1])
    ys = np.insert(ys,0,ys[0])
    ys = np.insert(ys,len(ys),ys[-1])
    yts_min = np.insert(yts_min,0,yts_min[0])
    yts_min = np.insert(yts_min,len(yts_min),yts_min[-1])
    yts_max = np.insert(yts_max,0,yts_max[0])
    yts_max = np.insert(yts_max,len(yts_max),yts_max[-1])
    yss_min = np.insert(yss_min,0,yss_min[0])
    yss_min = np.insert(yss_min,len(yss_min),yss_min[-1])
    yss_max = np.insert(yss_max,0,yss_max[0])
    yss_max = np.insert(yss_max,len(yss_max),yss_max[-1])
    
    
    plt.style.use('./plotstyle.mplstyle')
    plt.close('all')
    fig, ax = plt.subplots(figsize=(20*0.65, 10*0.65), dpi=600)
    fig.set_size_inches(6.94, 3.47)
    alphaVal = 0.5
    ax.set_xlabel('Time before mention (s)')
    plt.ylabel('Fixations inside ellipse (\%)')
    ax.set_ylim(0,70)    
    ax.set_xlim(0,60)     
    
    ax2 = ax.twiny()
    ax2.set_xlim(0,12) 
    ax2.set_xlabel('Sentence units before mention')
    
    ax3 = ax.twinx()
    ax3.set_ylabel('Total fixations')
    ax4 = ax3.twiny()
    ax4.sharex(ax2) 
    ax4.set_ylim(0,2800)   
    ax4.yaxis.set_major_locator(LinearLocator(8)) 
    lns5 = ax3.step(xt, nta,
                    color=colourWheel[4],
                    alpha=alphaVal,zorder=1,linewidth=1,
                    where = 'mid', dashes = (2.5,1,1,2,1,1))
    lns6 = ax4.step(xs, nsa,
                    color=colourWheel[3],
                    alpha=alphaVal,zorder=1,linewidth=1,
                    where = 'mid', linestyle = 'dotted')
    
    lns2 = ax.fill_between(xt, yts_min*100, yts_max*100, step = 'mid', 
                        color=colourWheel[0], alpha = 0.1, hatch = 'O')
    lns4 = ax2.fill_between(xs, yss_min*100, yss_max*100, step = 'mid',
                            color=colourWheel[1], alpha = 0.1, hatch = 'x')
    lns1 = ax.step(xt, 100*yt, color=colourWheel[0],
                    alpha=alphaVal,zorder=1,linewidth=1.5,
                    where = 'mid')
    lns3 = ax2.step(xs, 100*ys, color=colourWheel[1],
                    alpha=alphaVal,zorder=1,linewidth=1.5,
                    where = 'mid', linestyle = '--', dashes=(5, 1))
    
    legend = ax.legend(
        [(lns2, lns1[0]),(lns4, lns3[0]),(lns5[0],),(lns6[0],)],
        ['Time', 'Sentence', 'Total fixations - Time', 'Total fixations - Sentence'],
        loc=0, labelspacing=1.5, borderpad=1, ncol=2)
    ax.xaxis.set_tick_params(width=1)
    ax.yaxis.set_tick_params(width=1)
    ax2.xaxis.set_tick_params(width=1)
    ax2.yaxis.set_tick_params(width=1)
    
    #change the size of the confidence interval patches in the legend to make 
    # the backgroung pattern more visible
    for handle in legend.get_patches():
        height = handle.get_height()
        print(height)
        new_height = 15
        handle.set_height(new_height)
        handle.set_y((height-new_height)/2)
    
    ax.grid(zorder=-100)
    ax.set_axisbelow(True)
    plt.savefig(filepath, bbox_inches = 'tight', pad_inches = 0, dpi=600)

xt = np.load('xt.npy')
yt = np.load('yt.npy')
nta = np.load('nta.npy')
xs = np.load('xs.npy')
ys = np.load('ys.npy')
nsa = np.load('nsa.npy')
yts = np.load('yts.npy')
yss = np.load('yss.npy')

#print bin widths and location of peaks
print(xt[0]*2)
print(xt[np.argmax(yt)], (xt[np.argmax(yt)])-xt[0], (xt[np.argmax(yt)])+xt[0])
print(xs[0]*2)
print(xs[np.argmax(ys)],xs[np.argmax(ys)]-xs[0],xs[np.argmax(ys)]+xs[0])

plot_robust(xt, yt, np.percentile(np.array(yts), 2.5, axis = 0), 
                    np.percentile(np.array(yts), 97.5, axis = 0), nta, 
            xs, ys, np.percentile(np.array(yss), 2.5, axis = 0), 
                    np.percentile(np.array(yss), 97.5, axis = 0), nsa,
             filepath='plot_graph_delay.pdf')

