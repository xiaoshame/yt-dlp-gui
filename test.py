import wx

class MyPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        
        button = wx.Button(self, label="Click Me")
        text = wx.TextCtrl(self)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(button, 0, wx.ALL, 10)
        sizer.Add(text, 0, wx.ALL, 10)
        self.SetSizer(sizer)

app = wx.App()
frame = wx.Frame(None, title="Panel Example")
panel = MyPanel(frame)
frame.SetSize(300, 200)
frame.Show()
app.MainLoop()