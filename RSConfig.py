import ConfigParser

from itertools import izip, cycle

def load():
    config = dict()

    cp = ConfigParser.ConfigParser()

    try:
        cp.read("config.ini")
       
        # convert the config file to a dict
        for sec in cp.sections():
            config[sec] = dict()
            for item in cp.items(sec):
                config[sec][item[0]] = item[1]
    except:
        pass
      
    return config        

def save(config):

    existing = load()

    cp = ConfigParser.ConfigParser()

    # add existing config
    for sec in existing.keys():
        if not cp.has_section(sec):
            cp.add_section(sec)
            
        for item in existing[sec].keys():
            cp.set(sec, item, existing[sec][item])

    # update with new settings
    for sec in config.keys():
        if not cp.has_section(sec):
            cp.add_section(sec)
            
        for item in config[sec].keys():
            cp.set(sec, item, config[sec][item])
    
    cp.write(open("config.ini", "w"))


# more for obfuscation than anything else
def xor_crypt_string(data):
    return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(data, cycle("xdoiV82HRbXagtlAECZFIiSDcRftaYfwc031G34e7Amrc0H9VUhhbkjwjRzMysX")))

