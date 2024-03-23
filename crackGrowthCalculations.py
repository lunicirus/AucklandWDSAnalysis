import math


#universal constants
GRAVITY=9.807 #m/s²
W_DENSITY= 900 #kg/m³

DETECTABLE_FLOW_M3S = 0.250/3600 #m3/s

DELTA_DAYS = 1 #delta time of one day 


def convertmToMPa(pressureInm):
    
    return pressureInm * W_DENSITY * GRAVITY / (10 ** 6)

def convertMPaTom(pressureInMPa):
    
    return pressureInMPa * (10 ** 6)/(W_DENSITY * GRAVITY)

def getMLongFAVAD(crackLength:float,Dint:float,E:float,t:float)->float:
    """
        Calculates the head-area slope of a longitudinal leak. 
        Use the equation obtained by Cassa, & van Zyl, J. E. (2013). "Predicting the head-leakage slope of cracks in pipes subject to elastic deformations"
           Journal of Water Supply: Research and Technology - AQUA, 62(4), 214–223. https://doi.org/10.2166/aqua.2013.094
    Args:
        crackLength (float): length of the longitudinal crack in m 
        Dint (float): internal diameter of the pipe in m #TODO check units
        E (float): Elasticity modulus of the pipe material #TODO check units
        t (float): Thickness of the pipe wall in m #TODO check units

    Returns:
        float: Head-area slope of the longitudinal leak  
    """    
    
    return (2.93157*(Dint**0.3379)*(crackLength**4.8)*(10**(0.5997*(math.log(crackLength,10)**2)))*W_DENSITY*GRAVITY)/(E*(t**1.746))
        
def getPressureToBeDiscover(Cd:float, m:float, A0:float, QDiscoverable:float)->float:
    """
        Calculates the pressure at which a leak is discoverable using the equation resultant 
        from solving the FAVAD equation for pressure.
    Args:
        Cd (float): Discharge coefficient of the leak
        m (float): Head-area slope of the leak 
        A0 (float): Leak area under zero pressure conditions in m^2 #TODO check this m2 and m of the pressure head resultant
        QDiscoverable (float): Flow at which the avaliable leak detection technology will detect a leak
    Returns:
        float: Pressure head in m at which the leak would be discoverable
    """    
    
    C =  Cd*((2*GRAVITY)**0.5) 

    a3 = A0**3

    B3 = (2**(1/3)) * (C**2)
    
    B = ((2*a3*(C**6)*(m**3))+(3*(((12*a3*(C**10)*(m**7)*(QDiscoverable**2))+(81*(C**8)*(m**8)*(QDiscoverable**4)))**0.5))+(27*(C**4)*(m**4)*(QDiscoverable**2)))**(1/3)

    B1 = B3 * (m**2)

    B2 = B3 * (A0**2)

    hd = (1/3)*( (B/B1) + (B2/B) - (2*A0/m) )
    
    return hd

def createCurveUntilDetectable(widthC:float,Cd:float,E:float,Cparis:float,Mparis:float,t:float,Dint:float,lo:float,
                               nCicles:float,Pmax:float,Pmin:float,nonLeakingL:float=0)->tuple[bool, list[float], list[float], list[float], list[float]]:
    """
        Calculate the growth of a longitudinal crack due to pressure cycles. Uses Euler to resolve the Paris Equation for
        a cylindrical shell. 
    Args:
        widthC (float): Crack width in m.
        Cd (float): Discharge coeficient of the leak to calculate its flowrate.
        E (float): Elasticity modulus of the pipe material. #TODO units
        Cparis (float): C paris constant obtained empirically for the pipe material.
        Mparis (float): m paris constant obtained empirically for the pipe material.
        t (float): pipe wall thickness in m.
        Dint (float): pipe Internal diameter in m.
        lo (float): Initial crack length in m.
        nCicles (float): number of cycles per day.
        Pmax (float): Maximum pressure of the pressure cycle in m.
        Pmin (float): Minimum pressure of the pressure cycle in m.
        nonLeakingL (float): length of the crack that does not leak. Default is zero.
    Returns:
        tuple[bool, list[float], list[float], list[float], list[float]]: True if the function stoped coz the critical length was 
            reached, false if the discoverable flow rate was reached before the critical length. 
            List of 
    """    
    li = lo
    day = 0
    Q=0
    critical = False
    BUFFER_TIME = 0.025 #So that the graph can show the progression for a bit longer
    
    days = []
    Hdetect = []
    leng=[]
    flow=[]

    deltaP= convertmToMPa(Pmax-Pmin) #MPa
    nCiclesPerIter = DELTA_DAYS * nCicles # number of cycles per day
    
    #Euler
    while Q < (DETECTABLE_FLOW_M3S + BUFFER_TIME):

        #Paris Law------------------------------------------------------------------
        critical, Y = getGeometricFactorCylindricalShell(t, Dint, li)

        if critical:
            break
        
        deltaK = getStressIntensityFactor(t, Dint, li, deltaP, Y)
        
        #Final lenght of the crack
        lf = calculateChangeInCrackLength(Cparis, Mparis, nCiclesPerIter, deltaK) + li 
       
        # FAVAD--- from paper 012---------------------------------------------------
        lengthLeaking=lf-nonLeakingL  #0.175 #TODO put this value when the method is called
        leakArea = lengthLeaking*2*widthC
        mFAVAD = getHeadAreaSlope(E, t, Dint, lengthLeaking)
            
        Q = calculateQWithFAVAD(Cd, Pmax, leakArea, mFAVAD)
            
        try:
            hd = getPressureToBeDiscover(Cd, mFAVAD, leakArea, DETECTABLE_FLOW_M3S)
        except:
            print("Flow that is produced at the Pmax: ",Q)
            hd = 0 if (Q>=DETECTABLE_FLOW_M3S) else Exception("Error")
        
        
        Hdetect.append(hd)
        days.append(day)
        leng.append(lf)
        flow.append(Q)
   
        
        li = lf
        day += DELTA_DAYS
    
            
        if (day/365)>200:
            print("Too Slow")
            break
    
    
    return critical, days, Hdetect, leng, flow

