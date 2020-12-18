import arcgis
from arcgis.gis import GIS
import tkinter as tk
import xlsxwriter
from xlsxwriter import Workbook

## get user credentials - Tk

user_input = []

def getUserInput():

    global outputs
    outputs = [item.get() for item in user_input]

    root.destroy()

root = tk.Tk()
root.title('AGOL Credentials')
root.geometry('400x300')

for x in range(3):

    inputs = tk.Entry(root)
    inputs.grid(row = x, column=1)
    if x == 0:
        inputs.insert(0, 'https://arcgis.com')
    if x == 2:
        inputs.config(show='*')
    user_input.append(inputs)

button = tk.Button(root, text='OK', command=getUserInput)
button.grid(row=3, column=0, pady=20)

label_url = tk.Label(root, text='AGOL/Portal URL ')
label_url.grid(row=0, column=0, pady=20)
label_un = tk.Label(root, text='Username ')
label_un.grid(row=1, column=0, pady=20)
label_pw = tk.Label(root, text='Password ')
label_pw.grid(row=2, column=0, pady=20)

root.mainloop()
print(outputs)

url = outputs[0]
un = outputs[1]
pw = outputs[2]

# access AGOL
gis = GIS(url=url, username=un, password=pw)
print('Logged in as: {}'.format(gis.properties.user.username))

# features
lyrs = {}
lyr_search = gis.content.search(query="owner: {}".format(un), item_type="Feature *", max_items=1000)
for item in lyr_search:
    layers = item.layers
    for lyr in layers:
        lyrs[item.url+'/{}'.format(lyr.properties.id)] = [item.id, item.title, lyr.properties.name]

# webmaps
maps = {}
map_search = gis.content.search(query="owner: {}".format(un), item_type="Web Map", max_items=1000)
for item in map_search:
    for item in map_search:
        opLyrs = item.get_data()['operationalLayers']
        lyrIDs = [[l['title'], l['url']] for l in opLyrs]
        maps[item.id] = [item.title, lyrIDs]

# apps
apps = {}
app_search = gis.content.search(query="owner: {}".format(un), item_type = 'Web Mapping Application')
for item in app_search:
    map_in_app_id = item.get_data()['map']['itemId']
    apps[item.title] = [item.id, map_in_app_id]

# set up workbook
workbook = Workbook(r'C:\data\gtg-data\projects\_agol-slicer\ago_slicer_test2.xlsx')
sheet = workbook.add_worksheet('AGO Content')
# head_style = workbook.add_format({'bold':True})
sheet.write('A1','WebApp') #, head_style)
sheet.write('B1','WebMap') #, head_style)
sheet.write('C1','Feature Layer') #, head_style)
sheet.write('D1','Feature Service') #, head_style)

row = 1

# used lists
used_webmap = []
used_layers = []

# should catch exceptions for missing keys... this would 
# identify broken maps/layer connections. 
# try, except if keyError, means webmap is deleted or
# feature layer/service is deleted renames/changed index
# and needs inspection. 

for k, v in apps.items():

    app_name = k
    app_id = v[0]
    map_id = v[1]

    map_title = maps[map_id][0]
    layer_list = maps[map_id][1]

    for i, layers in enumerate(layer_list):
        layer_name = layers[0]
        layer_url = layers[1]

        feature_service_name = lyrs[layer_url][1]

        row += 1

        sheet.write('A{}'.format(str(row)), app_name)
        sheet.write('B{}'.format(str(row)), map_title)
        sheet.write('C{}'.format(str(row)), layer_name)
        sheet.write('D{}'.format(str(row)), feature_service_name)

        used_webmap.append(map_id)
        used_layers.append(layer_url)

unused_webmaps = list(set(maps.keys()) - set(used_webmap))

for wm in unused_webmaps:
    map_title = maps[wm][0]
    layer_list = maps[wm][1]

    for i, layers in enumerate(layer_list):
        layer_name = layers[0]
        layer_url = layers[1]

        feature_service_name = lyrs[layer_url][1]

        row += 1

        sheet.write('B{}'.format(str(row)), map_title)
        sheet.write('C{}'.format(str(row)), layer_name)
        sheet.write('D{}'.format(str(row)), feature_service_name)

        used_layers.append(layer_url)

unused_layers = list(set(lyrs.keys()) - set(used_layers))

for l in unused_layers:
    feature_name = lyrs[l][2]
    feature_service_name = lyrs[l][1]

    row += 1

    sheet.write('C{}'.format(str(row)), layer_name)
    sheet.write('D{}'.format(str(row)), feature_service_name)


workbook.close()

print('DONE!')


