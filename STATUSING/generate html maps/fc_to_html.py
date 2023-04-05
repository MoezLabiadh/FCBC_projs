'''
This function creates a HTML map for each Feature classe stored
in the one_status_common_datasets geodatabase
'''

import os
import timeit

import geopandas as gpd
import numpy  as np
import fiona #can replace with arcpy
#import arcpy
import folium


def generate_html_maps(status_gdb):
    """Creates a HTML map for each feature class in gdb"""
    # List all feature classes
    #can replace with arcpy.ListFeatureClasses()
    fc_list = fiona.listlayers(status_gdb)
    #arcpy.env.workspace = status_gdb
    #fc_list = arcpy.ListFeatureClasses()
    
    # Read the AOI feature class into a gdf 
    gdf_aoi = gpd.read_file(filename= status_gdb, layer= 'aoi')
    
    # Remove the aoi and aoi buffers from the list of feature classes
    fc_list = [x for x in fc_list if 'aoi' not in x]
    
    # Loop through the feature classes and make maps
    counter = 1
    for fc in fc_list:
        # Read the feature class into a gdf 
        gdf_fc = gpd.read_file(filename= status_gdb, layer= fc)
        
        print ("Creating Map {0} of {1}: {2}".format(counter,len(fc_list),fc))
        
        # Make sure the layer is not empty
        if gdf_fc.shape[0] > 0:
            # Set label column. Will be used for tooltip and legend.
            # Replace this with the label column from the tool inputs
            label_col = gdf_fc.columns[gdf_fc.columns.get_loc('label_field') + 1] 
        
            # Datetime columns are causing errors when plotting in folium. Converting them to str
            for col in gdf_fc.columns:
                if gdf_fc[col].dtype == 'datetime64[ns]':
                    gdf_fc[col] = gdf_fc[col].astype(str)
            
            # Remove the Geometry column from the popup window. 
            # Popup columns can be set to the list of columns pulled from the AST input spreadsheets
            popup_cols = list(gdf_fc.columns)                     
            popup_cols.remove('geometry')  
            
            # Initiate a Map object and set extent based on the layer 
            map_obj = folium.Map(tiles='openstreetmap')
            xmin,ymin,xmax,ymax = gdf_fc.to_crs(4326)['geometry'].total_bounds
            map_obj.fit_bounds([[ymin, xmin], [ymax, xmax]])
                    
            # Add the AOI layer to the folium map
            folium.GeoJson(data=gdf_aoi, name='AOI',
                           style_function=lambda x:{'color': 'red',
                                                    'weight': 3}).add_to(map_obj)
            
            # Assign random colors to the features (for legend)
            for x in gdf_fc.index:
                color = np.random.randint(16, 256, size=3)
                color = [str(hex(i))[2:] for i in color]
                color = '#'+''.join(color).upper()
                gdf_fc.at[x, 'color'] = color
                
            # Create a style function for the main layer 
            def style (feature):
                return {'fillColor': feature['properties']['color'],
                        'color': feature['properties']['color'],
                        'weight': 2}
            
            # Add the main layer to the folium map
            folium.GeoJson(data=gdf_fc,
                           name=fc,
                           style_function= style,
                           tooltip=folium.features.GeoJsonTooltip(fields=[label_col], labels=True),
                           popup=folium.features.GeoJsonPopup(fields=popup_cols, sticky=False)).add_to(map_obj)
            
            # add layer controls to the map
            folium.LayerControl().add_to(map_obj)
            
            # Create a Legend
            #legend colors and names
            legend_labels = zip(gdf_fc['color'], gdf_fc[label_col])
            
            #start the div tag and set the legend size and position
            legend_html = '''
                        <div id="legend" style="position: fixed; 
                        bottom: 50px; right: 50px; z-index: 1000; 
                        background-color: #fff; padding: 10px; 
                        border-radius: 5px; border: 1px solid grey;">
                        '''
            #add the AOI item to the legend
            legend_html += '''
                        <div style="display: inline-block; 
                        margin-right: 10px;background-color: red; 
                        width: 15px; height: 15px;"></div>AOI<br>
                        '''
            #add a header to the legend            
            legend_html += '''
                        <div style="font-weight: bold; 
                        margin-bottom: 5px;">{}</div>
                        '''.format(label_col)
        
            #add items to the legend
            for color, name in legend_labels:
                legend_html += '''
                                <div style="display: inline-block; 
                                margin-right: 10px;background-color: {0}; 
                                width: 15px; height: 15px;"></div>{1}<br>
                                '''.format(color, name)
            #close the div tag
            legend_html += '</div>'
            
            #add the legend to the map
            map_obj.get_root().html.add_child(folium.Element(legend_html))
            
        
            # Save the interavtive map to html file
            out_loc = r'\\spatialfiles.bcgov\Work\lwbc\visr\Workarea\moez_labiadh\TOOLS\SCRIPTS\STATUSING\fc_to_html\maps'
            map_obj.save(os.path.join(out_loc, fc+'.html'))
            
        counter += 1




# Execute the function and track processing time
start_t = timeit.default_timer() #start time


# This is an example of a one_status_common_datasets geodatabase
status_gdb = r'\\spatialfiles.bcgov\work\lwbc\visr\Workarea\FCBC_VISR\Lands_Statusing\1414630\one_status_common_datasets_aoi.gdb'

generate_html_maps(status_gdb)

finish_t = timeit.default_timer() #finish time
t_sec = round(finish_t-start_t)
mins = int (t_sec/60)
secs = int (t_sec%60)
print ('\nProcessing Completed in {} minutes and {} seconds'.format (mins,secs))
