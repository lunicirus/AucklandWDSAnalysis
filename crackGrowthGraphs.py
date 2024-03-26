import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cmlib
from matplotlib.ticker import AutoMinorLocator, MultipleLocator

def graphsAllGrowth(fileName:str,times:list[int],Hdx:list[float],lengx:list[float],flowx:list[float],maxPre:float):
    """
       Graphs the development with time of the strength index, flowrate at maximum pressure, and length of a crack. 
       It also graphs the maximum pressure of a system for reference. 
    Args:
        fileName (str): File name to be used for the graph image.
        times (list[int]): Time in days. X axis of the graph. 
        Hdx (list[float]): Strength indexes of the crack (m).
        lengx (list[float]): Lengths of the crack (m).
        flowx (list[float]): Flow rate (l/h) produced with the maximum pressure. 
    """    
    col = [ cmlib.get_cmap('viridis')(x) for x in np.linspace(0, 1, 3)]

    fig, ax = plt.subplots(1,figsize=(10, 8))
    ax2=ax.twinx()
    ax3=ax.twinx()
    
    ax3.spines['right'].set_position(("axes", 1.15))

    timesYear = [x / 365 for x in times]

    ax.plot(timesYear,Hdx,label="Pressure index",marker=".",color="m") 
    ax2.plot(timesYear,lengx,label="Crack length",marker=".",color= col[2])  
    ax3.plot(timesYear,flowx,label="Leak flowrate",marker=".",color='deepskyblue')  
    ax.hlines([maxPre],0,100,label="System maximum pressure",linewidth=2,color='r')

    #title = ('Pipe D='+ str(diam) + ' t=' + str(thickness) + ' E=' + str(E/1000000000) +
     #       "e6 with crack0 L=" + str(cLenght) + " w=" + str(widthC) )

    #ax.set_title(title,fontsize=16)
    ax.set_ylabel("Pressure/Strength index (m)",fontsize=14)
    ax2.set_ylabel("Crack length (m)",fontsize=14)
    #ax3.set_ylabel("Leakage (m3/s)",fontsize=14)
    ax3.set_ylabel("Leakage (l/h)",fontsize=14)
    ax.set_xlabel('Time (years)',fontsize=14)
    
    #For the zoom in 
    ax.set_xlim(0,52)
    ax.set_ylim(0,200)
    ax2.set_ylim(0.18,0.40)
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.grid(axis='both', which='both')
    
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()

    ax2.legend(lines2+lines3+lines,labels2+labels3+ labels,loc='upper center',bbox_to_anchor=(.5,-.13), ncol=4,  fontsize=14)
    
    #Hide axis
    ax.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax3.spines['top'].set_visible(False)

    fig.savefig(fileName +'.png',dpi=200, bbox_inches='tight',transparent=True) #save as png
