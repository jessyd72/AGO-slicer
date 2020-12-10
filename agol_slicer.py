import arcgis
from arcgis.gis import GIS
import tkinter as tk

# get user credentials - Tk

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

# gets feature collections and their layers
lyrs = {}
lyr_search = gis.content.search(query="owner: {}".format(un), item_type="Feature *", max_items=1000)
# print(search_result)
# print(str(len(search_result)))
for item in lyr_search:
    feature_service_id = item.id
    # print(item.id)  # long id -> '4bf0ef22293b4964bb1e1e4bf261958a'
    feature_service_name = item.title
    # print(item.title)  # Feature service name
    feature_service_url = item.url
    # item.url  # feature service url 
    layers = item.layers
    for lyr in layers:
        # print(lyr.properties.name)  # layer name 
        # lyr.properties.id # layer index 
        layer_name = lyr.properties.name
        layer_id = lyr.properties.id
        lyrs[layer_name] = [layer_id, feature_service_id, feature_service_name, feature_service_url]

print('LAYERS: ')
print(lyrs)

# gets WABs and their maps
apps = {}
app_search = gis.content.search(query="owner: {}".format(un), item_type = 'Web Mapping Application')
# print(app_search)
for item in app_search:
    app_id = item.id
    # print(item.id)
    app_name = item.title
    # print(item.title)
    map_in_app_id = item.get_data()['map']['itemId']
    # print(map_id)
    apps[app_name] = [app_id, map_in_app_id]
    # if map_id == map_id_first:
    #     print('YES!!')
    # else:
    #     print('Well shit...')

print('APPS: ')
print(apps)

# gets web maps and their layers
maps = {}
map_search = gis.content.search(query="owner: {}".format(un), item_type="Web Map", max_items=1000)
# print(map_search)
for item in map_search:
    map_id = item.id
    # map_id_first = item.id
    # print(item.id)
    map_name = item.title
    # print(item.title)
    for lyr in item.get_data()['operationalLayers']:
        print(lyr)
        # print(lyr['url'])
        # print(lyr['title'])
        # print(lyr['itemId'])
        # maps[item.title] = [str(item.id), lyr['url'], lyr['title'], lyr['itemId']]

print('MAPS: ')
print(maps)

