

import DataAnalysisConstants as DAC
import WatercareConstants as WC


MAX_PERCEN_TOSHOW = 2


#It finds the materials with significant percentage of pipe length
#it labels all other materials as OTHER, calculates the % of pipe length of each materials
# and assings the color values of each material 
def groupByMaterial(df, colors):
    
	groupMat = df.groupby([WC.MATERIAL]).agg({WC.LENG: 'sum'}).copy()

	#Creates the otherMaterials table to create the material "other" and updates the table
	groupMat[DAC.LEN_PERC] = groupMat[WC.LENG]/ groupMat[WC.LENG].sum() *100
	otherMaterials = groupMat[(groupMat[DAC.LEN_PERC] < MAX_PERCEN_TOSHOW)]
	groupMat = groupMat.reset_index()
	groupMat[WC.MATERIAL].replace(otherMaterials.index, DAC.OTHER, inplace=True)
	groupMat = groupMat.groupby([WC.MATERIAL]).agg({WC.LENG: 'sum' }).copy()

    #Once the other materials have been merged it calculates the percentages again 
	groupMat[DAC.LEN_PERC] = groupMat[WC.LENG]/ groupMat[WC.LENG].sum() *100

	#it adds the colors values to the dataframe
	groupMat = groupMat.join(colors).sort_values(by=WC.MATERIAL,axis=0, ascending=False)
   
	return groupMat