def calculateQWithFAVAD(Cd, Pmax, leakArea, mFAVAD):
    Q = Cd*((2*g)**0.5)*(leakArea*(Pmax**0.5)+mFAVAD*(Pmax**1.5))
    return Q

def getHeadAreaSlope(E, t, Dint, lengthLeaking):
    try:
        mFAVAD = getMLongFAVAD(lengthLeaking*2,Dint,E,t)
    except:
        print(lengthLeaking,Dint,E,t)
    return mFAVAD

def calculateChangeInCrackLength(Cparis:float, Mparis:float, nCycles:int, deltaK:float)->float:
    """
        Calculates the length change on a longitudinal crack due to nCycles number of pressure cycles.
        #TODO put paris? 
    Args:
        Cparis (float): C paris constant obtained empirically for the pipe material.
        Mparis (float): m paris constant obtained empirically for the pipe material.
        nCycles (int): Number of cycles that provoked the length change.
        deltaK (float): Stress intensity factor of the crack with length before the number of cycles. #TODO put units
    Returns:
        float: change in crack length due to the number of cycles
    """    
    return (Cparis * deltaK**Mparis )* nCycles

def getStressIntensityFactor(thickness:float, Dint:float, crackLength:float, deltaP:float, geometricFactor:float)->float:
    """
        Calculates the stress intensity factor of a crack given the characteristics of the crack and the pipe.
        #TODO put reference to paper
    Args:
        thickness (float): Wall thickness of the cylindrical shell in m
        Dint (float): Internal diameter of the cylindrical shell in m #TODO check units of everything.
        crackLength (float): Length of the crack in m #TODO check that is not half of the crack length.
        deltaP (float): Pressure difference of the fluctuations creating the pressure fatige in MPa #TODO check units.
        geometricFactor (float): geometric factor of a crack on a cylindrical shell. 
    Returns:
        float: stress intensity factor of the crack
    """    
    deltaK = deltaP * Dint / (2*thickness) * geometricFactor * (math.pi * crackLength)**0.5

    return deltaK

def getGeometricFactorCylindricalShell(thickness:float, Dint:float, crackLength:float)->tuple[bool,float]:
    """
        Calculates the geometric factor of a crack on a cylindrical shell (pipe, pressure vessel).
        #TODO put the reference to the paper 
    Args:
        thickness (float): Wall thickness of the cylindrical shell in m
        Dint (float): Internal diameter of the cylindrical shell in m #TODO check units of evertyhign
        crackLength (float): Length of the crack in m #TODO check that is not half of the crack length
    Returns:
        tuple[bool,float]: True if it reached the critical length, false otherwise. The value of the geometric factor.
    """    
    lam = crackLength/(Dint*thickness/2)**0.5 #lambda

    if lam <= 1:
        Y = (1+1.25* lam**2)**0.5   
    elif lam <= 5:
        Y = 0.6 + (0.9 * lam)
    else:
        critical = True

    return critical,Y