
import pandas as pd 
import numpy as np

import WatercareConstants as WC
import DataAnalysisConstants as DAC
import Files as FILES


#Returns a dataframe from the file and drops duplicates by index (WONO) and by attributes
def getFailureRecords(fname):
    #Reads the cvs file result from the query to the Watercare DB and store it in a dataframe
    failureRecords = pd.read_csv(fname, delimiter = ',', 
                                 usecols=[0,1,7,9,8,5],
                                 dtype = {WC.WONO:'str', WC.ACTCODE:'str',WC.SERVNO:'str',WC.SR_PROB:'str',
                                          WC.ADDDTTM:'str', WC.COMPKEY:'int64'},
                                 index_col=0,
                                 parse_dates=[WC.ADDDTTM],
                                )[[WC.SERVNO,WC.ACTCODE,WC.SR_PROB,WC.ADDDTTM,WC.COMPKEY]]
    numFailureRecordsOri= failureRecords.shape[0]
    print('Number of records from the DB query:' , numFailureRecordsOri)

    failureRecords= failureRecords[~failureRecords.index.duplicated()].copy()

    print('Number of failure records:', failureRecords.shape[0], ' Deleted records duplicated WONO: ', numFailureRecordsOri - failureRecords.shape[0])
    numFailureRecordsOri = failureRecords.shape[0]

    #For this study if it is the same type of Repair activity on the same asset associated 
    #to the same service number and in the same date 
    #The duplicated values are due diferencees in the contractor reference numbers used to add parts of the costs.
    #therefore the duplicates are not necesary unless the cost is needed
    failureRecords.drop_duplicates(inplace=True)

    #check for duplicates using only the date (not datetime) in the extraMethods.py file!!

    print('Number of failure records:', failureRecords.shape[0], ' Deleted records: ', numFailureRecordsOri - failureRecords.shape[0])
    numFailureRecordsOri = failureRecords.shape[0]
    return failureRecords, numFailureRecordsOri

def getAddressFromFailureRecords(fname):

	addressRecords = pd.read_csv(fname, delimiter = ',', 
								usecols=[0,12,13,14,15,16,17],
								dtype = {WC.WONO:'str', 'Street_Type':'str','Street_Name':'str',WC.SUBURB:'str',
								'FLAT':'str','HOUSENO':'str','POSTCODE':'str'})

	addressRecords.drop_duplicates(inplace=True)
	addressRecords.set_index(WC.WONO, inplace=True, drop=True)

	return addressRecords

# Creates a dataset combining all 3 assets files, separate mains from other assests, remove duplicates and return the mains dataset
def getAssetsRecords():

    fname = FILES.ASSETS1
    fname2 = FILES.ASSETS2
    fname3 = FILES.ASSETS3

    AllAssets = pd.read_csv(fname, delimiter = ',', index_col=['Asset Compkey'],
                        dtype = {WC.ASSET_TYPECODE:'str',WC.ASSET_SERV_STA:'str','Asset Status':'str','Asset Compkey':'int64' },     
                        usecols=[1,2,3,4,5,6,7])
    AllAssets2 = pd.read_csv(fname2, delimiter = ',', index_col=['Asset Compkey'],
                        dtype = {WC.ASSET_TYPECODE:'str',WC.ASSET_SERV_STA:'str','Asset Status':'str','Asset Compkey':'int64' },     
                        usecols=[1,2,3,4,5,6,7])
    AllAssets3 = pd.read_csv(fname3, delimiter = ',', index_col=['Asset Compkey'],
                        dtype = {WC.ASSET_TYPECODE:'str',WC.ASSET_SERV_STA:'str','Asset Status':'str','Asset Compkey':'int64' },     
                        usecols=[1,2,3,4,5,6,7])

    AllAssetsCom = AllAssets.append(AllAssets2).append(AllAssets3).copy()

    WaterMain = AllAssetsCom[AllAssetsCom[WC.ASSET_TYPECODE] == WC.WMN].copy()

    print("There are ", WaterMain.shape[0], " water mains in the database (NOT GIS)")

    waterMains = WaterMain[~WaterMain.index.duplicated(keep='first')]

    print("There are ", WaterMain.shape[0], " water mains not duplicated in the database (NOT GIS)")
    
    #rename the index
    waterMains.index.names = [WC.COMPKEY]

    return waterMains

