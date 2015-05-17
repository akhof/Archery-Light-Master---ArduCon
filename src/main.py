#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import wx, urllib2, threading, time, sys, json, thread
import pyduino
import icon

__VERSION__ = 1.0

class reloadThread(threading.Thread):
    def __init__(self, mf, host, port):
        threading.Thread.__init__(self)
        self.mf = mf
        self.host = host
        self.port = port
    def run(self):
        lasthorn = -1
        
        lastrot = None
        lastgelb = None
        lastgruen = None
        lastab = None
        lastcd = None
        while True:
            try:
                if not self.mf.started:
                    continue
                
                try:
                    req = urllib2.Request("http://{}:{}/json-status".format(self.host, self.port))
                    result = urllib2.urlopen(req, timeout=2).read()
                except Exception as e:
                    msg = "[!!] Error while connect to server: '{}'  -  Try again in 3 secounds".format(e)
                    wx.CallAfter(self.mf.log, msg)
                    time.sleep(3)
                    continue
                
                try:
                    loaded = json.loads(result)
                except Exception as e:
                    msg = "[!!] Error while loading server's result(1): '{}'  -  Try again in 3 secounds".format(e)
                    wx.CallAfter(self.mf.log, msg)
                    time.sleep(3)
                    continue
                
                try:
                    rot = loaded["red"]
                    gelb = loaded["yellow"]
                    gruen = loaded["green"]
                    ab = loaded["ab"]
                    cd = loaded["cd"]
                    horn = int(loaded["horn"])
                except Exception as e:
                    msg = "[!!] Error while loading server's result(2): '{}'  -  Try again in 3 secounds".format(e)
                    wx.CallAfter(self.mf.log, msg)
                    time.sleep(3)
                    continue
                
                try:
                    if not (rot == lastrot and gelb == lastgelb and gruen == lastgruen and ab == lastab and cd == lastcd):
                        lastrot = rot
                        lastgelb = gelb
                        lastgruen = gruen
                        lastab = ab
                        lastcd = cd
    
                        print("Rot: {}\tGelb: {}\tGruen: {}\tAB: {}\tCD: {}\tHupe: {}".format(rot, gelb, gruen,ab, cd, horn))
                        wx.CallAfter(self.mf.setZustand,
                                     rot=rot, gelb=gelb, gruen=gruen, ab=ab, cd=cd)
                    
                    if time.time()-lasthorn > 1.5 and horn != 0:
                        lasthorn = time.time()
                        def dohorn():
                            for _ in range(horn):
                                wx.CallAfter(self.mf.setZustand, hupe=True)
                                time.sleep(0.25)
                                wx.CallAfter(self.mf.setZustand, hupe=False)
                        thread.start_new(dohorn, ())
                except Exception as e:
                    msg = "[!!] Error while loading server's result(3): '{}'  -  Try again in 3 secounds".format(e)
                    wx.CallAfter(self.mf.log, msg)
                    time.sleep(3)
                    continue
                
            finally:
                if self.mf.exit: return
                time.sleep(0.25)

class MainFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.label_server = wx.StaticText(self, wx.ID_ANY, "Server:")
        self.input_host = wx.TextCtrl(self, wx.ID_ANY, "localhost")
        self.label_dpunkt = wx.StaticText(self, wx.ID_ANY, ":")
        self.input_port = wx.SpinCtrl(self, wx.ID_ANY, "8080", min=0, max=1000000)
        self.label_arduino = wx.StaticText(self, wx.ID_ANY, "Arduino:")
        self.input_arduino = wx.TextCtrl(self, wx.ID_ANY, "/dev/ttyUSB0")
        self.sl1 = wx.StaticLine(self, wx.ID_ANY)
        self.label_pins = wx.StaticText(self, wx.ID_ANY, "Pin-Einstellungen:")
        self.label_rot = wx.StaticText(self, wx.ID_ANY, "Rot:")
        self.input_rot = wx.SpinCtrl(self, wx.ID_ANY, "2", min=0, max=50)
        self.label_gelb = wx.StaticText(self, wx.ID_ANY, "Gelb:")
        self.input_gelb = wx.SpinCtrl(self, wx.ID_ANY, "2", min=0, max=50)
        self.label_gruen = wx.StaticText(self, wx.ID_ANY, u"Gr\xfcn:")
        self.input_gruen = wx.SpinCtrl(self, wx.ID_ANY, "2", min=0, max=50)
        self.label_ab = wx.StaticText(self, wx.ID_ANY, "A / B:")
        self.input_ab = wx.SpinCtrl(self, wx.ID_ANY, "2", min=0, max=50)
        self.label_cd = wx.StaticText(self, wx.ID_ANY, "C / D:")
        self.input_cd = wx.SpinCtrl(self, wx.ID_ANY, "2", min=0, max=50)
        self.label_hupe = wx.StaticText(self, wx.ID_ANY, "Hupe:")
        self.input_hupe = wx.SpinCtrl(self, wx.ID_ANY, "2", min=0, max=50)
        self.sl2 = wx.StaticLine(self, wx.ID_ANY)
        self.button_start = wx.Button(self, wx.ID_ANY, "START")
        self.sl3 = wx.StaticLine(self, wx.ID_ANY)
        self.list_log = wx.ListBox(self, wx.ID_ANY, choices=["Achery Light Master - ArduCon v.{}".format(__VERSION__), u"Letzten 50 Einträge:", "="*40])
        
        self.SetTitle("Archery Light Master - ArduCon v.{}".format(__VERSION__))
        self.label_server.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.input_host.SetMinSize((160, 20))
        self.input_host.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.label_dpunkt.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.input_port.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.label_arduino.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.input_arduino.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.label_pins.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_rot.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.input_rot.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.label_gelb.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.input_gelb.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.label_gruen.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.input_gruen.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.label_ab.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.input_ab.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.label_cd.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.input_cd.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.label_hupe.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.input_hupe.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.button_start.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.list_log.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.list_log.SetSelection(0)
        
        sizer_1 = wx.FlexGridSizer(3, 3, 0, 0)
        sizer_2 = wx.FlexGridSizer(1, 3, 0, 15)
        sizer_3 = wx.FlexGridSizer(6, 1, 15, 0)
        sizer_6 = wx.FlexGridSizer(2, 6, 15, 15)
        sizer_4 = wx.FlexGridSizer(2, 2, 15, 15)
        sizer_5 = wx.FlexGridSizer(1, 3, 0, 10)
        sizer_1.Add((20, 20), 0, 0, 0)
        sizer_1.Add((20, 20), 0, 0, 0)
        sizer_1.Add((20, 20), 0, 0, 0)
        sizer_1.Add((20, 20), 0, 0, 0)
        sizer_4.Add(self.label_server, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_5.Add(self.input_host, 0, wx.EXPAND, 0)
        sizer_5.Add(self.label_dpunkt, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_5.Add(self.input_port, 0, wx.EXPAND, 0)
        sizer_4.Add(sizer_5, 1, wx.EXPAND, 0)
        sizer_4.Add(self.label_arduino, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_4.Add(self.input_arduino, 0, wx.EXPAND, 0)
        sizer_4.AddGrowableCol(1)
        sizer_3.Add(sizer_4, 1, wx.EXPAND, 0)
        sizer_3.Add(self.sl1, 0, wx.EXPAND, 0)
        sizer_3.Add(self.label_pins, 0, 0, 0)
        sizer_6.Add(self.label_rot, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_6.Add(self.input_rot, 0, wx.EXPAND, 0)
        sizer_6.Add(self.label_gelb, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_6.Add(self.input_gelb, 0, wx.EXPAND, 0)
        sizer_6.Add(self.label_gruen, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_6.Add(self.input_gruen, 0, wx.EXPAND, 0)
        sizer_6.Add(self.label_ab, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_6.Add(self.input_ab, 0, wx.EXPAND, 0)
        sizer_6.Add(self.label_cd, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_6.Add(self.input_cd, 0, wx.EXPAND, 0)
        sizer_6.Add(self.label_hupe, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_6.Add(self.input_hupe, 0, wx.EXPAND, 0)
        sizer_6.AddGrowableCol(1)
        sizer_6.AddGrowableCol(3)
        sizer_6.AddGrowableCol(5)
        sizer_3.Add(sizer_6, 1, wx.EXPAND, 0)
        sizer_3.Add(self.sl2, 0, wx.EXPAND, 0)
        sizer_3.Add(self.button_start, 0, wx.EXPAND, 0)
        sizer_2.Add(sizer_3, 1, wx.EXPAND, 0)
        sizer_2.Add(self.sl3, 0, wx.EXPAND, 0)
        sizer_2.Add(self.list_log, 0, wx.EXPAND, 0)
        sizer_2.AddGrowableRow(0)
        sizer_2.AddGrowableCol(2)
        sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)
        sizer_1.Add((20, 20), 0, 0, 0)
        sizer_1.Add((20, 20), 0, 0, 0)
        sizer_1.Add((20, 20), 0, 0, 0)
        sizer_1.Add((20, 20), 0, 0, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        sizer_1.AddGrowableRow(1)
        sizer_1.AddGrowableCol(1)
        self.Layout()
        self.Centre()
        
        self.Bind(wx.EVT_BUTTON, self.__startstop, self.button_start)
        self.Bind(wx.EVT_CLOSE, self.__close)
        
        #####################################
        self.started = False
        self.exit = False
        
        self.arduino = None
        
        self.reload = reloadThread(self, 0, 0)
        self.reload.start()
        
        self.Enable()
        
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        
        self.SetIcon(wx.IconFromBitmap(icon.geticonBitmap()))
    
    def log(self, msg):
        if len(self.list_log.GetItems()) == 53:
            self.list_log.Delete(3)
        self.list_log.Append(msg)
        self.list_log.Select(len(self.list_log.GetItems())-1)
    
    def setZustand(self, rot=None, gelb=None, gruen=None, ab=None, cd=None, hupe=None):
        if rot != None:
            self.__setPort(self.input_rot.GetValue(), rot)
        if gelb != None:
            self.__setPort(self.input_gelb.GetValue(), gelb)
        if gruen != None:
            self.__setPort(self.input_gruen.GetValue(), gruen)
        if ab != None:
            self.__setPort(self.input_ab.GetValue(), ab)
        if cd != None:
            self.__setPort(self.input_cd.GetValue(), cd)
        if hupe != None:
            self.__setPort(self.input_hupe.GetValue(), hupe)
        
    def __close(self, event):
        print("Exit...")
        self.exit = True
        self.Hide()
        wx.Yield()
        time.sleep(2)
        wx.Exit()
        sys.exit(0)
    
    def __setPort(self, pin, value):
        if value: value = 1
        else: value = 0
        self.arduino.digital[pin].write(value)
    
    def __startstop(self, event):
        if self.started:
            self.started = False
            
            try: self.arduino.exit()
            except: pass
                        
            self.httpClient = None
            self.arduino = None
            
            self.Enable()
            self.button_start.SetLabel("START")
            
            self.log("{0} CLOSE CONNECTION {0}".format("="*5))
        else:
            try:
                self.arduino = pyduino.Arduino(self.input_arduino.GetValue())
                
                pins = [self.input_rot.GetValue(), self.input_gelb.GetValue(), self.input_gruen.GetValue(),
                        self.input_ab.GetValue(), self.input_cd.GetValue(), self.input_hupe.GetValue()]
                for pin in pins:
                    self.arduino.digital[pin].set_active(1)
                    self.arduino.digital[pin].set_mode(pyduino.DIGITAL_OUTPUT)
                
                self.log("")
                self.log("Connected to Arduino-Board sucessfull! :)")
            except Exception as e:
                self.log("[!!] Cannot init Arduino-Board: {}".format(e))
                return
            
            self.reload.host = self.input_host.GetValue()
            self.reload.port = self.input_port.GetValue()
            
            self.started = True
            self.Disable()
            self.button_start.SetLabel("STOP")
    
    def Enable(self, enable=True):
        objs = [self.label_ab, self.label_cd, self.label_hupe, self.label_rot, self.label_gelb, self.label_gruen, self.label_arduino, self.label_server,
                self.input_ab, self.input_cd, self.input_hupe, self.input_rot, self.input_gelb, self.input_gruen, self.input_arduino, self.input_host, self.input_port, self.label_pins]
    
        for obj in objs:
            obj.Enable(enable)
    def Disable(self):
        self.Enable(False)
    
    
if __name__ == "__main__":
    print("Start 'Archery Light Master - ArduCon' v.{}".format(__VERSION__))
    
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = MainFrame(None, wx.ID_ANY, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
