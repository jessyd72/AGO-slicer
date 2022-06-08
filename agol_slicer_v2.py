from arcgis.gis import GIS, User
import os
import json
from datetime import datetime

from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from matplotlib.pyplot import text


def getUserCreds():

    gui = Tk()
    gui.geometry("400x400")
    gui.title("FC")

    user_input = []

    def getFolderPath():
        folder_selected = filedialog.askdirectory()
        folderPath.set(folder_selected)

    def doStuff():
        global outputs
        outputs = [item.get() for item in user_input]

        gui.destroy()

    folderPath = StringVar()
    a = Label(gui ,text="Select folder to save Excel file")
    a.grid(row=0,column = 0, pady=20)
    E0 = Entry(gui,textvariable=folderPath)
    E0.grid(row=0,column=1)
    btnFind = ttk.Button(gui, text="Browse Folder",command=getFolderPath)
    btnFind.grid(row=0,column=2, pady=20)
    user_input.append(E0)

    label_url = Label(gui, text='AGOL/Portal URL ')
    label_url.grid(row=1, column=0, pady=20)
    E1 = Entry(gui,textvariable='https://arcgis.com')
    E1.grid(row=1,column=1)
    E1.insert(1, 'https://arcgis.com')
    user_input.append(E1)

    label_un = Label(gui, text='Username ')
    label_un.grid(row=2, column=0, pady=20)
    E2 = Entry(gui)
    E2.grid(row=2,column=1)
    user_input.append(E2)

    label_pw = Label(gui, text='Password ')
    label_pw.grid(row=3, column=0, pady=20)
    E3 = Entry(gui)
    E3.grid(row=3,column=1)
    E3.config(show='*')
    user_input.append(E3)

    c = ttk.Button(gui ,text="Run!", command=doStuff)
    c.grid(row=4,column=0, pady=20)

    gui.mainloop()
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

        today = datetime.now().strftime('%m%d%Y')

        # AGOL item types
        print('loading dictionary...')
        working_fldr = (os.path.dirname(__file__))
        item_txt = open(working_fldr + r'\AGO_items_by_group.json').read()
        item_types = json.loads(item_txt)

        print('getting credentials...')
        creds = getUserCreds()

        print(creds)

        url = creds[1]
        un = creds[2]
        pw = creds[3]
        out_xlsx_path = creds[0]

        out_xlsx = out_xlsx_path + f'\AGO_ContentSlicer_{un}_{today}.xlsx'
        print(f'output file: {out_xlsx}')

        print('accessing AGO...')
        gis = GIS(url, un, pw)
        user = User(gis, un)
        ## future ref- can use gis.users.search() to get list
        ## of all users in org. Loop all users through the
        ## getContent funct to get whole org's content. 
        ## consider new tab/df for each user

        # print('getting user''s content...')
        # item_dict = getContent(user)
        # print('organizing content by type...')
        # apps, maps, lyrs, data = sortContent(item_dict, item_types)
        # print('creating XLSX...')
        # wb, sh = createWorkbook(out_xlsx, un)
        # print('writing to XLSX...')
        # writeItems(wb, sh, apps, maps, lyrs, data)

    except KeyError as e:
        print('oh noo')
        
        # print(e)
        # print(lyrs)
        # print(maps)
        # print(apps)

'''
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
gui = Tk()
gui.geometry("400x400")
gui.title("FC")

def getFolderPath():
    folder_selected = filedialog.askdirectory()
    folderPath.set(folder_selected)

def doStuff():
    folder = folderPath.get()
    print("Doing stuff with folder", folder)

folderPath = StringVar()
a = Label(gui ,text="Enter name")
a.grid(row=0,column = 0)
E = Entry(gui,textvariable=folderPath)
E.grid(row=0,column=1)
btnFind = ttk.Button(gui, text="Browse Folder",command=getFolderPath)
btnFind.grid(row=0,column=2)

c = ttk.Button(gui ,text="find", command=doStuff)
c.grid(row=4,column=0)
gui.mainloop()
'''