def getFilterCodesAndSR() :

	fileACTCODE = 'Data/01-ACTCODERepair.csv'
	fileSR_Prob = 'Data/02-SR_PROB_TO_FILTER.csv'

	#read the filter files
	ACTCODERepair = pd.read_csv(fileACTCODE)
	SR_ToFilter = pd.read_csv(fileSR_Prob)

	return ACTCODERepair, SR_ToFilter

# It removes records associated to 3rd party caused failures or with service requests that did not include a repair 
# From the dataset of service requests and returns the cleaned dataset
def filters3PandNotRepairs(failureRecords, SR_ToFilter, ACTCODERepair, numFailureRecordsOri):
	#filters the service codes related to third parties---------------------------------------------------------------
    failureRecords= failureRecords[~failureRecords[WC.SR_PROB].isin(SR_ToFilter['SR_PROB_TO_FILTER'])].copy()
    
    print('Number of failure records:', failureRecords.shape[0], ' 3P Deleted records: ', numFailureRecordsOri - failureRecords.shape[0])
    numFailureRecordsOri = failureRecords.shape[0]


	#filters the activities with actcodes not related to repairs------------------------------------------------------
    failureRecords= failureRecords[failureRecords[WC.ACTCODE].isin(ACTCODERepair[WC.ACTCODE])].copy()
    
    print('Number of failure records:', failureRecords.shape[0], ' Not repair Deleted records: ', numFailureRecordsOri - failureRecords.shape[0])
    
    return failureRecords

def filterFailuresbyInconsistentAddress(failures, addressRecords, assetAddresses):

	#adds the compkeys to the addressess of the failure table 
    failAddr= failures.join(addressRecords)[[WC.COMPKEY,'Street_Type','Street_Name',WC.SUBURB]]
    failAddr=failAddr.astype({WC.COMPKEY: 'int64'})

	#creates the table to compare addresses 
    addrComp= failAddr.join(assetAddresses, on=WC.COMPKEY)

	#compare the suburbs and drop the values that dont match
    indexToFilter= addrComp[addrComp[WC.SUBURB].str.upper()!=addrComp[WC.SUBURB].str.upper()].index
    failures.drop(indexToFilter , inplace=True)
    
    return failures

def manage_GISPipes(mainFailures,WMNFromAssetRecordsIndex):

	failuresWithPipesInGIS, wPipesGIS = getFailuresWithPipes(mainFailures,WMNFromAssetRecordsIndex)

	countNumFPerPipe = failuresWithPipesInGIS.groupby([WC.COMPKEY]).agg({WC.SERVNO: 'count', WC.ACTCODE : 'first'})
	countNumFPerPipe.rename(columns={WC.SERVNO:'Num of failures'}, inplace= True)


	#asign the number of failures per pipe including 0 to all the main pipe table and change formats
	wPipesGIS[WC.NOM_DIA_MM] = pd.to_numeric(wPipesGIS[WC.NOM_DIA_MM],errors='coerce')
	wPipesGISNfailures = wPipesGIS.join(countNumFPerPipe[['Num of failures']])
	wPipesGISNfailures["Num of failures"].fillna(0, inplace=True)
	wPipesGISNfailures['Shape_Leng'] = wPipesGISNfailures['Shape_Leng']/1000
	wPipesGISNfailures[WC.MATERIAL] = wPipesGISNfailures[WC.MATERIAL].replace(WC.UNKNOWN, np.nan)
    
    #Combine AC
	wPipesGISNfailures[WC.MATERIAL] = wPipesGISNfailures[WC.MATERIAL].replace(WC.FB, WC.AC)
    
    #Combine PE
	wPipesGISNfailures[WC.MATERIAL] = wPipesGISNfailures[WC.MATERIAL].replace(WC.ALK, WC.PE)
    
    #combine CI
	wPipesGISNfailures[WC.MATERIAL] = wPipesGISNfailures[WC.MATERIAL].replace(WC.CLCI, DAC.IRON)
	wPipesGISNfailures[WC.MATERIAL] = wPipesGISNfailures[WC.MATERIAL].replace(WC.DI, DAC.IRON)
	wPipesGISNfailures[WC.MATERIAL] = wPipesGISNfailures[WC.MATERIAL].replace(WC.ELCI, DAC.IRON)
	wPipesGISNfailures[WC.MATERIAL] = wPipesGISNfailures[WC.MATERIAL].replace(WC.CLDI, DAC.IRON)
	wPipesGISNfailures[WC.MATERIAL] = wPipesGISNfailures[WC.MATERIAL].replace(WC.GI, DAC.IRON)
	wPipesGISNfailures[WC.MATERIAL] = wPipesGISNfailures[WC.MATERIAL].replace(WC.CI, DAC.IRON) 
    
	wPipesGISNfailures[WC.NOM_DIA_MM].fillna(0, inplace=True)
	wPipesGISNfailures["Age Today"] = (pd.to_datetime('today').tz_localize('UTC')-pd.to_datetime(wPipesGISNfailures["INSTALLED"])).astype('<m8[Y]')
	

	#uniStatus = failuresWithPipesInGIS[WC.ASSET_SERV_STA].value_counts()
	#print('Pipes with failures in GIS', uniStatus)

	#uniStatus = failuresWithPipesMissingInGIS[WC.ASSET_SERV_STA].value_counts()
	#print('Pipes with failures missing in GIS', uniStatus)

	return wPipesGISNfailures

