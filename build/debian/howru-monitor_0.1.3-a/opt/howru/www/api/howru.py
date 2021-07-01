import json
import flask
from flask import request, jsonify, render_template
import os, os.path
import glob

app = flask.Flask(__name__)
app.config["DEBUG"] = True
data = None
settings = None
bindPort = None
multi_server = False
data_dir="/opt/howru/www"

def load_conf():
    global bindPort, multi_server
    conf = open("/etc/howru/howruc.conf", "r")
    for line in conf:
        if (line.find('api') == 0):
            if (line.find('Port') > 0):
                pos = line.find('=')
                port = line[pos+1:]
                if (isinstance(int(port), int)):
                   bindPort = int(port)
                else:
                    bindPort = 80
            if (line.find('Server') > 0):
                pos = line.find('=')
                multi_s = line[pos+1]
                if (isinstance(int(multi_s), int)):
                    if (multi_s > 0):
                        multi_server = True
                    else:
                        multi_server = False
                else:
                    multi_server = False
    conf.close()
    return bindPort

def load_data():
    global data, multi_server
    if (multi_server):
       count = 0 
       os.chdir(data_dir)
       data = {
                  "server": [
                      ]
              }

       for file in glob.glob("*.json"):
            f = open(file, "r")
            data_set = json.loads(f.read())
            data["server"].append(data_set)
            f.close()
            count = count + 1
       os.chdir("/opt/howru/www/api")
    else:
       f = open("../monitor_data.json", "r")
       data = json.loads(f.read())
       f.close()

def load_settings():
    global settings 
    f = open("/etc/howru/plugins.conf", "r")
    try:
        settings = f.readlines()
    finally:
        f.close()

def load_scheduler_settings():
    global settings
    f = open("/etc/howru/howruc.conf", "r")
    try:
        settings = f.readlines()
    finally:
        f.close()

@app.route('/', methods=['GET'])
def home():
    full_filename = '/static/howru.png'
    return render_template("index.html", user_image = full_filename)

@app.route('/docs', methods=['GET'])
def documentation():
    full_filename = '/static/howru.png'
    return render_template("documentation.html", user_image = full_filename)
 
@app.route('/pluginSearch', methods=['GET'])
def search_plugin():
    full_filename = '/static/howru.png'
    return render_template("plugin_query.html", user_image = full_filename)

@app.route('/api/v1/howru/monitoring/json', methods=['GET'])
def api_json():
   global data
   load_data()
   return jsonify(data)

@app.route('/api/v1/howru/monitoring/howareyou', methods=['GET'])
def api_howareyou():
    global data, multi_server
    load_data()
    ok = 0
    warn = 0
    crit = 0
    results = []
    unknown = 0
    res = "I am not sure"

    if (multi_server):
        print("Not yet implemented")
        results = [
            { 'answer' : res,
            'monitor_results':
                   {'ok': 0,
                     'warn' : 0,
                    'crit' : 0,
                    'unknown': 0
                }
            }
        ]
    else:
        obj = data['monitoring']
        for status in obj:
            if (status['pluginStatusCode'] == "0"):
                ok = ok + 1
            elif (status['pluginStatusCode'] == "1"):
                warn = warn + 1
            elif (status['pluginStatusCode'] == "2"):
                crit = crit +1
            else:
                unknown = unknown +1
        if (crit > 0):
            res = "I'm not fine!"
        else:
            if (warn > 0):
                res = "I'm so so"
            else:
                res = "I'm "
                if (unknown > 0):
                    res = res + " not completly sure to be honest."
                else:
                    res = res + " fine, thanks for asking!"

        results = [
            { 'answer' : res,
            'monitor_results':
                   {'ok': ok,
                     'warn' : warn,
                    'crit' : crit,
                    'unknown': unknown
                }  
            }
        ]

    return jsonify(results)

@app.route('/api/v1/howru/monitoring/ok', methods=['GET'])
def api_show_oks():
    global data, multi_server
    load_data()
    results = []

    if (multi_server):
        #results.append(data['server'])
        print "Not yet implemented"
    else:
        results.append(data['host'])
        obj = data['monitoring']
        for i in obj:
            if (i['pluginStatusCode'] == "0"):
                results.append(i)

    return jsonify(results)

@app.route('/api/v1/howru/monitoring/warnings', methods=['GET'])
def api_show_warnings():
    global data, multi_server
    load_data()
    results = []

    if (multi_server):
        print("Not yet implemented")
    else:
        results.append(data['host'])
        obj = data['monitoring']
        for i in obj:
            if (i['pluginStatusCode'] == "1"):
                results.append(i)

    return jsonify(results)

@app.route('/api/v1/howru/monitoring/criticals', methods=['GET'])
def api_show_criticals():
    global data, multi_server
    load_data()
    results = []

    if (multi_server):
        print ("Not implemente yet")
    else:
       results.append(data['host'])
       obj = data['monitoring']
       for i in obj:
           if (i['pluginStatusCode'] == "2"):
               results.append(i)

    return jsonify(results)

@app.route('/api/v1/howru/monitoring/changes', methods=['GET'])
def api_show_changes():
    global data, multi_server
    load_data()
    results = []

    if (multi_server):
        print("Not implemented yet")
        return results

    results.append(data['host'])
    obj = data['monitoring']
    for i in obj:
        if (i['pluginStatusChanged'] == "1"):
            results.append(i)

    return jsonify(results)

@app.route('/api/v1/howru/monitoring/plugin', methods=['GET'])
def api_show_plugin():
    global data, multi_server
    load_data()
    do_start = True
    info = []
    name = ""
    id = -1
    id_count = 0
    results = []

    if (multi_server):
        print("Not implemented yet")
        return results

    results.append(data['host'])
    if 'name' in request.args:
        name = request.args['name']
    elif 'id' in request.args:
        id = int(request.args['id'])
    else:
        do_start = False
        info = [
           { 'returnCode' :'2',
                'monitoring':
                   {'info': 'No id or name provided for plugin'
                   }
           }
        ]
        results.append(info)
    if (do_start):
       obj = data['monitoring']
       for i in obj:
           if ((id_count == id) or (name == i['pluginName'])):
               results.append(i)
               break
           id_count = id_count + 1

    return jsonify(results)

@app.route('/api/v1/howru/settings/plugins', methods=['GET'])
def api_show_settings():
    global settings
    load_settings()
    results = []
    #results = settings
    for s in settings:
        if (s[0] != '#'):
            s_arr = s.split(';')
            pos = s_arr[0].find(']')
            p_name = s_arr[0][1:pos]
            p_des = s_arr[0][pos+2:]
            p_info = [
                    { 'pluginName' : p_name,
                        'settings':
                        {'description': p_des,
                         'command': s_arr[1],
                         'active': s_arr[2],
                         'interval': s_arr[3].rstrip()
                        }
               }
            ]
            results.append(p_info)

    return jsonify(results)

@app.route('/api/v1/howru/settings/scheduler', methods=['GET'])
def api_show_scheduler_settings():
    global settings
    load_scheduler_settings()
    results = []

    #results = settings
    for s in settings:
        s.rstrip()
        s_arr = s.split('=')
        pos = s_arr[0].find('.')
        configType = s_arr[0][:pos]
        configName = s_arr[0][pos+1:]
        pos = s.find('=')
        configValue = s[pos+1:].rstrip()
        if (len(configType) > 2):
            s_info = [
                    { 'configType': configType,
                      'name': configName,
                    'value': configValue
                    }
            ]
            results.append(s_info)

    return jsonify(results)

if __name__ == '__main__':
    use_port = load_conf()
    app.run(host='0.0.0.0', port=use_port)
