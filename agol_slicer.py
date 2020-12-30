import arcgis
from arcgis.gis import GIS, User
import json
import tkinter as tk
import xlsxwriter
from xlsxwriter import Workbook

def createWorkbook(output_dir, un):
    ''' Creates Excel workbook with sheet of 
    AGOL content for a user. Intended to be used
    to create a slicer.'''

    workbook = Workbook(output_dir)
    sheet = workbook.add_worksheet('AGO Items-{}'.format(un))
    sheet.write('A1','WebApp')
    sheet.write('B1','WebMap')
    sheet.write('C1','Feature Layer')
    sheet.write('D1','Feature Service')
    sheet.write('E1', 'Folder')

    return(workbook, sheet)

def getUserCreds():
    '''Gets AGO/Portal creds'''

    def getUserInput():
        '''Reads inputs from Tk object'''

        global outputs
        outputs = [item.get() for item in user_input]

        root.destroy()

    user_input = []

    root = tk.Tk()
    root.title('AGOL Credentials')
    root.geometry('400x400')

    for x in range(4):

        inputs = tk.Entry(root)
        inputs.grid(row = x, column=1)
        if x == 0:
            inputs.insert(0, 'https://arcgis.com')
        if x == 2:
            inputs.config(show='*')
            
        user_input.append(inputs)

    button = tk.Button(root, text='OK', command=getUserInput)
    button.grid(row=4, column=0, pady=20)

    label_url = tk.Label(root, text='AGOL/Portal URL ')
    label_url.grid(row=0, column=0, pady=20)
    label_un = tk.Label(root, text='Username ')
    label_un.grid(row=1, column=0, pady=20)
    label_pw = tk.Label(root, text='Password ')
    label_pw.grid(row=2, column=0, pady=20)
    label_pw = tk.Label(root, text='Output Excel Workbook ')
    label_pw.grid(row=3, column=0, pady=20)

    root.mainloop()
    return(outputs)

def getContent(user):
    '''Gets all items within a user's
    AGO. Returns a dictionary of items, 
    Item ID : [Item Title, Item Type, Folder]'''

    all_items = {}

    # get users items (home)
    for item in user.items():
        if item.type != 'Code Attachment':
            all_items[item.itemid] = [item.title, item.type, 'home', item]

    folders = user.folders
    for f in folders:
        f_items = user.items(folder=f['title'])
        for item in f_items:
            if item.type != 'Code Attachment':
                all_items[item.itemid] = [item.title, item.type, f['title'], item]

    return(all_items)

def sortContent(items, content_types):
    '''Sorts content into respective dictionaries
    to write to Excel workbook in writeItems function. 
    Accesses any layers within a feature service.
    maps, layers, tools, applications, datafiles'''

    lyrs = {}
    maps = {}
    apps = {}
    data = {}
    tools = {}

    for k, v in items.items():
        item_id = k
        item_title = v[0]
        item_type = v[1]
        item_loc = v[2]
        item_obj = v[3]

        item_cat = content_types[item_type]

        if item_cat == 'layers':
            layers = item_obj.layers
            for l in layers:
                service_url = (l.url).replace('ArcGIS', 'arcgis')
                lyr_name = l.properties.name
                # feature layer service url = [feature layer name, feature service id, feature service name, folder]
                lyrs[service_url] = [lyr_name, item_id, item_title, item_loc]
            if item_type == 'Map Service':
                lyrs[item_obj.url] = [item_title, item_id, item_title, item_loc]

        elif item_cat == 'maps':
            op_lyrs = item_obj.get_data()['operationalLayers']
            op_lyr_ids = [[l['title'], l['url'].replace('ArcGIS', 'arcgis')] for l in op_lyrs]
            # web map id = [web map name, [feature layer name, feature layer service url]]
            maps[item_id] = [item_title, op_lyr_ids, item_loc]
        
        elif item_cat == 'applications':
            # print(item_id)
            # print(item_title)l
            # print(item_type)
            # print(item_loc)
            map_in_app = ''
            app_data = item_obj.get_data()
            if 'map' in app_data.keys():
                map_in_app = app_data['map']['itemId']
            elif item_type == 'Dashboard' and 'widgets' in app_data.keys():
                for d in app_data['widgets']:
                    if d['type'] == 'mapWidget':
                        map_in_app = d['itemId']
                if map_in_app == '':
                    map_in_app = 'NA'
            else:
                map_in_app = 'NA'
            # application name = [application id, web map id]
            apps[item_title] = [item_id, map_in_app, item_loc]

        elif item_cat == 'datafiles':
            data[item_title] = [item_id, item_loc]
        
        elif item_cat == 'tools':
            tools[item_title] = [item_id, item_loc]

        else:
            continue   

    return(apps, maps, lyrs, data)

def writeItems(workbook, sheet, apps, maps, layers, data):
    '''dooo itttt
     feature layer service url = [feature layer name, feature service id, feature service name, folder]
     web map id = [web map name, [feature layer name, feature layer service url]]
     application name = [application id, web map id]'''

    used_webmap = []
    used_layers = []
    row = 1

    for k, v in apps.items():

        app_name = k
        map_id = v[1]

        if map_id == 'NA':

            row += 1

            sheet.write('A{}'.format(str(row)), app_name)

        else:
            map_title = maps[map_id][0]
            layer_list = maps[map_id][1]

            for lyr in layer_list:
                layer_name = lyr[0]
                layer_url = lyr[1]

                feature_service_name = layers[layer_url][2]

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

        for lyr in layer_list:
            layer_name = lyr[0]
            layer_url = lyr[1]

            feature_service_name = layers[layer_url][2]

            row += 1

            sheet.write('B{}'.format(str(row)), map_title)
            sheet.write('C{}'.format(str(row)), layer_name)
            sheet.write('D{}'.format(str(row)), feature_service_name)

            used_layers.append(layer_url)

    unused_layers = list(set(layers.keys()) - set(used_layers))

    for l in unused_layers:
        layer_name = layers[l][0]
        feature_service_name = layers[l][2]

        row += 1

        sheet.write('C{}'.format(str(row)), layer_name)
        sheet.write('D{}'.format(str(row)), feature_service_name)

    workbook.close()


if __name__ == '__main__':

    try: 

        # AGOL item types
        print('loading dictionary...')
        txt = open(r"C:\data\gtg-data\projects\_agol-slicer\AGO_items_by_group.json").read()
        item_types = json.loads(txt)

        print('getting credentials...')
        creds = getUserCreds()

        url = creds[0]
        un = creds[1]
        pw = creds[2]
        out_xlsx = creds[3]

        print('accessing AGO...')
        gis = GIS(url, un, pw)
        user = User(gis, un)
        ## future ref- can use gis.users.search() to get list
        ## of all users in org. Loop all users through the
        ## getContent funct to get whole org's content. 
        ## consider new tab/df for each user

        print('getting user''s content...')
        item_dict = getContent(user)
        print('organizing content by type...')
        apps, maps, lyrs, data = sortContent(item_dict, item_types)
        print('creating XLSX...')
        wb, sh = createWorkbook(out_xlsx, un)
        print('writing to XLSX...')
        writeItems(wb, sh, apps, maps, lyrs, data)

    except KeyError as e:
        
        print(e)
        print(lyrs)
        print(maps)
        print(apps)