def getFailuresWithPipes(mainFailures, WMNFromAssetRecordsIndex):

	fWPipes = 'Data/00-Water_Pipe.csv'

	wPipesGIS = pd.read_csv(fWPipes, delimiter = ',', 
		                                dtype = {WC.COMPKEY:'int64',WC.STATUS:'str',WC.MATERIAL:'str',
		                                         WC.NOM_DIA_MM:'str',WC.INSTALLED:'str',
                                                 'Shape_Leng' : 'float64'},
		                                usecols=[2,8,9,11,12,18],
		                                parse_dates=[WC.INSTALLED],
		                                index_col=[WC.COMPKEY]
		                                )

	print("Records of pipes (GIS) ",  wPipesGIS.shape[0], " length ", "%.2f" % wPipesGIS['Shape_Leng'].sum())
	originalGIS = wPipesGIS.shape[0]
    
    #merge duplicates compkeys
	wPipesGIS = wPipesGIS.groupby(wPipesGIS.index).agg({'Shape_Leng':sum, WC.STATUS: 'first', WC.NOM_DIA_MM: 'first', WC.MATERIAL : 'first', WC.INSTALLED:'first'})
	print("Records of pipes (GIS) ",  wPipesGIS.shape[0], " total length ", "%.2f" % wPipesGIS['Shape_Leng'].sum(),". Removed COMPKEY duplicates: ", originalGIS - wPipesGIS.shape[0])
	originalGIS = wPipesGIS.shape[0]
	
	#Delete no main pipes by the all assets dataset
	wPipesGIS = wPipesGIS[wPipesGIS.index.isin(WMNFromAssetRecordsIndex)].copy()
	print("Records of main pipes (GIS) ",  wPipesGIS.shape[0], ". Removed pipes with all assets WMN: ", originalGIS - wPipesGIS.shape[0])
	
    
	#look for the pipes of the failures and create a table with number of failure per pipe
	mainF_GISPipes= mainFailures.join(wPipesGIS, on= WC.COMPKEY).copy()
	failuresWithPipesMissingInGIS = mainF_GISPipes[pd.isna(mainF_GISPipes['Shape_Leng'])].copy()
	failuresWithPipesInGIS = mainF_GISPipes[~pd.isna(mainF_GISPipes['Shape_Leng'])].copy()
	print('Failures with pipes in the GIS ', failuresWithPipesInGIS.shape[0], '. Failures with pipes missing in GIS ', failuresWithPipesMissingInGIS.shape[0])


	return failuresWithPipesInGIS, wPipesGIS

def getFailures(fname):
      
	failuresDF, numFailures = getFailureRecords(fname)
	addressFromFailureRecords = getAddressFromFailureRecords(fname)
	WMNFromAssetRecords = getAssetsRecords()

	ACTCODERepair, SR_ToFilter = getFilterCodesAndSR()

	failuresDF = filters3PandNotRepairs(failuresDF, SR_ToFilter, ACTCODERepair,numFailures)

	#divide between MAIN and SERViCE LINES------------------------------------------------
	mainFailures = failuresDF[(failuresDF[WC.ACTCODE]==WC.WMNRM) | (failuresDF[WC.ACTCODE]== WC.WMNRPL)].copy()

	numFailRecordsOriM = mainFailures.shape[0]
	print('Number of failures in Mains :', numFailRecordsOriM)

	mainFailures = filterFailuresbyInconsistentAddress(mainFailures, addressFromFailureRecords, WMNFromAssetRecords)
	print('Number of failures in Mains :', mainFailures.shape[0], ' Different address Deleted records: ', numFailRecordsOriM - mainFailures.shape[0])

	#returns the shape_length in km
	wPipesGISNfailures = manage_GISPipes(mainFailures,WMNFromAssetRecords.index)

	return wPipesGISNfailures, mainFailures
