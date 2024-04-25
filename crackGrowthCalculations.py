import math


#universal constants
GRAVITY=9.807 #m/s²
W_DENSITY= 900 #kg/m³

DETECTABLE_FLOW_M3S = 0.250/3600 #m3/s

DELTA_DAYS = 1 #delta time of one day 


def convertmToMPa(pressureInm:float)->float:
    
    return pressureInm * W_DENSITY * GRAVITY / (10 ** 6)

def getHeadAreaSlopeLong(crackLength:float,diameter:float,E:float,t:float)->float:
    """
        Calculates the head-area slope of a longitudinal leak. 
        Use the equation obtained by Cassa, & van Zyl, J. E. (2013). "Predicting the head-leakage slope of cracks in pipes subject to elastic deformations"
           Journal of Water Supply: Research and Technology - AQUA, 62(4), 214–223. https://doi.org/10.2166/aqua.2013.094
    Args:
        crackLength (float): length of the longitudinal crack in m 
        diameter (float): internal diameter of the pipe in m #TODO check if internal
        E (float): Elasticity modulus of the pipe material in Pa.
        t (float): Thickness of the pipe wall in m.
    Returns:
        float: Head-area slope of the longitudinal leak in m^2/m
    """ 
    try:   
        m= (2.93157*(diameter**0.3379)*(crackLength**4.8)*(10**(0.5997*(math.log(crackLength,10)**2)))*W_DENSITY*GRAVITY)/(E*(t**1.746))
    except:
        print(crackLength,diameter,E,t)
    
    return m

def calculateQWithFAVAD(Cd:float, h:float, A0:float, m:float)->float:
    """
        Calculates the flowrate of a leak at pressure h using the Modified orifice equation or FAVAD.
    Args:
        Cd (float): Discharge coeficient of the leak.
        h (float): Pressure of the pipe in m.
        A0 (float): Leak area under zero pressure conditions in m^2.
        mFAVAD (float): Head-area slope of the crack m^2/m.
    Returns:
        float : flowrate of the leak in m3/s.
    """    
    Q = Cd*((2*GRAVITY)**0.5)*(A0*(h**0.5)+m*(h**1.5))

    return Q
        
def getPressureToBeDiscover(Cd:float, m:float, A0:float, QDiscoverable:float)->float:
    """
        Calculates the pressure at which a leak is discoverable using the equation resultant 
        from solving the FAVAD equation for pressure.
    Args:
        Cd (float): Discharge coefficient of the leak
        m (float): Head-area slope of the leak in m^2/m
        A0 (float): Leak area under zero pressure conditions in m^2 #TODO check units
        QDiscoverable (float): Flow at which the avaliable leak detection technology will detect a leak in m3/s
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

def createCurveUntilDetectable(widthC:float,Cd:float,ElasticityModulus:float,Cparis:float,Mparis:float,Wthickness:float,Dint:float,iniCrackLength:float,
                               nCycles:float,Pmax:float,deltaP:float,nonLeakingL:float=0)->tuple[bool, list[float], list[float], list[float], list[float]]:
    """
        Calculate the growth of a longitudinal crack due to pressure cycles. Uses Euler to resolve the Paris Equation for
        a cylindrical shell. 
    Args:
        widthC (float): Crack width in m.
        Cd (float): Discharge coeficient of the leak to calculate its flowrate.
        ElasticityModulus (float): Elasticity modulus of the pipe material in Pa.
        Cparis (float): C paris constant obtained empirically for the pipe material in m/cycle/(Mpa m^0.5)^m.
        Mparis (float): m paris constant obtained empirically for the pipe material.
        Wthickness (float): Pipe wall thickness in m.
        Dint (float): Pipe Internal diameter in m.
        iniCrackLength (float): Initial crack length in m.
        nCycles (float): Number of cycles per day.
        Pmax (float): Maximum pressure of the pressure cycle in m.
        deltaP (float): Delta pressure un MPa
        nonLeakingL (float): Length of the crack that does not leak in m. Default is zero.
    Returns:
        tuple[bool, list[float], list[float], list[float], list[float]]: True if the function stoped coz the critical length was 
            reached, false if the discoverable flow rate was reached before the critical length. 
            List of days. List of pressure indexes in m. List of crack Lengths in m. List of flowrate in m3/s. 
    """    
    li = iniCrackLength
    day = 0
    Q=0
    critical = False
    BUFFER_TIME = 0.025 #So that the graph can show the progression for a bit longer
    
    days = []
    Hdetect = []
    leng=[]
    flow=[]

    nCiclesPerIter = DELTA_DAYS * nCycles # number of cycles per day
    
    #Euler
    while Q < (DETECTABLE_FLOW_M3S + BUFFER_TIME):

        #Paris Law------------------------------------------------------------------
        critical, Y = getGeometricFactorCylindricalShell(Wthickness, Dint, li)

        if critical:
            break
        
        deltaK = getStressIntensityFactor(Wthickness, Dint, li, deltaP, Y)
        da = calculateChangeInCrackLength(Cparis, Mparis, nCiclesPerIter, deltaK) 
        
        lf = (da - li/2)*2  #Final lenght of the crack in m
       
        # FAVAD--- from paper 012---------------------------------------------------
        lengthLeaking = lf-nonLeakingL   #m
        leakArea = lengthLeaking*widthC  #m2
        mFAVAD = getHeadAreaSlopeLong(lengthLeaking, Dint, ElasticityModulus, Wthickness)
            
        Q = calculateQWithFAVAD(Cd, Pmax, leakArea, mFAVAD) #m3/s
            
        try:
            hd = getPressureToBeDiscover(Cd, mFAVAD, leakArea, DETECTABLE_FLOW_M3S) #m
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
        Dint (float): Internal diameter of the cylindrical shell in m 
        crackLength (float): Length of the crack in m 
        deltaP (float): Pressure difference of the fluctuations creating the pressure fatige in MPa 
        geometricFactor (float): geometric factor of a crack on a cylindrical shell. 
    Returns:
        float: stress intensity factor of the crack in MPa m^0.5
    """    
    a = crackLength/2
    deltaK = deltaP * Dint / (2*thickness) * geometricFactor * (math.pi * a)**0.5

    return deltaK

def getGeometricFactorCylindricalShell(thickness:float, Dint:float, crackLength:float)->tuple[bool,float]:
    """
        Calculates the geometric factor of a crack on a cylindrical shell (pipe, pressure vessel).
        #TODO put the reference to the paper 
    Args:
        thickness (float): Wall thickness of the cylindrical shell in m
        Dint (float): Internal diameter of the cylindrical shell in m #TODO check units of evertyhign
        crackLength (float): Length of the crack in m 
    Returns:
        tuple[bool,float]: True if it reached the critical length, false otherwise. The value of the geometric factor.
    """ 
    critical = False  
    Y = None

    a = crackLength/2
    lam = a/(Dint*thickness/2)**0.5 #lambda

    if lam <= 1:
        Y = (1+1.25* lam**2)**0.5   
    elif lam <= 5:
        Y = 0.6 + (0.9 * lam)
    else:
        critical = True

    return critical,Y