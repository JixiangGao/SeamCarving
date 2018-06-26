# -*- coding: utf-8 -*-
import wx
# from PIL import Image
import wx.lib.imagebrowser
import os
import cv2
from seamCarver_gray import SeamCarver
from PIL import Image
import numpy as np
import PIL
import PilToWx
import time
import threading

class SeamCarving(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(600, 400))
        self.Center(wx.BOTH)
        self.initFrame()
        self.flag = 0
        self.click_flag = 0
        self.img2_dir = ""
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # 记录矩形框点
        self.rect_Lpoint = (0, 0)
        self.rect_Rpoint = (0, 0)

        self.InitPaint()
        self.InitBuffer()

        self.carver = None
        self.last_mode = None

    def initFrame(self):
        icon = wx.Icon('icon.jpg', wx.BITMAP_TYPE_JPEG)
        self.SetIcon(icon)
        self.Show(True)
        self.initMenu()
        # self.bitmap = wx.StaticBitmap(self, -1)
        self.bitmap2 = wx.StaticBitmap(self, -1)
        self.directory = ""
        self.available = " "
        self.str = wx.StaticText(self, -1, u"原图像：" + self.available, pos=(20, 10))
        self.init_bottom()

        self.img = None
        self.mask_flag = 0

    def init_bottom(self):
        size = self.GetClientSize()

        self.gen_str = wx.StaticText(self, -1, u"生成图像：" + self.available, pos=(int(size.GetWidth()/2), 10))

        # Bottom

        # current process
        self.curr_button = wx.Button(self, wx.ID_OPEN, u"Realtime", pos=(15, size.GetHeight()-80))
        self.curr_button.Bind(wx.EVT_BUTTON, self.current_process, id=wx.ID_OPEN)

        # removal
        self.removal_button = wx.Button(self, wx.ID_OPEN, u'Removal', pos=(125, size.GetHeight()-80))
        self.removal_button.Bind(wx.EVT_BUTTON, self.removal_process, id=wx.ID_OPEN)


        # re-show
        self.reShow_button = wx.Button(self, wx.ID_OPEN, u'Re-Show', pos = (235, size.GetHeight()-80))
        self.reShow_button.Bind(wx.EVT_BUTTON, self.reShow_process, id=wx.ID_OPEN)

        # face-detection
        self.face_button = wx.Button(self, wx.ID_OPEN, u'Face Detection', pos=(345, size.GetHeight()-80))
        self.face_button.Bind(wx.EVT_BUTTON, self.face_detection, id=wx.ID_OPEN)

        # select combobox
        choices = ['Gray', 'Rgb']
        self.combobox = wx.ComboBox(self, -1, pos=(470, size.GetHeight()-80), size=(80, -1),
                    choices=choices, style=wx.CB_READONLY, value='Gray')
        self.Bind(wx.EVT_COMBOBOX, self.OnSelect)

        self.width_str = wx.StaticText(self, -1, u"width:", pos=(15, size.GetHeight() - 35))
        self.w_text = wx.TextCtrl(self, -1, "100", size=(70, -1), pos=(60, size.GetHeight() - 40))

        self.height_str = wx.StaticText(self, -1, u"height:", pos=(150, size.GetHeight() - 35))
        self.h_text = wx.TextCtrl(self, -1, "100", size=(70, -1), pos=(195, size.GetHeight() - 40))

        self.transform_button = wx.Button(self, wx.ID_OK, U"Transform", pos=(300, size.GetHeight() - 40))
        self.transform_button.SetDefault()
        self.transform_button.Bind(wx.EVT_BUTTON, self.OnTransform, id=wx.ID_OK)

        # protect
        self.protect_button = wx.Button(self, wx.ID_OPEN, u'Protect', pos=(410, size.GetHeight() - 40))
        self.protect_button.Bind(wx.EVT_BUTTON, self.protect_process, id=wx.ID_OPEN)

    def re_pos_bottom(self):
        size = self.GetClientSize()
        self.gen_str.SetPosition((int(size.GetWidth()/2), 10))
        self.curr_button.SetPosition((15, size.GetHeight()-80))
        self.removal_button.SetPosition((125, size.GetHeight()-80))
        self.reShow_button.SetPosition((235, size.GetHeight()-80))
        self.face_button.SetPosition((345, size.GetHeight()-80))
        self.combobox.SetPosition((470, size.GetHeight()-80))
        self.width_str.SetPosition((15, size.GetHeight() - 35))
        self.w_text.SetPosition((60, size.GetHeight() - 40))
        self.height_str.SetPosition((150, size.GetHeight() - 35))
        self.h_text.SetPosition((195, size.GetHeight() - 40))
        self.transform_button.SetPosition((300, size.GetHeight() - 40))
        self.protect_button.SetPosition((410, size.GetHeight()-40))

    def initMenu(self):
        menu = wx.MenuBar()
        self.SetMenuBar(menu)

        self.m1 = wx.Menu()
        ID_OPEN = wx.NewId()
        self.m1.Append(ID_OPEN, u"打开(&O)\tCtrl+O")
        # ID_DOWNLOAD = wx.NewId()
        # self.m1.Append(ID_DOWNLOAD, u"下载验证码(&D)\tCtrl+D")
        self.ID_MASK = wx.NewId()
        self.m1.Append(self.ID_MASK, u"Mask(&A)\tCtrl+Alt+O")
        # self.m1.Enable(self.ID_SAVE, False)
        self.m1.Append(wx.ID_EXIT, u"退出(&X)\tCtrl+X")
        menu.Append(self.m1, u"打开(&O)")

        m4 = wx.Menu()
        ID_ABOUT = wx.NewId()
        m4.Append(ID_ABOUT, u"程序信息(&I)\tF1")
        menu.Append(m4, u"关于(&A)")

        self.Bind(wx.EVT_MENU, self.OnOpen, id=ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnMask, id=self.ID_MASK)
        self.Bind(wx.EVT_MENU, self.OnExit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=ID_ABOUT)

    def set_result(self):
        size = self.GetClientSize()
        '''''wx.Image'''
        wxImg = PilToWx.PilImg2WxImg(self.result)
        '''''wx.Bitmap'''
        bitmap2 = wx.BitmapFromImage(wxImg)

        # self.bitmap2.SetBitmap(bitmap2)
        # self.bitmap2.SetPosition((int(size.GetWidth()) / 2 + 5, 35))

        # jpg = wx.Image('result.jpg', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        # # self.img = jpg
        self.InitBuffer()
        self.shapes = []
        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        dc.DrawBitmap(bitmap2, int(size.GetWidth()) / 2 + 5, 35, False)
        self.Draw(dc)

    def OnTransform(self, evt):
        image = cv2.imread(self.directory)
        carver = SeamCarver(image)
        self.carver = carver
        self.last_mode = 'resize'

        thread_obj = threading.Thread(target=self.son_thread, args=(carver,))
        thread_obj.start()
        print('transfer done')

    def son_thread(self, carver):
        carver.resize_aim(int(self.h_text.GetValue()), int(self.w_text.GetValue()))
        carver.get_resize_seams()

        max_w = carver.image.shape[1] if carver.image.shape[1] > int(self.w_text.GetValue()) \
            else int(self.w_text.GetValue())
        max_h = carver.image.shape[0] if carver.image.shape[0] > int(self.h_text.GetValue()) \
            else int(self.h_text.GetValue())
        self.resize_win(max_w, max_h)

        flag = True
        while flag:
            self.result, flag = carver.showing_process(mode='resize')
            self.set_result()
            time.sleep(0.1)

        cv2.imwrite('result.jpg', cv2.cvtColor(self.result, cv2.COLOR_RGB2BGR))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Refresh()
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def InitPaint(self):

        self.x1, self.x2, self.y1, self.y2 = 0, 0, 0, 0
        self.iscaptured = -1
        self.p1 = (0, 0)
        self.p2 = (0, 0)
        self.st = 'rect'
        self.pos = (0, 0)
        self.pen = wx.Pen("green", 2, wx.SOLID)
        self.brush = wx.Brush('', wx.TRANSPARENT)  # 透明填充
        self.shapes = []

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOTION, self.OnMotion)

    def InitBuffer(self):
        size = self.GetClientSize()
        mm = wx.DisplaySize()  # 获取屏幕大小
        self.buffer = wx.Bitmap(mm[0], mm[1])
        dc = wx.BufferedDC(None, self.buffer)
        dc.SetPen(self.pen)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.SetBrush(self.brush)
        dc.Clear()
        self.Draw(dc)
        return dc

    def OnLeftDown(self, event):
        self.p1 = event.GetPosition()
        self.rect_Lpoint = self.p1
        self.x1, self.y1 = self.p1

        self.CaptureMouse()  # 6 捕获鼠标
        self.iscaptured = 1

    def OnLeftUp(self, event):
        self.rect_Rpoint = event.GetPosition()
        if self.iscaptured == 1:
            self.ReleaseMouse()  # 7 释放鼠标
            self.p2 = event.GetPosition()
            x1, y1 = self.p1
            x2, y2 = self.p2
            self.shapes.append((self.st, (x1, y1, x2, y2)))
            self.InitBuffer()
            self.iscaptured = 0

    def OnMotion(self, event):
        if event.Dragging() and event.LeftIsDown():  # 8 确定是否在拖动
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)  # 9 创建另一个缓存的上下文
            self.drawMotion(dc, event)
        event.Skip()

    def drawMotion(self, dc, event):
        if self.iscaptured == 1:
            self.p2 = event.GetPosition()
            x1, y1 = self.p1
            x2, y2 = self.p2
            self.shapes.append((self.st, (x1, y1, x2, y2)))
            self.InitBuffer()
            self.shapes.pop(len(self.shapes) - 1)

    def Draw(self, dc):

        if self.img != None:
            dc.DrawBitmap(self.img, 20, 35, False)
        self.draw_border_line(dc)
        dc.SetPen(self.pen)
        for st, (x1, y1, x2, y2) in self.shapes:
            if st == 'line':
                dc.DrawLine(x1, y1, x2, y2)
            elif st == 'oval':
                dc.DrawEllipse(x1, y1, x2 - x1, y2 - y1)
            elif st == 'rect':
                dc.DrawRectangle(x1, y1, x2 - x1, y2 - y1)

    def removal_process(self, evt):
        self.pen = wx.Pen("green", 2, wx.SOLID)
        print("rect:", self.rect_Lpoint, self.rect_Rpoint)
        self.InitPaint()
        dc = self.InitBuffer()
        self.shapes = []
        self.Draw(dc)

        # 处理图片
        image = cv2.imread(self.directory)
        carver = SeamCarver(image)
        self.carver = carver
        self.last_mode = 'removal'

        thread_obj = threading.Thread(target=self.removal_thread, args=(carver,))
        thread_obj.start()
        print('removal done')

        return

    def removal_thread(self, carver):
        removal_flag_arr = np.zeros(carver.image.shape[:2])

        min_x = min(self.rect_Lpoint[0], self.rect_Rpoint[0]) - 20
        min_x = 0 if min_x < 0 else min_x
        max_x = max(self.rect_Lpoint[0], self.rect_Rpoint[0]) - 20
        max_x = carver.image.shape[1] if max_x > carver.image.shape[1] else max_x

        min_y = min(self.rect_Lpoint[1], self.rect_Rpoint[1]) - 35
        min_y = 0 if min_y < 0 else min_y
        max_y = max(self.rect_Lpoint[1], self.rect_Rpoint[1]) - 35
        max_y = carver.image.shape[0] if max_y > carver.image.shape[0] else max_y

        for x in range(min_x, max_x-1):
            for y in range(min_y, max_y):
                removal_flag_arr[y][x] = 1

        # 处理
        if self.mask_flag == 0:
            carver.remove_aim(removal_flag_arr)
        else:
            carver.remove_aim(self.mask_img)
            self.mask_flag = 0

        carver.get_removal_seams()

        flag = True
        while flag:
            self.result, flag = carver.showing_process(mode='removal')
            self.set_result()
            time.sleep(0.1)

        cv2.imwrite('result.jpg', cv2.cvtColor(self.result, cv2.COLOR_RGB2BGR))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Refresh()
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def protect_process(self, evt):
        self.pen = wx.Pen("green", 2, wx.SOLID)
        print("rect:", self.rect_Lpoint, self.rect_Rpoint)
        self.InitPaint()
        dc = self.InitBuffer()
        self.shapes = []
        self.Draw(dc)

        # 处理图片
        image = cv2.imread(self.directory)
        carver = SeamCarver(image)
        self.carver = carver
        self.last_mode = 'resize'

        thread_obj = threading.Thread(target=self.protect_thread, args=(carver,))
        thread_obj.start()
        print('protect done')

        return

    def protect_thread(self, carver):
        removal_flag_arr = np.zeros(carver.image.shape[:2])

        min_x = min(self.rect_Lpoint[0], self.rect_Rpoint[0]) - 20
        min_x = 0 if min_x < 0 else min_x
        max_x = max(self.rect_Lpoint[0], self.rect_Rpoint[0]) - 20
        max_x = carver.image.shape[1] if max_x > carver.image.shape[1] else max_x

        min_y = min(self.rect_Lpoint[1], self.rect_Rpoint[1]) - 35
        min_y = 0 if min_y < 0 else min_y
        max_y = max(self.rect_Lpoint[1], self.rect_Rpoint[1]) - 35
        max_y = carver.image.shape[0] if max_y > carver.image.shape[0] else max_y

        for x in range(min_x, max_x-1):
            for y in range(min_y, max_y):
                removal_flag_arr[y][x] = 1

        # 处理
        carver.protect_resize_aim(int(self.h_text.GetValue()), int(self.w_text.GetValue()), removal_flag_arr)
        carver.get_resize_seams(protect=True)

        max_w = carver.image.shape[1] if carver.image.shape[1] > int(self.w_text.GetValue()) \
            else int(self.w_text.GetValue())
        max_h = carver.image.shape[0] if carver.image.shape[0] > int(self.h_text.GetValue()) \
            else int(self.h_text.GetValue())
        self.resize_win(max_w, max_h)

        flag = True
        while flag:
            self.result, flag = carver.showing_process(mode='resize')
            self.set_result()
            time.sleep(0.1)

        cv2.imwrite('result.jpg', cv2.cvtColor(self.result, cv2.COLOR_RGB2BGR))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Refresh()
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def face_detection(self, evt):
        import face_detection as detection
        face = detection.face_detection(self.directory)

        self.rect_Lpoint = (face[0][0], face[0][1])
        self.rect_Rpoint = (face[0][0]+face[0][2], face[0][1]+face[0][3])

        jpg = wx.Image('face.jpg', wx.BITMAP_TYPE_ANY).ConvertToBitmap()

        self.img = jpg
        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        dc.DrawBitmap(jpg, 20, 35, False)
        return

    def reShow_process(self, evt):
        thread_obj = threading.Thread(target=self.reShow_thread, args=())
        thread_obj.start()
        print('Re-Show done')

    def reShow_thread(self):
        self.carver.refresh()
        flag = True
        while flag:
            self.result, flag = self.carver.showing_process(mode=self.last_mode)
            self.set_result()
            time.sleep(0.1)

    def resize_win(self, w, h):
        win_w = 600 if w * 2 < 600 - 70 else w * 2 + 70
        win_h = 400 if h < 400 - self.bottom - 100 else h + self.bottom + 100

        self.SetSize((win_w, win_h))
        self.re_pos_bottom()

    def OnSelect(self, evt):
        item = evt.GetSelection()
        print (item)
        if item == 1:
            from seamCarver_bgr import SeamCarver
        else:
            from seamCarver_gray import SeamCarver

    def OnOpen(self, evt):
        dialog = wx.lib.imagebrowser.ImageDialog(None)
        if dialog.ShowModal() == wx.ID_OK:
            self.directory = dialog.GetFile()
            self.Bind(wx.EVT_PAINT, self.OnPaint)
            self.flag = 1
            try:
                # image = wx.Image(self.directory, wx.BITMAP_TYPE_ANY)
                # self.bitmap.SetBitmap(image.ConvertToBitmap())
                jpg = wx.Image(self.directory, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
                self.img = jpg
                self.InitBuffer()
                self.shapes = []
                dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
                # dc.DrawBitmap(jpg, 20, 35, False)
                self.Draw(dc)
            except Exception as e:
                print(e)
                wx.MessageBox(u"图片格式错误", u"ERROR", wx.OK | wx.ICON_INFORMATION, self)
                self.directory = self.available
                if self.available == " ":
                    self.flag = 0
            else:
                self.available = self.directory
                # self.bitmap.SetPosition((20, 40))

        self.str.SetLabel(u"图像文件：" + self.available)
        # self.str.SetFont(wx.Font(10, wx.DECORATIVE, wx.NORMAL, wx.BOLD))
        if self.flag == 1:
            self.image = wx.Image(self.directory, wx.BITMAP_TYPE_ANY)

            w = self.image.GetWidth()
            h = self.image.GetHeight()

            # 根据图片大小调整窗口大小
            self.resize_win(w, h)


            # 初始化输入框的值
            self.w_text.SetValue(str(w))
            self.h_text.SetValue(str(h))

            # self.bitmap.SetBitmap(self.image.ConvertToBitmap())
            # self.bitmap.SetPosition((20, 35))

            # Left down & up
            # self.bitmap.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
            # self.bitmap.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)

        dialog.Destroy()
        self.Refresh()

    def OnMask(self, evt):
        dialog = wx.lib.imagebrowser.ImageDialog(None)
        if dialog.ShowModal() == wx.ID_OK:
            self.mask_img = cv2.imread(dialog.GetFile(), 0)
            self.mask_flag = 1


    def OnSave(self, evt):
        wildcard = "Text Files (*.txt)|*.txt|" \
                   "All files (*.*)|*.*"
        dialog = wx.FileDialog(None, "Choose a file", os.getcwd(),
                               "", wildcard, wx.SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            file = open(dialog.GetPath(), 'w')
            file.write(self.result)
            file.close()
            self.m1.Enable(self.ID_SAVE, False)
        dialog.Destroy()
        self.Refresh()

    def OnExit(self, evt):
        self.Close()

    def OnAbout(self, event):
        wx.MessageBox(u"多媒体作业\nSeam Carving\n\n\n学号：10152130206\n姓名：高吉祥\n\n学号：10152130219\n姓名：颜定坤\n"
                      , u"Seam Carving", wx.OK | wx.ICON_INFORMATION, self)

    def OnPaint(self, evt):

        wx.BufferedPaintDC(self, self.buffer)  # 处理一个paint（描绘）请求

        dc = wx.PaintDC(self)
        self.draw_border_line(dc)

    def draw_border_line(self, dc):
        size = self.GetClientSize()
        lineColor = '#000000'
        pen = wx.Pen(lineColor)
        pen.SetCap(wx.CAP_PROJECTING)
        dc.SetPen(pen)

        # Draw line
        self.bottom = 90
        dc.DrawLine(15, 30, 15, size.GetHeight() - self.bottom)
        dc.DrawLine(15, 30, size.GetWidth() - 15, 30)
        dc.DrawLine(size.GetWidth() - 15, 30, size.GetWidth() - 15, size.GetHeight() - self.bottom)
        dc.DrawLine(15, size.GetHeight() - self.bottom, size.GetWidth() - 15, size.GetHeight() - self.bottom)

        # middle line
        dc.DrawLine(int(size.GetWidth()/2), 30, int(size.GetWidth()/2), size.GetHeight() - self.bottom)

    def current_process(self, evt):
        a = SubFrame(None, title='Seam Carving')
        a.show_image(self.directory)


class SubFrame(wx.Frame):
    def __init__(self, parent, title):
        # wx.Frame.__init__(self, parent, title=title, size=(600, 400), style=wx.CLIP_CHILDREN)
        wx.Frame.__init__(self, parent, title=title, size=(600, 400), style = wx.DEFAULT_FRAME_STYLE  )
        # self.Center(wx.BOTH)
        self.Centre()
        self.initFrame()
        self.flag = 0
        self.click_flag = 0
        self.img2_dir = ""
        self.Bind(wx.EVT_PAINT, self.OnPaint)


    def initFrame(self):
        icon = wx.Icon('icon.jpg', wx.BITMAP_TYPE_JPEG)
        self.SetIcon(icon)
        self.Show(True)
        # self.Bind(wx.EVT_SIZE, self.OnSize)

        # 初始化终态size
        self.img_size = (-1, -1)

        # 每次线程调用时间
        self.delay = 0.5

        # 标记线程是否启用
        self.thread_flag = False




    def show_image(self, path):
        self.path = path
        self.bitmap = wx.StaticBitmap(self, -1)
        image = wx.Image(path, wx.BITMAP_TYPE_ANY)
        self.SetClientSize((image.GetWidth(), image.GetHeight()))
        self.bitmap.SetBitmap(image.ConvertToBitmap())

        self.image = cv2.imread(self.path)

        # 启用线程
        thread_obj = threading.Thread(target=self.son_thread, args=())
        thread_obj.start()

    # def OnSize(self, evt):
    #     # image = cv2.imread(self.path)
    #     # self.result = image

    def son_thread(self):
        carver = SeamCarver(self.image)

        while True:
            size = self.GetClientSize()
            print (size)

            self.result = carver.realtime_resize(int(size.GetWidth()), int(size.GetHeight()))
            print(type(self.result))
            self.set_result()

            # cv2.imwrite('result.jpg', cv2.cvtColor(self.result, cv2.COLOR_RGB2BGR))
            time.sleep(0.1)
        # self.Bind(wx.EVT_PAINT, self.OnPaint)
        # self.Refresh()
        # self.Bind(wx.EVT_PAINT, self.OnPaint)

    def set_result(self):
        '''''wx.Image'''
        wxImg = PilToWx.PilImg2WxImg(self.result)
        '''''wx.Bitmap'''
        bitmap = wx.BitmapFromImage(wxImg)
        # '''''wx.StaticBitmap'''
        # self.bitmap2 = wx.StaticBitmap(self, -1, wxImg)
        self.bitmap.SetBitmap(bitmap)

        # self.bitmap.SetPosition((int(size.GetWidth()) / 2 + 5, 35))

    def OnPaint(self, evt):
        return


if __name__ == '__main__':
    app = wx.App()
    SeamCarving(None, title='Seam Carving')
    app.MainLoop()
