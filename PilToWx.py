# -*- coding: utf-8 -*-

from PIL import Image
import wx


def PilImg2WxImg(Image):
    '''''PIL的image转化为wxImage'''
    try:
        image = wx.EmptyImage(Image.shape[1], Image.shape[0])
    except:
        pass
    image.SetData(Image.tobytes())
    # image.SetAlphaData(pilImg.convert("RGBA").tobytes()[3::4])
    # image.SetData(pilImg.convert("RGBA").tobytes()[3::4])
    return image


def WxImg2PilImg(wxImg):
    '''''wxImage转化为PIL的image'''
    pilImage = Image.new('RGB', (wxImg.GetWidth(), wxImg.GetHeight()))
    pilImage.fromstring(wxImg.GetData())
    if wxImg.HasAlpha():
        pilImage.convert('RGBA')
        wxAlphaStr = wxImg.GetAlphaData()
        pilAlphaImage = Image.fromstring('L', (wxImg.GetWidth(), wxImg.GetHeight()), wxAlphaStr)
        pilImage.putalpha(pilAlphaImage)
    return pilImage