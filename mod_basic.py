import base64

from support import SupportSubprocess

from .setup import *


class ModuleBasic(PluginModuleBase):

    def __init__(self, P):
        super(ModuleBasic, self).__init__(P, name='basic', first_menu='setting', scheduler_desc='디스코드 봇 메시지 대기')
        self.db_default = {
            f'{self.name}_db_version' : '1',
            f'{self.name}_auto_start' : 'False',
            f'{self.name}_bot_token' : '',
        }
        self.process = None
        default_route_socketio_module(self, attach='/status')


    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        if sub == 'setting':
            arg['_status'] = self.process != None
        return render_template('{package_name}_{module_name}_{sub}.html'.format(package_name=P.package_name, module_name=self.name, sub=sub), arg=arg)
    

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {'ret':'success', 'json':None}
        if command == 'execute':
            if arg1 == 'true':
                self.start()
            else:
                self.stop()
        return jsonify(ret)


    def plugin_load(self):
        if P.ModelSetting.get_bool(f'{self.name}_auto_start'):
            self.start()
    
    
    def start(self):
        os.environ['DISCORD_BOT_TOKEN'] = P.ModelSetting.get(f'basic_bot_token')
        cmd = [os.environ['FF_PYTHON'], os.path.join(os.path.dirname(__file__), 'client.py')]
        self.process = SupportSubprocess(cmd, stdout_callback=self.stdout_callback, call_id=f"discord_bot_main", env=os.environ)
        self.process.start(join=False)


    def stop(self):
        if self.process != None:
            self.process.process_close()
            self.process = None


    def stdout_callback(self, call_id, mode, data):
        try:
            if mode == 'END':
                self.process = None
            if mode == 'LOG' and data.startswith('>>'):
                msg = json.loads(base64.b64decode(data[2:].encode()).decode())
                #logger.debug(d(msg))
                if msg['type'] == 'READY':
                    if msg['guild']:
                        F.socketio.emit('notify', {'type':'success', 'msg':f"디스코드 봇이 FlaskFarm 채널에 있습니다.<br>Role: {msg['role']}" }, namespace='/framework', broadcast=True)
                    else:
                        F.socketio.emit('notify', {'type':'warning', 'msg':"디스코드 봇이 FlaskFarm 채널에 없습니다." }, namespace='/framework', broadcast=True)
                if msg['type'] == 'FF':
                    self.process_ff(msg)
                elif msg['type'] == 'DM':
                    self.process_dm(msg)
                        
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(f"[{call_id}] [{mode}] [{data}]")

    
    def process_ff(self, data):
        try:
            if data['msg'].startswith('^') == False:
                return
            from support import SupportAES
            data['msg'] = json.loads(SupportAES.decrypt(data['msg'][1:]))
            #P.logger.error(d(data))
            target_plugin_name = data['msg'].get('t1')
            target_module_name = data['msg'].get('t2')
            target_page_name = data['msg'].get('t3')
            target_plugin_ins = None
            target_module_ins = None
            target_page_ins = None
            if target_plugin_name == None:
                logger.warning('target wrong')
                return
            try:
                target_plugin_ins = F.PluginManager.get_plugin_instance(target_plugin_name)
            except: pass

            if target_plugin_ins == None:
                return
            target_module_ins = target_plugin_ins.logic.get_module(target_module_name)
            if target_module_ins == None:
                return
            if target_page_name != None:
                target_page_ins = target_module_ins.get_page(target_page_name)
                if target_page_ins != None:
                    target_page_ins.process_discord_data(data)
            else:
                target_module_ins.process_discord_data(data)
        except Exception as e:
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())

    def process_dm(self, data):
        logger.debug(d(data))
        # reserved