
class VSwitch(object):
    def __init__(self, object_id, backing_adapter_uri, port):
        self.object_id = object_id
        self.backing_adapter_uri = backing_adapter_uri
        self.port = port

    def get_property(self, name):
        if name == 'object-id':
            return self.object_id

VSWITCHES = [VSwitch("vswitch-uuid-1", "/api/adapters/uuid-1", 0),
             VSwitch("vswitch-uuid-2", "/api/adapters/uuid-2", 1),
             VSwitch("vswitch-uuid-3", "/api/adapters/uuid-3", 0)]

class VSwitchManager(object):
    def __init__(self, vswitches=VSWITCHES):
        self.vswitches = vswitches

    def find(self, **kwargs):
        for vswitch in self.vswitches:
            if (vswitch.backing_adapter_uri ==
                    kwargs.get('backing-adapter-uri') and vswitch.port ==
                    kwargs.get('port')):
                return vswitch


class CPC(object):

    def __init__(self, dpm_enabled=True):
        self.dpm_enabled = dpm_enabled
        self.vswitches = VSwitchManager()


