import dearpygui.dearpygui as dpg

from file_browser import FileBrowser
from keys import keys
from tk_file_dialog import CreateFileDialog_Open, CreateFileDialog_SaveToFolder

import os
import sys
import win32clipboard
from io import BytesIO
import ctypes
import webbrowser
import configparser
import pywinstyles
import time

import numpy as np
import cv2
import random
import threading
from Font.funcs import putTTFText

from PIL import Image

cv2.putTTFText = putTTFText

def resource_path(relative_path):
    if getattr(sys, "frozen", False):  # exe
        base_path = os.path.dirname(sys.executable)
    else:  # скрипт
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

user32 = ctypes.windll.user32

user32.SetProcessDPIAware()

screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)

def get_hwnd():
    return user32.FindWindowW(None, "RetroImageViewer")

if not os.path.exists(resource_path("output")):
    os.makedirs(resource_path("output"))
    print("No output folder. Creating...")
else:
    print("Output folder detected.")

img_l = None

SW_MINIMIZE = 6
SW_RESTORE = 9
SW_MAXIMIZE = 3
SW_SHOWDEFAULT = 10

isMaximized = False
isMaximized_xd = False
isDragging = False

img_tag = 0
int_img_tag = 0

img_is_loaded = False
#срывать list через таймер или через скалинг
useImagePreview = True
isPreviewDisabled = False
current_selected_image_item = None
image_list_loaded = False
image_from_list = [] #передавать индекс в list
image_items_tags = []
image_item_tag = None
image_list_frame_size = 10
is_frame_refreshed = False
#проверка на нажатие предмета что бы не менять рамку
custom_decorator = False

isEditMode = True
isEditModeEnabled = False

image_path = None
show_wv = True

useOpenCV = True
useThreading = True
useResizing = True
resize_res = 2000
resize_factor = 2.0

img_save_num = 0
img_channels = 0
scale = 0.8675 #0.8645
scale_mod = 1.15
title_offset = -45
dynamic_theming = True

msg_timer_start = 0

config = configparser.ConfigParser()

if os.path.isfile(resource_path("settings.ini")):
    print("Config file detected.")
else:
    print("No config file. Creating...")
    config['FIRST_LAUNCH'] = {'First_launch': 'True'}
    config['UI'] =    {'isspacing': 'True',
                         'intspacing': '0.0',}
    config['Theme'] =  { 'dynamic_theme_image': 'True'}
    config['Behaviour'] = {'zoom_mod': '1.15'}
    config['Mechanics'] = {'loading_thread': 'True',
                            'isresize': 'True',
                            'resizeres': '2000',
                            'resizefactor': '1.5'}

    with open(resource_path("settings.ini"), "w") as configfile:
        config.write(configfile)

config.read(resource_path("settings.ini"))

isFirstLaunch = config.getboolean("FIRST_LAUNCH", "First_launch")
scale_mod = config.getfloat("Behaviour", "zoom_mod")
useThreading = config.getboolean("Mechanics", "loading_thread")
useResizing = config.getboolean("Mechanics", "isresize")
resize_res = config.getint("Mechanics", "resizeres")
resize_factor = config.getfloat("Mechanics", "resizefactor")

print(f"\nThreading: {useThreading}")
print(f"Resizing: {useResizing}\n")

if isFirstLaunch == True:
    print("First launch: ", isFirstLaunch)
    with open(resource_path("settings.ini"), "w") as configfile:
        isFirstLaunch = False
        config.set('FIRST_LAUNCH', 'First_launch', 'False')
        config.write(configfile)

print("Screen resolution:",screen_w,"x",screen_h)

def save_settings():
    config['FIRST_LAUNCH']['First_launch'] = str(isFirstLaunch)
    config['UI']['isspacing'] = str(settings_ui.spacing)
    config['UI']['intspacing'] = str(settings_ui.spacing_set)
    config['Theme']['dynamic_theme_image'] = str(Theme.dynamic_theming)
    config['Behaviour']['zoom_mod'] = str(scale_mod)
    config['Mechanics']['loading_thread'] = str(useThreading)
    config['Mechanics']['isresize'] = str(useResizing)
    config['Mechanics']['resizeres'] = str(resize_res)
    config['Mechanics']['resizefactor'] = str(resize_factor)

    with open(resource_path("settings.ini"), "w") as f:
        config.write(f)
        print("New settings saved into settings.ini")
        MenuBar.show_message("Settings saved.")

def show_selected_file(sender, files, cancel_pressed):
	if not cancel_pressed:
		dpg.set_value('selected_file', files[0])

def debug_output():
    print("+")

def dynamic_img_theme(rgb):
    color = rgb
    color = bgr2rgb(color)
    with dpg.theme() as dynamic_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, color)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (color[0]-25,color[1]-25,color[2]-25))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (color[0]-25,color[1]-25,color[2]-25))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (color[0]-35,color[1]-35,color[2]-35))
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (color[0]-25,color[1]-25,color[2]-25))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (color[0],color[1],color[2]))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered,  (color[0],color[1],color[2]))
            dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.5, 0.5)
            img_avg_col2 = (img_avg_col[0]-35,img_avg_col[1]-35,img_avg_col[2]-35)
            pywinstyles.change_header_color(get_hwnd(), color=rgb2hex(img_avg_col2))
            pywinstyles.change_title_color(get_hwnd(), color="white")

    with dpg.theme() as dynamic_theme_node:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvNodeCol_GridBackground,  (color[0]-35,color[1]-35,color[2]-35),category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_GridLine, (color[0]-55,color[1]-65,color[2]-55), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBar, (color[0], color[1], color[2], 175), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, (color[0], color[1], color[2], 200), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, (color[0], color[1], color[2], 215), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, (color[0], color[1], color[2], 0), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_NodeBackground,  (0,0,0, 150), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_NodeBackgroundHovered,  (0,0,0, 150), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_NodeBackgroundSelected,  (0,0,0, 150), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_Pin,  (color[0], color[1], color[2], 255), category=dpg.mvThemeCat_Nodes)



    with dpg.theme() as dynamic_theme_tansparent:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (color[0], color[1], color[2], 100))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (color[0]-25, color[1]-25, color[2]-25, 175))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (color[0]-25, color[1]-25, color[2]-25, 175))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (color[0]-35,color[1]-35,color[2]-35, 100))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, (65, 65, 65, 200))

            dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive, (0, 0, 0, 0))

            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (color[0]-25, color[1]-25, color[2]-25, 200))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (color[0], color[1], color[2], 200))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (color[0]+15, color[1]+15, color[2]+15, 200))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (color[0]+15, color[1]+15, color[2]+15, 200))

    with dpg.theme() as dynamic_button_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (color[0]+75, color[1]+75, color[2]+75, 175))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (color[0]+25, color[1]+25, color[2]+25, 175))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (color[0]+25, color[1]+25, color[2]+25, 175))
            #dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (0,0,255,0))
            #dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (color[0]-25, color[1]-25, color[2]-25, 175))
            #dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (color[0]-25, color[1]-25, color[2]-25, 175))


    dpg.bind_item_theme("main_window", dynamic_theme) #создавать мини окна от размера этого, а не от вьюпорта или экрана
    dpg.bind_item_theme("menu_bar", dynamic_theme)
    dpg.bind_item_theme("menu_btn1", dynamic_theme)
    dpg.bind_item_theme("menu_btn2", dynamic_theme)
    dpg.bind_item_theme("menu_btn3", dynamic_theme)
    dpg.bind_item_theme("menu_btn5", dynamic_theme)
    dpg.bind_item_theme("menu_btn6", dynamic_theme)
    dpg.bind_item_theme("list_window", dynamic_theme_tansparent)
    dpg.bind_item_theme("images_horizontal_group", dynamic_button_theme)
    dpg.bind_item_theme("img_node_window", dynamic_theme_node)
    dpg.bind_item_theme("node_window", dynamic_theme_node)
    dpg.bind_theme(dynamic_theme)

small_app_icon = resource_path("icons/16_ico_n.ico")
large_app_icon = resource_path("icons/256_ico_n.ico")

def bgr2rgb(color):
    rgb_color = int(color[2]), int(color[1]), int(color[0])
    return rgb_color

def rgb2hex(color):
    color = bgr2rgb(color)
    r = max(0, min(255, int(color[0])))
    g = max(0, min(255, int(color[1])))
    b = max(0, min(255, int(color[2])))
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

class Window:
    @staticmethod

    def minimize_window():
        hwnd = get_hwnd()
        if hwnd:
            user32.ShowWindow(hwnd, SW_MINIMIZE)

    def restore_window():
        hwnd = get_hwnd()
        if hwnd:
            user32.ShowWindow(hwnd, SW_RESTORE)

    def maximize_window():
        global isMaximized
        hwnd = get_hwnd()
        if hwnd:
            if not isMaximized:
                user32.ShowWindow(hwnd, SW_MAXIMIZE)
                isMaximized = True
            else:
                user32.ShowWindow(hwnd, SW_SHOWDEFAULT)
                isMaximized = False

    def maximize_window_xd():
        global isMaximized_xd
        hwnd = get_hwnd()
        if hwnd:
            if not isMaximized_xd:
                user32.ShowWindow(hwnd, SW_MAXIMIZE)
                isMaximized_xd = True

    def app_close():
        dpg.stop_dearpygui()

class MenuBar:
    @staticmethod

    def save_btn():
        global img, img_save_num
        img_save_num +=1
        image_name = "img_"+str(random.randint(0,99999999999))+".jpg"
        save_img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        cv2.imwrite(resource_path("output/"+image_name), save_img)
        print(f"Image saved in output/{image_name}.")

    def save_as_btn():
        global img, img_save_num
        img_save_num +=1
        save_img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        save_path = CreateFileDialog_SaveToFolder()
        cv2.imwrite(save_path, save_img)
        print(f"Image saved in {save_path}.")
        MenuBar.show_message(f"Saved:\n{os.path.basename(save_path)}")

    def show_edit_rgb_shift():
        dpg.show_item("cv_rgb_shift")

    def show_edge_detection():
        dpg.show_item("cv_edge_d")

    def show_edit_text():
        dpg.show_item("cv_text")

    def show_preview_list():
        global isPreviewDisabled
        if dpg.is_item_visible("list_window"):
            dpg.hide_item("list_window")
            isPreviewDisabled = True
        else:
            isPreviewDisabled = False
            dpg.show_item("list_window")


    def show_edit_mode():
        global isEditModeEnabled, isPreviewDisabled
        isPreviewDisabled = not isPreviewDisabled
        if isEditMode:
            if dpg.is_item_visible("img_node_window"):
                dpg.hide_item("img_node_window")
                dpg.hide_item("node_window")
            else:
                isEditModeEnabled = True
                dpg.show_item("img_node_window")
                dpg.show_item("node_window")

    def show_node_list():
        if dpg.is_item_visible("node_add_window"):
            dpg.hide_item("node_add_window")
                #dpg.hide_item("node_add_window")
        else:
            dpg.show_item("node_add_window")
                #dpg.show_item("node_add_window")

    def show_dialogue(sender):
        dpg.show_item("file_dialog_ext")

    def show_dialogue_tk():
        open_image_tk()

    def show_settings():
        dpg.show_item("settings_window")

    def show_info():
        dpg.show_item("info_window")

    def show_message(message="hello there"):
        global msg_timer_start
        dpg.show_item("message_window")
        dpg.configure_item("message_text", default_value=message,pos=[35, 40])
        msg_timer_start = time.perf_counter()

    def msg_timer():
        if dpg.is_item_shown("message_window"):
            elapsed = time.perf_counter() - msg_timer_start
            if elapsed >= 2.5:
                dpg.hide_item("message_window")


    def show_about():
        webbrowser.open("https://github.com/RetroMaidRage/RetroImageViewer")

class settings_ui:
    spacing = config.getboolean("UI", "isspacing")
    spacing_set = config.getfloat("UI", "intspacing")
    scaling_set = config.getfloat("Behaviour", "zoom_mod")
    useThreading = config.getboolean("Mechanics", "loading_thread")
    resize_res = config.getint("Mechanics", "resizeres")
    resize_factor = config.getfloat("Mechanics", "resizefactor")

    #print(spacing, spacing_set)
    spacing_items = ["sp1", "sp2", "sp3", "sp4"]

    @staticmethod
    def menu_bar_spacing():
        settings_ui.spacing = not settings_ui.spacing
        print("Spacing is ", settings_ui.spacing)

        for item in settings_ui.spacing_items:
            if settings_ui.spacing:
                dpg.show_item(item)
            else:
                dpg.hide_item(item)

        save_settings()

    def menu_bar_spacing_set(sender, app_data):
        settings_ui.spacing_set = app_data
        print("Spacing set to: ", settings_ui.spacing_set)
        for item in settings_ui.spacing_items:
            if settings_ui.spacing:
                dpg.configure_item(item, width=settings_ui.spacing_set)

        save_settings()

    def img_scaling_set(sender, app_data):
        global scale_mod
        scale_mod = settings_ui.scaling_set
        scale_mod = app_data
        save_settings()

    def img_resizing():
        global resize_res, resize_factor, useResizing
        useResizing = dpg.get_value("checkbox_7")
        resize_res = dpg.get_value("resizing_res_text")
        resize_factor = float(dpg.get_value("resizing_factor_text"))
        save_settings()

    def use_opencv():
        global useOpenCV
        useOpenCV = not useOpenCV
        save_settings()

    def image_threading():
        global useThreading
        useThreading = not useThreading
        save_settings()


class Theme():
    dynamic_theming = config.getboolean("Theme", "dynamic_theme_image")
    @staticmethod

    def dynamic_image_theme():
        global dynamic_theming
        Theme.dynamic_theming = not Theme.dynamic_theming
        print("Dynamic theme: ", Theme.dynamic_theming)
        if Theme.dynamic_theming == False:
            dpg.bind_item_theme("main_window", menu_theme) #создавать мини окна от размера этого, а не от вьюпорта или экрана
            dpg.bind_item_theme("menu_bar", bar_theme)

            dpg.bind_theme(menu_theme)

            dpg.bind_item_theme("menu_btn1", btn_theme)
            dpg.bind_item_theme("menu_btn2", btn_theme)
            dpg.bind_item_theme("menu_btn3", btn_theme)
            dpg.bind_item_theme("menu_btn5", btn_theme)
            dpg.bind_item_theme("menu_btn6", btn_theme)

            dpg.bind_item_theme("info_window", transparent_theme)
            dpg.bind_item_theme("settings_window", non_transparent_theme)
            dpg.bind_item_theme("list_window", transparent_theme)
            dpg.bind_item_theme("cv_text", transparent_theme)
            dpg.bind_item_theme("cv_rgb_shift", transparent_theme)
            dpg.bind_item_theme("cv_edge_d", transparent_theme)
            dpg.bind_item_theme("rgb_s_1", slider_red)
            dpg.bind_item_theme("rgb_s_2", slider_green)
            dpg.bind_item_theme("rgb_s_3", slider_blue)
            dpg.bind_item_theme("checkbox_1", checkbox_theme)
            dpg.bind_item_theme("settings_group1", checkbox_theme)
            dpg.bind_item_theme("settings_group2", checkbox_theme)
            dpg.bind_item_theme("welcome_window", non_transparent_theme)
            dpg.bind_item_theme("message_window", non_transparent_theme)
            dpg.bind_item_theme("file_dialog_ext", non_transparent_theme)
            pywinstyles.change_header_color(get_hwnd(), color="#151515")
            #рамка окна тоже
        save_settings()



current_index = 0
img_list = []

class Controls:
    is_info_showed = False
    w_pressed = False
    q_was_pressed = False
    s_was_pressed = False
    c_was_pressed = False

    la_was_pressed = False
    ra_was_pressed = False

    @staticmethod
    def prev_img():
    #    la_pressed = dpg.is_key_down(dpg.mvKey_Left)

        global current_index
        if current_index > 0 and img_is_loaded and image_list_loaded:
            if useImagePreview == False:
                current_index -= 1
            if useThreading == True:
                if useImagePreview == True:
                    refresh_frame_list_prev()
                t1 = threading.Thread(target=load_new_image, args=(img_list[current_index],))
                t1.start()
                print("Thread loading: ", useThreading)
            else:
                load_new_image(img_list[current_index])
        #    Controls.la_was_pressed = la_pressed

            #print("Image index: ", current_index)

    def next_img():
        global current_index, img_num
        if current_index < len(img_list) - 1 and img_is_loaded and image_list_loaded:
            if useImagePreview == False:
                current_index += 1
            if useThreading == True:
                if useImagePreview == True:
                    refresh_frame_list_next()
                t1 = threading.Thread(target=load_new_image, args=(img_list[current_index],))
                t1.start()
                print("Thread loading: ", useThreading)
            else:
                load_new_image(img_list[current_index])
            #print("Image index: ", current_index)
    #print(img_list[current_index])

    def clear_img():
        global current_index

        q_pressed = dpg.is_key_down(dpg.mvKey_Q)
        if q_pressed and not Controls.q_was_pressed:
            load_new_image(img_list[current_index])
            print("Image reloaded.")
            MenuBar.show_message("Image reloaded.")
        Controls.q_was_pressed = q_pressed

        s_pressed = dpg.is_key_down(dpg.mvKey_S)
        if s_pressed and not Controls.s_was_pressed:
            MenuBar.save_as_btn()
        Controls.s_was_pressed = s_pressed

        c_pressed = dpg.is_key_down(dpg.mvKey_C)
        if c_pressed and not Controls.c_was_pressed:
            save_to_clipboard(image_path)
            MenuBar.show_message("Copied")
        Controls.c_was_pressed = c_pressed


    def alt_keys():
        w_pressed = dpg.is_key_down(dpg.mvKey_W)
        if w_pressed and not Controls.w_was_pressed:
            Controls.is_info_showed = not Controls.is_info_showed
            if Controls.is_info_showed:
                dpg.show_item("info_window")
            else:
                dpg.hide_item("info_window")
        Controls.w_was_pressed = w_pressed

        q_pressed = dpg.is_key_down(dpg.mvKey_Q)
        if q_pressed and not Controls.q_was_pressed:
            MenuBar.show_preview_list()
        Controls.q_was_pressed = q_pressed

    def mouse_drag_handler(sender, app_data, user_data):
        global isDragging, last_x
        #print("eeee")
        current_scroll = dpg.get_x_scroll("list_window")
        if isDragging:
            print("t")
            dpg.set_x_scroll("list_window", current_scroll+15)



    def mouse_down_handler(sender, app_data, user_data):
        global isDragging, last_x
        if app_data and isDragging is False:
            print("2")
            isDragging = True

    def mouse_release_handler(sender, app_data, user_data):
        global isDragging
        if app_data == dpg.mvMouseButton_Left:
            isDragging = False
            print("P", isDragging)

    def scaling(s, a):
        global scale
        if is_window_open():
            return
        if a < 0:
            scale *= 1 / scale_mod
            scale = max(0.1, scale)
            print("scale -")
            image_resize()
        else:
            scale *= scale_mod
            scale = max(0.1, scale)
            print("scale +")
            image_resize()
        if scale >= 0.9 and not isPreviewDisabled:
            print("limit")
            dpg.hide_item("list_window")
        elif scale <= 0.8 and not isPreviewDisabled:
            dpg.show_item("list_window")


class OpenCV:
    @staticmethod

    def openCVRotate90():
        global img
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        update_texture_from_memory()
        MenuBar.show_message("Image rotated\n+90")

    def openCVRotateM90():
        global img
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        update_texture_from_memory()
        MenuBar.show_message("Image rotated\n-90")

    def openCVGrayscale():
        global img
        grayscale = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        img = cv2.cvtColor(grayscale, cv2.COLOR_GRAY2RGBA)
        print("Grayscale applied.")
        update_texture_from_memory()
        MenuBar.show_message("Applied:\nGrayscale")

    def avg_color(file_path):
        step = 8
        src_img = cv2.imread(file_path)
        if src_img is None:
            src_img = opencv_unicode(file_path)
        sampled = src_img[::step, ::step]
        average_color_row = np.average(sampled, axis=0)
        average_color = np.average(average_color_row, axis=0)
        #print(average_color)
        return average_color

    def openCVRGB_Shift():
        global img

        r,g,b,a = cv2.split(img)

        value_r = int(round(dpg.get_value("rgb_s_1")))
        value_g = int(round(dpg.get_value("rgb_s_2")))
        value_b = int(round(dpg.get_value("rgb_s_3")))

        r_shifted = np.roll(r, value_r, axis=1)  # сдвиг по горизонтали на 5 пикселей
        g_shifted = np.roll(g, value_g, axis=1) # сдвиг по вертикали на -5 пикселей
        b_shifted = np.roll(b, value_b, axis=1) # сдвиг по горизонтали на 10 пикселей

        merge_rgb = cv2.merge([r_shifted, g_shifted, b_shifted, a])
        img = merge_rgb
        print("RGB Shift applied.")
        MenuBar.show_message("Applied:\nRGB Shift")
        update_texture_from_memory()

    def openCVNoise():
        global img, img_height, img_width, img_channels
        img.shape = img_height, img_width, img_channels
        strenght = 1
        noise = np.random.normal(0, strenght, img.shape).astype(np.uint8)
        #noise = cv2.GaussianBlur(noise, (0, 0), 0.8)
        img = cv2.add(img, noise)
        print("Noise applied.")
        MenuBar.show_message("Applied:\nNoise")
        update_texture_from_memory()

    def openCVEdge_Detection(sener, app_data, user_data):
        global img
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

        if user_data == "canny":
            canny_edges = cv2.Canny(gray, 150, 250)
            edges = canny_edges

        elif user_data == "sobel":
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)  # Horizontal edges
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)  # Vertical edges

            gradient_magnitude = cv2.magnitude(sobelx, sobely)
            sobel_edges = cv2.convertScaleAbs(gradient_magnitude)

            edges = sobel_edges

        elif user_data == "laplacian":
            lap = cv2.Laplacian(gray, cv2.CV_64F)

            laplacian_edges = cv2.convertScaleAbs(lap)  #  uint8 grayscale
            edges = laplacian_edges

        img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGRA)
        #OpenCV.openCVGaussian_Blur()
        print("Edge detection applied: ", user_data)
        MenuBar.show_message("Applied:\nEdge")
        update_texture_from_memory()

    def openCVGaussian_Blur():
        global img
        img = cv2.GaussianBlur(img, (5, 5), 1.4)
        print("Gaussian Blur applied: ")
        MenuBar.show_message("Applied:\nBlur")
        update_texture_from_memory()


    def openCVText():
        global img
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = dpg.get_value("input_text_1")
        #cv2.putText(img, text, (0, 50), font, 3, (255, 255, 255), 5)
        imgcx,imgcy = img_width / 2, img_height / 2

        img = putTTFText(img, text, (int(imgcx), int(imgcy)), resource_path("fonts/selawk.ttf"), 100, color=(255, 0, 0))

        print("Text added: ", text)
        MenuBar.show_message("Applied:\nText")
        update_texture_from_memory()

    def openCVCrop(): #add resize
        global img

        x1,x2  = 0, 1000
        y1,y2  = 0, 500

        img = img[y1:y2, x1:x2]
        update_texture_from_memory()

class NodeEditor:
    def __init__(self):
        self.links = {}  # словарь связей конкретного объекта]
        #self.node_types = {}
        self.position_x = 0
        self.position_y = 0
        self.node_types = {
            "node0": {"type": "input", "name": "Start"},
            "node1": {"type": "effect", "name": "Rotate 90"},
            "node2": {"type": "effect", "name": "Rotate -90"},
            "node3": {"type": "effect", "name": "Grayscale"},
            "node4": {"type": "effect", "name": "RGB Shift"},
            "node5": {"type": "effect", "name": "Noise"},
            "node6": {"type": "effect", "name": "Edge Detection"},
            "node7": {"type": "effect", "name": "Add Text"},
            "node8": {"type": "effect", "name": "Crop"},
            "node9": {"type": "effect", "name": "Remove Text"},
            "node10": {"type": "effect", "name": "Vision"},
            "node11": {"type": "effect", "name": "Add Text"},
            "node12": {"type": "effect", "name": "Add Text"},
        }


    def add_node(self, tag, node_type, node_name): #1 тэг 2 тип 'node1': 'input'
        self.position_x += 50
        self.position_y += 50

        self.node_types[tag] = {
            "type": node_type,
            "name": node_name
        }

        if node_type == "input":
            attr_type = dpg.mvNode_Attr_Output
            with dpg.node(label=f"{node_name} ({node_type})", tag=tag, pos=[self.position_x,self.position_y], parent=node_editor_tag):
                with dpg.node_attribute(attribute_type=attr_type):
                    dpg.add_text(f"{node_type.capitalize()} Attribute")

        elif node_type == "effect":
            attr_type = dpg.mvNode_Attr_Input
            attr_type1 = dpg.mvNode_Attr_Output

            with dpg.node(label=f"{node_name} ({node_type})", tag=tag, parent=node_editor_tag):
                with dpg.node_attribute(attribute_type=attr_type):
                    dpg.add_text(f"In {node_name}") #добавлять ноды через контрол а и потом в селекторе выбирать

                with dpg.node_attribute(attribute_type=attr_type1):
                    dpg.add_text(f"Out {node_name}")


        elif node_type == "output":
            attr_type = dpg.mvNode_Attr_Input
            with dpg.node(label=f"{node_name} ({node_type})", tag=tag, parent=node_editor_tag):
                with dpg.node_attribute(attribute_type=attr_type):
                    dpg.add_text(f"{node_type.capitalize()} Attribute")


    def link_callback(self, sender, app_data):
        link_id = dpg.add_node_link(app_data[0], app_data[1], parent=sender)
        self.links[link_id] = (app_data[0], app_data[1])

        print(self.links)
        self.node_logic(app_data[0], app_data[1])

    def delink_callback(self, sender, app_data):
        if app_data in self.links:
            print("Delinked: ", self.links[app_data])
            del self.links[app_data]
        dpg.delete_item(app_data)

    def node_logic(self, output_attr, input_attr):
        output_node_id = dpg.get_item_parent(output_attr)
        input_node_id = dpg.get_item_parent(input_attr)

        output_node = dpg.get_item_alias(output_node_id)
        input_node = dpg.get_item_alias(input_node_id)

        output_type = self.node_types[output_node]["type"]
        output_name = self.node_types[output_node]["name"]

        input_type = self.node_types[input_node]["type"]
        input_name = self.node_types[input_node]["name"]
        print("o", output_type, "i", input_type)

        if (output_type == "input" and input_type == "effect") or (output_type == "effect" and input_type == "effect") :
            print(f"do: {output_name} → {input_name}")
            print("input_name", input_name)
            if input_name == "Rotate 90":
                OpenCV.openCVRotate90()
            if input_name == "Rotate -90":
                OpenCV.openCVRotateM90()
            if input_name == "Grayscale":
                OpenCV.openCVGrayscale()
            if input_name == "RGB Shift":
                MenuBar.show_edit_rgb_shift()
            if input_name == "Noise":
                OpenCV.openCVNoise()
            if input_name == "Edge Detection":
                MenuBar.show_edge_detection()
            if input_name == "Add Text":
                MenuBar.show_edit_text()
            if input_name == "Crop":
                OpenCV.openCVGrayscale()
            if input_name == "Remove Text":
                OpenCV.openCVGrayscale()
            if input_name == "Vision":
                OpenCV.openCVGrayscale()

        elif output_type == "effect" and input_type == "output":
            print(f"send: {output_name} → {input_name}")

        else:
            print(f"save: {output_name} → {input_name}")


    def make_node(self):
        selected_node = dpg.get_value("node_combo")

        name, rest = selected_node.split(" (")
        tag = selected_node.split(" (")[0]
        rest = rest.rstrip(")")  # убираем закрывающую скобку
        type, name = [x.strip() for x in rest.split(",")]
        print(tag, type, name)
        self.add_node(tag, type, name) #1 тэг 2 тип 'node1': 'input'


editor = NodeEditor()

def dpg_quad():
    mx, my = dpg.get_mouse_pos()

    dpg.configure_item("roi_quad",
            p1=[0,0],
            p2=[mx,0],
            p3=[mx,my],
            p4=[0,my],
        )


def print_me(sender):
    print(f"Menu Item: {sender}")

def is_window_open():
    return (
        dpg.is_item_shown("file_dialog") or
        dpg.is_item_shown("settings_window") or
        dpg.is_item_shown("welcome_window") or
        dpg.is_item_shown("node_add_window") or
        dpg.is_item_shown("file_dialog_ext")
    )

def save_to_clipboard(filepath):

    image = Image.open(filepath)

    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

def configure_text(file):
    window_width = dpg.get_item_width("info_window")
    window_height = dpg.get_item_height("info_window")

    text_x = (window_width / 3)
    text_y = 30

    if file is None:
        print("Image is not opened.")
        dpg.configure_item("info_text", default_value="Image is not opened", pos=[text_x, text_y+30])
    else:
        file_size = os.path.getsize(file) / 1024
        text_label = (f"""Name: {os.path.basename(file).split(".")[0]}
Resolution: {img_width}x{img_height}
Size: {file_size:.0f} KB
----------------------
Image path: '{os.path.abspath(file)}'
Debug index: {current_index}
Images found in folder: {len(img_list)}
Folder: {os.path.dirname(file)}""")
        dpg.configure_item("info_text", default_value=text_label, pos=[5, text_y])

def configure_image(file, width, height):
    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()

    window_height = dpg.get_item_height("main_window")

    #print("VH: "+str(viewport_height)+" WH: "+str(window_height))
    img_w = viewport_width
    img_h = img_w / img_aspectratio

    if img_h > viewport_height:
        img_h = viewport_height
        img_w = img_h * img_aspectratio

    window_pos = dpg.get_item_pos("main_window")

    if img_h > viewport_height:
        img_h = viewport_height
        img_w = img_h * img_aspectratio

    x = (viewport_width - img_w) / 2
    #y = window_pos[1] + (viewport_height - img_h) / 2
    y = (viewport_height - img_h) / 2
    #dpg.set_item_width("main_window", viewport_width)
    #dpg.set_item_height("main_window", viewport_height)
    #dpg.configure_item("main_img", width=img_w, height=img_h, pos=[x, y])

    #print(f"""Image size: {img_w}x{img_h}""")
    image_data = f"""{file} Resolution:  {str(width)}x{str(height)}"""
    dpg.configure_item("main_window", label=image_data)


def opencv_unicode(file_path):
    print(f"For file: | {os.path.basename(file_path)} | using unicode reading with numpy.")
    data = np.fromfile(file_path, dtype=np.uint8)

    img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    return img

def opencv_image(file_path):
    global img

    cv_img = None
    cv_img = cv2.imread(file_path)

    if cv_img is None:
        cv_img = opencv_unicode(file_path)

    img = cv_img        # BGR
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    height, width, channels = img.shape
    height_i, width_i = height, width
    resize_resolution = int(resize_res)
    if useResizing == True:
        if height >= resize_resolution or width >= resize_resolution:
            r_width = int(width / resize_factor)
            r_height = int(height / resize_factor)
            img = cv2.resize(img, (r_width, r_height), interpolation=cv2.INTER_AREA)
            height, width = img.shape[:2]
            print(f"Image resolution is too big {width_i},{height_i}, resizing to...{width}x{height}")

    data = img.flatten() / 255.0
    return width, height, channels, data

def opencv_image_list(file_path):
    global img_l, img_list_width, img_list_height

    cv_img = None
    cv_img = cv2.imread(file_path)

    if cv_img is None:
        cv_img = opencv_unicode(file_path)

    img_l = cv_img        # BGR
    img_l = cv2.cvtColor(img_l, cv2.COLOR_BGR2RGBA)
    height, width, channels = img_l.shape
    height_i, width_i = height, width

    max_side = max(width_i, height_i)
    scale = 128 / max_side
    new_width = int(width_i * scale)
    new_height = int(height_i * scale)
    print(f"Rescaled image list resolution: {new_width}x{new_height}")
    img_l = cv2.resize(img_l, (new_width, new_height), interpolation=cv2.INTER_AREA)
    height, width = new_height, new_width
    img_list_width = width
    img_list_height = height
    data = img_l.flatten() / 255.0
    return width, height, channels, data

def update_texture_from_memory():

    global img, img_tag, loaded_image, img_width, img_height, img_aspectratio

    img_height, img_width, channels = img.shape
    img_aspectratio = img_width / img_height

    data = img.flatten() / 255.0

    old_img_tag = "img_" + str(img_tag)

    img_tag += 1
    new_img_tag = "img_" + str(img_tag)

    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=img_width, height=img_height, default_value=data, tag=new_img_tag)

    dpg.configure_item("main_img", texture_tag=new_img_tag)
    dpg.configure_item("node_img", texture_tag=new_img_tag)

    if dpg.does_item_exist(old_img_tag):
        dpg.delete_item(old_img_tag)

    configure_image(image_path, img_width, img_height)
    configure_text(image_path)

    loaded_image = (img_width, img_height, channels, data)

    on_resize(None, None)

def remove_old_images_from_list():
    print(image_from_list)
    if image_items_tags is not None:
        for img_l in image_items_tags:
            dpg.delete_item(img_l)
            print("Deleted image item from list: ", img_l)
        else:
            pass

    if image_from_list is not None:
        for img_l1 in image_from_list:
            dpg.delete_item(img_l1)
            print("Deleted image from list: ", img_l1)
        else:
            pass

    image_items_tags.clear()
    image_from_list.clear()


def add_images_to_list(image, index):
    global image_items_tags, current_selected_image_item

    image_item_tag = f"list_img_item_{index}"
    image_items_tags.append(image_item_tag)
    if current_index == index:
        dpg.add_image_button(image, parent=images_horizontal,
        callback= open_image_from_list, user_data = index, #предать в глоаб и потом изменить
        tag=image_item_tag, frame_padding=image_list_frame_size)
        current_selected_image_item = image_item_tag

    else:
        dpg.add_image_button(image, parent=images_horizontal,
        callback= open_image_from_list, user_data = index,
        tag=image_item_tag, frame_padding=1)


def open_image_from_list(sender, app_data, index):

    global current_index, current_selected_image_item
    current_index = index

    dpg.configure_item(sender, frame_padding=image_list_frame_size)
    refresh_frame_pos(sender)

    if current_selected_image_item is not None:
        dpg.configure_item(current_selected_image_item, frame_padding=1) #to global for hange with buttons
    current_selected_image_item = sender
    print("ikgkigiggeg", current_selected_image_item)
    load_new_image(img_list[current_index])


def refresh_frame_pos(item):
    global is_frame_refreshed
    item_pos = dpg.get_item_pos(item)
    item_width = dpg.get_item_width(item)

    win_width = dpg.get_item_width("list_window")

    target_scroll_x = item_pos[0] + item_width/2 - win_width/2

    max_scroll = dpg.get_x_scroll_max("list_window")
    target_scroll_x = max(0, min(target_scroll_x, max_scroll))

    dpg.set_x_scroll("list_window", target_scroll_x)

    #is_frame_refreshed = True


def refresh_frame_list_prev():
    global current_selected_image_item, current_index
    old_item = current_selected_image_item


    dpg.configure_item(old_item, frame_padding=1)

    if current_index >= 0:
        current_index -= 1
        new_item = image_items_tags[current_index]

        dpg.configure_item(new_item, frame_padding=image_list_frame_size)
        refresh_frame_pos(new_item)
        current_selected_image_item = new_item

def refresh_frame_list_next(): #just call for next_img without changing index
    global current_selected_image_item, current_index
    old_item = current_selected_image_item

    dpg.configure_item(old_item, frame_padding=1)

    if current_index + 1 < len(image_items_tags):
        current_index += 1
        new_item = image_items_tags[current_index]
        dpg.configure_item(new_item, frame_padding=image_list_frame_size)
        refresh_frame_pos(new_item)
        current_selected_image_item = new_item

def load_new_images(file_path): #or just add directly in the window for the moment
    dpg.show_item("list_window")
    gstart = time.perf_counter()
    global image_list_loaded, image_from_list

    remove_old_images_from_list()
    MenuBar.show_message("Image list\nLoading started...")
    base_path = os.path.dirname(file_path)
    dpg.configure_item("list_window", label=base_path)

    with dpg.texture_registry(show=False) as new_image_registry: #don't mak new every time
        pass

    img_tag1 = 0
    new_img_tag_str = ""
    width1, height1, channels1, data1 = None, None, None, None
    image_from_list = []

    img_list = sorted([
    os.path.abspath(os.path.join(base_path, f))
    for f in os.listdir(base_path)
    if f.lower().endswith((".jpg", ".png"))
    ])

    for index, absfile in enumerate(img_list):
        img_tag1 +=1
        new_img_tag_str = "img_list_"+str(img_tag1)

        if useOpenCV == True:
            start = time.perf_counter()
            loaded1_image = opencv_image_list(absfile)
            end = time.perf_counter()
    #        print(f"\nOpenCV image opening time: {end - start:.6f} sec.")
            width1, height1, channels1, data1 = loaded1_image
            image_from_list.append(new_img_tag_str)
        else:
            start = time.perf_counter()
            loaded1_image = dpg.load_image(absfile)
            end = time.perf_counter()
    #        print(f"\nDPG image opening time: {end - start:.6f} sec.")
            width1, height1, channels1, data1 = loaded1_image
            image_from_list.append(new_img_tag_str)


    #    print(f"Adding texture {new_img_tag_str}: width={width1}, height={height1}, channels={channels1}, data_len={len(data1)}")
                #if


        #start_i = time.perf_counter()
        dpg.add_static_texture(width=width1, height=height1, default_value=data1, tag=new_img_tag_str, parent=new_image_registry)
        images_list_path = absfile
        add_images_to_list(new_img_tag_str, index)
        #end_i = time.perf_counter()
    #    print(f"Static textures processing time:  {end_i - start_i:.6f}")

    #add_images_to_list(image_from_list)
    gend = time.perf_counter()
    calculated_time = gend - gstart
    print(f"\nList loading time: {calculated_time:.3f} sec.")
    image_list_loaded = True
    MenuBar.show_message(f"Image list loaded.\nTime: {calculated_time:.3f} sec.")
    print("Image list loaded.")

def load_new_image(file_path):
    global img_tag, img_aspectratio, loaded_image, image_path, img_width, img_height, img_list, img_name, img_channels, img_data, img_avg_col, img_is_loaded
    img_is_loaded = False
    #загружать картинку уже с измененым положением
    start_t = time.perf_counter()
    if useOpenCV == True:
        start = time.perf_counter()
        loaded_image = opencv_image(file_path)
        end = time.perf_counter()
        print(f"\nOpenCV image opening time: {end - start:.6f} sec.")
    else:
        start = time.perf_counter()
        loaded_image = dpg.load_image(file_path)
        end = time.perf_counter()
        print(f"\nDPG image opening time: {end - start:.6f} sec.")

    if loaded_image is None:
        print("Wrong image/can't load it. "+"Filepath: "+file_path)
        return

    width, height, channels, data = loaded_image

    img_channels = channels
    img_width, img_height = width, height
    img_aspectratio = width / height
    img_data = data

    viewport_width = dpg.get_viewport_width()
    viewport_height = dpg.get_viewport_height()

    available_height = viewport_height - title_offset
    available_width = viewport_width

    aspect_img = img_aspectratio
    aspect_view = available_width / available_height

    if aspect_img > aspect_view:
        img_w = available_width*scale
        img_h = img_w / aspect_img
    else:
        img_h = available_height*scale #добавить в open image
        img_w = img_h * aspect_img

    x = (viewport_width - img_w) / 2
    y = (available_height - img_h) / 2 + title_offset

    img_tag += 1

    new_img_tag = "img_"+str(img_tag)

    old_img_tag = img_tag-1
    old_img_name_tag = "img_"+str(old_img_tag)

    #print("New texture tag: ", new_img_tag)

    #print("Old texture tag: ", old_img_name_tag)

    if dpg.does_item_exist(old_img_name_tag):
        dpg.delete_item(old_img_name_tag)
        #print(f"Old texture tag: {old_img_name_tag} deleted")
    #else:
        #print(f"Old texture tag: {old_img_name_tag} not found")

    if Theme.dynamic_theming == True:
        img_avg_col = OpenCV.avg_color(file_path)

    with dpg.texture_registry(show=False):
        start_i = time.perf_counter()
        dpg.add_static_texture(width=width, height=height, default_value=data, tag=new_img_tag)
        dpg.configure_item("main_img", texture_tag=new_img_tag,  pos=[x,y], width=img_w, height=img_h)
        if isEditMode:
            img_channels = channels
            img_width, img_height = width, height
            img_aspectratio = width / height
            img_data = data

            viewport_width = dpg.get_item_width("img_node_window")
            viewport_height = dpg.get_item_height("img_node_window")

            available_height = viewport_height
            available_width = viewport_width

            aspect_img = img_aspectratio
            aspect_view = available_width / available_height

            if aspect_img > aspect_view:
                img_w = available_width*scale
                img_h = img_w / aspect_img
            else:
                img_h = available_height*scale #добавить в open image
                img_w = img_h * aspect_img

            x = (viewport_width - img_w) / 2
            y = (available_height - img_h) / 2 + title_offset
            dpg.configure_item("node_img", texture_tag=new_img_tag,  pos=[x,y-title_offset], width=img_w, height=img_h)
        end_i = time.perf_counter()
        print(f"Static texture processing time:  {end_i - start_i:.6f}")

    if Theme.dynamic_theming == True:
        dynamic_img_theme(img_avg_col)

    configure_image(file_path, width, height)
    end_t = time.perf_counter()
    print(f"Image rendering time: {end_t - start_t:.6f} sec.\n")
    #OpenCV.main_color()
    image_path = file_path
    #on_resize(None, None)
    print("-------------------------------------------")
    print(f"""Image: {img_name} | Res: {width}x{height} | Tag: {new_img_tag}""")
    print("-------------------------------------------")
    configure_text(img_list[current_index])
    img_is_loaded = True
    if not image_list_loaded and useImagePreview: #threading
        load_new_images(file_path)


def open_image(sender, app_data, cancel):
    global img_tag, img_aspectratio, loaded_image, image_path, img_width, img_height, img_list, img_name, current_index

    if cancel:
        dpg.hide_item("file_dialog_ext")
        print("FDialog closed.")
        return

    try:
        file_path = app_data[0]
    except IndexError:
        print("No selected items.")
        return

    if cancel:
        dpg.hide_item("file_dialog_ext")
    if file_path.lower().endswith((".jpg", ".png")):
        dpg.hide_item("file_dialog_ext")
        print(f"Selected {file_path.lower()}")
    else:
        print(f"Not valid file type. {file_path.lower()}")
        return

    folder = os.path.dirname(file_path)
    name = os.path.splitext(os.path.basename(file_path))[0]
    img_name=name
    current_image = os.path.abspath(file_path)
    current_folder = folder


    img_list = sorted([
        os.path.abspath(os.path.join(folder, f))
        for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".png"))
    ])


    current_index = img_list.index(file_path)

    #print("index", current_index)

    image_path = file_path
    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()

    load_new_image(img_list[current_index])

def open_image_tk(sender=None, app_data=None, cancel=False):
    global img_tag, img_aspectratio, loaded_image, image_path, img_width, img_height, img_list, img_name, current_index, image_list_loaded, is_frame_refreshed
    app_data = CreateFileDialog_Open()

    image_list_loaded = False
    is_frame_refreshed = False

    #remove_old_images_from_list()

    if cancel:
        dpg.hide_item("file_dialog_ext")
        print("FDialog closed.")
        return

    try:
        file_path = app_data
    except IndexError:
        print("No selected items.")
        return
    file_path = os.path.abspath(file_path)

    if cancel:
        dpg.hide_item("file_dialog_ext")

    if file_path.lower().endswith((".jpg", ".png")):
        dpg.hide_item("file_dialog_ext")
        print(f"Selected {file_path.lower()}")
    else:
        print(f"Not valid file type. {file_path.lower()}")
        return

    folder = os.path.dirname(file_path)
    name = os.path.splitext(os.path.basename(file_path))[0]
    img_name=name
    current_image = os.path.abspath(file_path)
    current_folder = folder


    img_list = sorted([
        os.path.abspath(os.path.join(folder, f))
        for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".png"))
    ])


    current_index = img_list.index(file_path)

    #print("index", current_index)

    image_path = file_path
    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()

    if useThreading == True:
        t1 = threading.Thread(target=load_new_image, args=(img_list[current_index],))
        t1.start()
        print("Thread loading: ", useThreading)
    else:
        load_new_image(img_list[current_index])

    MenuBar.show_message("Image opened")


def open_image_from_start(file_path): #debug index bug
    global img_tag, img_aspectratio, loaded_image, image_path, img_width, img_height, img_list, img_name

    file_path = os.path.abspath(file_path)
    folder = os.path.dirname(file_path)
    name = os.path.splitext(os.path.basename(file_path))[0]
    img_name = name

    img_list = sorted([
        os.path.abspath(os.path.join(folder, f))
        for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".png"))
    ])

    if file_path not in img_list:
        print("Can't open this file. "+"Filepath: "+file_path)
        return

    current_index = img_list.index(file_path)
    #print("index", current_index)

    image_path = file_path
    load_new_image(img_list[current_index])


dpg.create_context()
#dpg.create_viewport(title='RetroImageViewer', width=screen_w//2, height=screen_h//2, x_pos=screen_w//4, y_pos=screen_h//4)
dpg.create_viewport(title='RetroImageViewer', small_icon=small_app_icon, large_icon=large_app_icon, width=screen_w+25, height=screen_h, x_pos=0, y_pos=0)

with dpg.font_registry():
    default_font = dpg.add_font(resource_path("fonts/selawk.ttf"), 24)
dpg.bind_font(default_font)

with dpg.texture_registry(show=False):
    dpg.add_static_texture(1, 1, default_value=[50/255,50/255,50/255,255], tag="texture_tag")

#main
with dpg.viewport_menu_bar(tag="menu_bar") as view_menu_bar:
#on resize y * 20 too
    with dpg.group(horizontal=True, tag="left_menu_group"):
        with dpg.menu(label="File", tag="menu_btn1"):
            dpg.add_menu_item(label="Save", callback=MenuBar.save_btn)
            dpg.add_menu_item(label="Save As", callback=MenuBar.save_as_btn)
            dpg.add_separator()
            dpg.add_menu_item(label="Open...", callback=MenuBar.show_dialogue_tk)
            dpg.add_menu_item(label="Open (old)", callback=MenuBar.show_dialogue)
        dpg.add_spacer(width=settings_ui.spacing_set, show=settings_ui.spacing, tag="sp1")
        with dpg.menu(label="Edit", tag="menu_btn2"):
            dpg.add_menu_item(label="Rotate 90", callback=OpenCV.openCVRotate90)
            dpg.add_menu_item(label="Rotate -90", callback=OpenCV.openCVRotateM90)
            dpg.add_separator()
            dpg.add_menu_item(label="Grayscale", callback=OpenCV.openCVGrayscale)
            dpg.add_menu_item(label="RGB Shift", callback=MenuBar.show_edit_rgb_shift)
            dpg.add_menu_item(label="Noise", callback=OpenCV.openCVNoise)
            dpg.add_separator()
            dpg.add_menu_item(label="Edge Detection", callback=MenuBar.show_edge_detection)
            dpg.add_separator()
            dpg.add_menu_item(label="Text", callback=MenuBar.show_edit_text)
            dpg.add_menu_item(label="Crop", callback=OpenCV.openCVCrop)
            #dpg.add_menu_item(label="AVG", callback=get_image_avg_col)
        dpg.add_spacer(width=settings_ui.spacing_set, show=settings_ui.spacing, tag="sp2")
        with dpg.menu(label="View", tag="menu_btn3"):
            dpg.add_menu_item(label="Preview", callback=MenuBar.show_preview_list)
            dpg.add_menu_item(label="Info", callback=MenuBar.show_info)
            dpg.add_menu_item(label="Edit mode", callback=MenuBar.show_edit_mode)
            dpg.add_menu_item(label="Message", callback=MenuBar.show_message)
        dpg.add_spacer(width=settings_ui.spacing_set, show=settings_ui.spacing, tag="sp3")
        dpg.add_menu_item(label="Settings", tag="menu_btn5", callback=MenuBar.show_settings)
        dpg.add_spacer(width=settings_ui.spacing_set, show=settings_ui.spacing, tag="sp4")
        dpg.add_menu_item(label="About", tag="menu_btn6", callback=MenuBar.show_about)

    dpg.add_spacer(width=0, tag="spacer")
    dpg.set_item_pos("left_menu_group", [0, 0])

    if custom_decorator == True:
        dpg.set_viewport_decorated(False)
        with dpg.group(horizontal=True, tag="right_menu_group"):
            dpg.add_menu_item(label="-", callback=Window.minimize_window)
            dpg.add_menu_item(label="[]", callback=Window.maximize_window)
            dpg.add_menu_item(label="x", callback=app_close)

with dpg.window(label="Add text", tag="cv_text", show=False,pos=[(dpg.get_viewport_width()-400)/2, (dpg.get_viewport_height()-250)/2], width=400, height=250):
    with dpg.group(horizontal=True,tag="edit_text_gp"):
        dpg.add_input_text(tag="input_text_1")
        dpg.add_button(label="Apply", callback=OpenCV.openCVText)

with dpg.window(label="Edge detection", tag="cv_edge_d", show=False,pos=[(dpg.get_viewport_width()-400)/2, (dpg.get_viewport_height()-250)/2], width=400, height=250):
    with dpg.group(horizontal=True):
        dpg.add_button(label="Sobel", user_data="sobel", callback=OpenCV.openCVEdge_Detection)
        dpg.add_button(label="Laplacian", user_data="laplacian", callback=OpenCV.openCVEdge_Detection)
        dpg.add_button(label="Canny", user_data="canny", callback=OpenCV.openCVEdge_Detection)

with dpg.window(label="RGB Shift", tag="cv_rgb_shift", show=False,pos=[(dpg.get_viewport_width()-400)/2, (dpg.get_viewport_height()-250)/2], width=400, height=250):
    with dpg.group(tag="edit_rgb_shift"):
        dpg.add_slider_float(label="Red", tag="rgb_s_1",width=200, min_value=-50, max_value=50, default_value=0)
        dpg.add_slider_float(label="Green", tag="rgb_s_2",width=200, min_value=-50, max_value=50, default_value=10)
        dpg.add_slider_float(label="Blue", tag="rgb_s_3", width=200, min_value=-50, max_value=50, default_value=10)
        dpg.add_button(label="Apply", callback=OpenCV.openCVRGB_Shift)

with dpg.window(label="", tag="main_window", pos=[0,30],
no_move=True, no_collapse=True,no_close=True,
no_scrollbar=False, no_scroll_with_mouse=False,
no_bring_to_front_on_focus=True, no_resize=True):
    dpg.add_image("texture_tag", tag='main_img')
    ##with dpg.drawlist(width=1920, height=1080, pos=[0,0]):
    #    dpg.draw_quad(
    #        p1=[0,0],
    #        p2=[100,0],
    #        p3=[100,100],
    #        p4=[0,100],
    #        color=(255,0,0,255),
    #        tag="roi_quad"
    #    )

        #dpg.draw_image("main_img_texture", [0,0], [600,400])
        #dpg.draw_image("main_img_texture", [0,0], [600,400])
with dpg.window(label="", tag="list_window", pos=[0,dpg.get_viewport_height()-225], width=dpg.get_viewport_width(), height=200,
no_move=True, no_collapse=True,no_close=True,
no_scrollbar=False,horizontal_scrollbar=True, no_scroll_with_mouse=False, no_resize=True, show=False) as list_images_window:
    #dpg.add_image("texture_tag", tag='main_img')
    with dpg.group(horizontal=True, parent=list_images_window, tag="images_horizontal_group") as images_horizontal:
        pass

    with dpg.item_handler_registry(tag="list_scrolling"):
        pass

    #dpg.add_image("texture_tag", tag='list_img')
if isEditMode:
    with dpg.window(label="Image", tag="img_node_window", pos=[0,title_offset+75], width=dpg.get_viewport_width()/2, height=dpg.get_viewport_height(),
    no_scrollbar=True,horizontal_scrollbar=False, no_resize=False, no_close=True,  no_move=True, no_collapse=True,show=False):
        dpg.add_image("texture_tag", tag='node_img')

    with dpg.window(label="Node Editor", tag="node_window", pos=[dpg.get_viewport_width()/2,title_offset+75], width=dpg.get_viewport_width()/2-25, height=dpg.get_viewport_height(),
    no_scrollbar=False,horizontal_scrollbar=True, no_resize=False, no_close=True, no_move=True, no_collapse=True,show=False):
        with dpg.menu_bar():
            dpg.add_menu_item(label="Add...", callback=MenuBar.show_node_list)

        with dpg.node_editor(callback=lambda s,a: editor.link_callback(s,a),
         delink_callback=lambda s,a: editor.delink_callback(s,a)) as node_editor_tag:
            #editor.add_node("node0", "output", "Image")
            editor.add_node("node0", "input", "Start")
            #editor.add_node("node1", "effect", "Grayscale")

    with dpg.window(label="Add node", tag="node_add_window", pos=[dpg.get_item_pos("node_window")[0]*1.35,dpg.get_item_pos("node_window")[1]*15] , width=400, height=200,
    no_scrollbar=False,horizontal_scrollbar=True, no_resize=True, no_collapse=True,show=False, modal=True):
        dpg.add_separator()
        node_items = [f'{tag} ({data["type"]}, {data["name"]})' for tag, data in editor.node_types.items()]
        #print(editor.node_types.items())
        dpg.add_combo(node_items,label="Nodes",tag="node_combo",     callback=editor.make_node)



    #dpg.add_image("texture_tag", tag='main_img')



with dpg.window(label="", show=False, tag="file_dialog_ext", no_title_bar=True, width=1000,height=620,
 no_scrollbar=True, no_scroll_with_mouse=True,no_resize=True):
    FileBrowser(tag="file_d_ext", default_path=os.getcwd(),
        		width=1000,
        		height=600,
        		modal_window =True,
        		show_ok_cancel=True,
        		allow_multi_selection=False,
        		collapse_sequences=True,
                add_filename_tooltip=True,
                icon_size=2,
        		callback=open_image)
#    dpg.add_input_text(
    #tag="selected_file",
#    label="",
#    width=400, pos=[0,600]
#    )

with dpg.window(label="Welcome!", show=isFirstLaunch, tag="welcome_window",
pos=[(dpg.get_viewport_width()-800)/2, (dpg.get_viewport_height()-800)/2]
, width=800, height=800):
        with dpg.group(horizontal=True, tag="welcome_group"):
             dpg.add_text("It's seems this your first time here, it would be better if you visit setting page.", tag="welcome_text")
        dpg.add_button(label="It's here...", width=100, callback=MenuBar.show_settings)

with dpg.window(label="Settings", tag="settings_window", show=False,
pos=[(dpg.get_viewport_width()-600)/2, (dpg.get_viewport_height()-800)/2]
, width=600, height=800):
        with dpg.group(tag="settings_group"):
             dpg.add_text("Menu panel", tag="settings_text")
             dpg.add_checkbox(label="Use custom decorator", tag="checkbox_1", callback=print_me)
             with dpg.group(tag="settings_group1"):
                 dpg.add_checkbox(label="Menu spacing", tag="checkbox_2", default_value = settings_ui.spacing, callback=settings_ui.menu_bar_spacing)
                 dpg.add_slider_float(label="Spacing", width=200, min_value=0.00, max_value=400.00, default_value=settings_ui.spacing_set, callback=settings_ui.menu_bar_spacing_set)
             dpg.add_separator()
             with dpg.group(tag="settings_group2"):
                 dpg.add_text("Behaviour", tag="settings_text2")
                 dpg.add_slider_float(label="Image zoom factor", width=200, min_value=1, max_value=5, default_value=scale_mod, callback=settings_ui.img_scaling_set)
             dpg.add_separator()
             with dpg.group(tag="settings_group_theme"):
                 dpg.add_text("Theme")
                 dpg.add_checkbox(label="Dynamic theme", tag="checkbox_5", default_value = Theme.dynamic_theming, callback=Theme.dynamic_image_theme)
             dpg.add_separator()
             with dpg.group(tag="settings_group4"):
                 dpg.add_text("Mechanics")
                 dpg.add_checkbox(label="Use OpenCV library\n(Required for image processing).", tag="checkbox_3", default_value = useOpenCV, callback=settings_ui.use_opencv)
                 dpg.add_checkbox(label="Image Threading load", tag="checkbox_6", default_value = useThreading, callback=settings_ui.image_threading)
                 #dpg.add_separator()
                 dpg.add_checkbox(label="Image Resizing", tag="checkbox_7",callback=settings_ui.img_resizing, default_value = useResizing)
                 with dpg.group(horizontal=True):
                     dpg.add_text("Resize on res:")
                     dpg.add_input_text(width=50, tag="resizing_res_text", default_value=resize_res, callback=settings_ui.img_resizing)
                     dpg.add_text("Resize multiplier:")
                     dpg.add_input_text(width=35, tag="resizing_factor_text", default_value=resize_factor, callback=settings_ui.img_resizing)
             dpg.add_separator()
             with dpg.group(tag="settings_group3"):
                 dpg.add_text("Keybindings", tag="keys_text")
                 with dpg.group(horizontal=True):
                     dpg.add_combo(keys, label="+", default_value="mvKey_LControl", tag="all_keys", width =200)
                     dpg.add_combo(keys, label="Reset image", default_value="mvKey_Q", tag="all_keys1",  width =200)
                 with dpg.group(horizontal=True):
                     dpg.add_combo(keys, label="+", default_value="mvKey_LAlt", tag="all_keys2", width =200)
                     dpg.add_combo(keys, label="Info Window", default_value="mvKey_W", tag="all_keys3",  width =200)
                 with dpg.group(horizontal=True):
                     dpg.add_combo(keys, label="+", default_value="mvKey_LAlt", tag="all_keys17", width =200)
                     dpg.add_combo(keys, label="Preview Window", default_value="mvKey_Q", tag="all_keys18",  width =200)
                 with dpg.group(horizontal=True):
                     dpg.add_combo(keys, label="+", default_value="mvKey_LControl", tag="all_keys11", width =200)
                     dpg.add_combo(keys, label="Save as", default_value="mvKey_C", tag="all_keys12",  width =200)
                 with dpg.group(horizontal=True):
                     dpg.add_combo(keys, label="+", default_value="mvKey_LControl", tag="all_keys14", width =200)
                     dpg.add_combo(keys, label="To clipboard", default_value="mvKey_C", tag="all_keys15",  width =200)

                 dpg.add_combo(keys, label="Maximize", default_value="mvKey_Enter", tag="all_keys4", width =200)
                 dpg.add_combo(keys, label="Prev", default_value="mvKey_Left", tag="all_keys6",  width =200)
                 dpg.add_combo(keys, label="Next", default_value="mvKey_Right", tag="all_keys5",  width =200)
             dpg.add_separator()
             with dpg.group(tag="settings_group5"):
                 dpg.add_text("Debug", tag="debug_text")
                 dpg.add_text("Version: 0.098a-pre-win", tag="debug_text1")

if show_wv == True:
    with dpg.window(label="Image: Info", show=False, tag="info_window", pos=[0, 200], width=500, height=600):
        with dpg.group(horizontal=True, tag="info_group"):
            dpg.add_text("hello", tag="info_text")
#ширина окна от ширины текста
with dpg.window(label="Message",no_move=True, no_focus_on_appearing= True, #создавать каждый раз
 no_collapse=True, no_close=True, no_resize=True, no_title_bar=False,
  show=False, tag="message_window", #modal vindow
   pos=[dpg.get_viewport_width()/1.1299, dpg.get_viewport_height()/18], width=200, height=20):
    dpg.add_text("", tag="message_text")

with dpg.file_dialog(directory_selector=False,show=False,callback=open_image,tag="file_dialog", width=screen_w//2, height=screen_h//2):
    dpg.add_file_extension(".*", color=(255, 255, 255, 255))
    dpg.add_file_extension(".jpg", color=(144, 238, 144, 255))
    dpg.add_file_extension(".png", color=(144, 238, 143, 255))

def image_resize():
    global img_aspectratio
    viewport_width = dpg.get_viewport_width()
    viewport_height = dpg.get_viewport_height()

    available_height = viewport_height - title_offset
    available_width = viewport_width

    aspect_img = img_aspectratio
    aspect_view = available_width / available_height

    if aspect_img > aspect_view:
        img_w = available_width*scale
        img_h = img_w / aspect_img
    else:
        img_h = available_height*scale #добавить в open image
        img_w = img_h * aspect_img

    x = (viewport_width - img_w) / 2
    y = (available_height - img_h) / 2 + title_offset

    iw = dpg.get_item_width("main_img")
    ig = dpg.get_item_height("main_img")

    #print(iw,ig,viewport_width,viewport_height)
    if isEditMode:
        n_img_w, n_img_n = None, None
        n_viewport_width = dpg.get_item_width("img_node_window")
        n_viewport_height = dpg.get_item_height("img_node_window")

        n_available_height = n_viewport_height - title_offset
        n_available_width = n_viewport_width

        n_aspect_img = img_aspectratio
        n_aspect_view = n_available_width / n_available_height

        if aspect_img > n_aspect_view:
            n_img_w = n_available_width*scale
            n_img_h = n_img_w / aspect_img
        else:
            n_img_h = n_available_height*scale #добавить в open image
            n_img_w = n_img_h * aspect_img

        n_x = (n_viewport_width - n_img_w) / 2
        n_y = (n_available_height - n_img_h) / 2 + title_offset

        dpg.configure_item("node_img", width=n_img_w, height=n_img_h, pos=[n_x,n_y])

    dpg.set_item_width("main_window", viewport_width)
    dpg.set_item_height("main_window", viewport_height*20)
    dpg.configure_item("main_img", width=img_w, height=img_h, pos=[x,y])

    print("Scale: ", scale)

def image_resize2():
    global img_aspectratio
    viewport_width = dpg.get_viewport_width()
    viewport_height = dpg.get_viewport_height()
    title_offset = -45
    available_height = viewport_height - title_offset
    available_width = viewport_width

    aspect_img = img_aspectratio
    aspect_view = available_width / available_height

    if aspect_img > aspect_view:
        img_w = available_width
        img_h = img_w / aspect_img
    else:
        img_h = available_height
        img_w = img_h * aspect_img

    x = (viewport_width - img_w) / 2
    y = (available_height - img_h) / 2 + title_offset

    td = dpg.get_mouse_pos()

    mx,my = td[0], td[1]

    rel_x = (mx - x) / img_w
    rel_y = (my - y) / img_h
    iw = dpg.get_item_width("main_img")
    ig = dpg.get_item_height("main_img")

    img_w *= scale
    img_h *= scale

    x = mx - rel_x * img_w
    y = my - rel_y * img_h

    #print(iw,ig,viewport_width,viewport_height)

    dpg.set_item_width("main_window", viewport_width)
    dpg.set_item_height("main_window", viewport_height*20)
    dpg.configure_item("main_img", width=img_w, height=img_h, pos=[x,y])

    print("Scale: ", scale)


def on_resize(sender, app_data): #add img_list
    global img_aspectratio, loaded_image, image_path, current_img_w, current_img_h, current_img_pos_x, current_img_pos_y, scale
    viewport_width = dpg.get_viewport_width()
    viewport_height = dpg.get_viewport_height()

    available_height = viewport_height - title_offset
    available_width = viewport_width

    aspect_img = img_aspectratio
    aspect_view = available_width / available_height

    if aspect_img > aspect_view:
        img_w = available_width*scale
        img_h = img_w / aspect_img
    else:
        img_h = available_height*scale #добавить в open image
        img_w = img_h * aspect_img

    x = (viewport_width - img_w) / 2
    y = (available_height - img_h) / 2 + title_offset

    dpg.set_item_width("main_window", viewport_width)
    dpg.set_item_height("main_window", viewport_height)
    dpg.configure_item("main_img", width=img_w, height=img_h, pos=[x, y])
    dpg.configure_item("list_window", pos=[0,dpg.get_viewport_height()-245], width=dpg.get_viewport_width(), height=200)

    #print(f"""Image size after resize: {str(int(img_w))}x{img_h}""")
    if image_path is not None:
        configure_text(image_path)

#with dpg.handler_registry() as drag_handlers:
#    dpg.add_mouse_down_handler(button=0, callback=Window.start_drag)
#    dpg.add_mouse_release_handler(button=0, callback=Window.stop_drag)
#    dpg.add_mouse_move_handler(callback=Window.window_drag)



with dpg.theme() as menu_theme: #menu bar
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (65, 65, 65, 255))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (65, 65, 65, 255)) #отдельно для настроек сделать
        #dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 0, 0, 255))       # цвет рамки
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (50, 50, 50, 255))     #
        dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.5, 0.5)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (75, 75, 75, 255))
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (75, 75, 75, 255))

with dpg.theme() as bar_theme:
    with dpg.theme_component(dpg.mvAll):
        #dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 0)  # x- и y-расстояние
        dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (50, 50, 50, 255))     #

with dpg.theme() as btn_theme:
    with dpg.theme_component(dpg.mvMenu):
        #dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 0)  # x- и y-расстояние
        dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))        # цвет текста

        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (75, 75, 75, 255))

with dpg.theme() as checkbox_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (220, 220, 220, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (65, 65, 65, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (70, 70, 70, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (70, 70, 70, 255))


with dpg.theme() as transparent_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (0, 0, 0, 100))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (65, 65, 65, 175))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (65, 65, 65, 200))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, (65, 65, 65, 200))

        dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip, (0, 0, 0, 0))
        dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered, (0, 0, 0, 0))
        dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive, (0, 0, 0, 0))
    #    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 5, 2)

    #    dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 0)
with dpg.theme() as non_transparent_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (55, 55, 55, 255))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (65, 65, 65, 255)) #отдельно для настроек сделать
        #dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 0, 0, 255))       # цвет рамки
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (50, 50, 50, 255))     #
        dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.5, 0.5)
        dpg.add_theme_color(dpg.mvThemeCol_Button, (65, 65, 65, 255))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (75, 75, 75, 255))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (95, 95, 95, 255))
        dpg.add_theme_color(dpg.mvThemeCol_TabActive, (95, 95, 95, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (220, 220, 220, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (255, 255, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (75, 75, 75, 255))

        dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (220, 220, 220, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (65, 65, 65, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (70, 70, 70, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (70, 70, 70, 255))
    with dpg.theme_component(dpg.mvSelectable):
        dpg.add_theme_color(dpg.mvThemeCol_Header, (35, 35, 35, 255))        # выбранный
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (45, 45, 45, 255)) # hover
        dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (65, 65, 65, 255))   # клик



with dpg.theme() as slider_red:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (200, 0, 0, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (225, 0, 0, 255))

with dpg.theme() as slider_green:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (0, 200, 0, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (0, 225, 0, 255))

with dpg.theme() as slider_blue:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (0, 0, 200, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (0, 0, 225, 255))




if len(sys.argv) > 1:
    open_image_from_start(sys.argv[1])
else:
    loaded_image = resource_path("icons/img.jpg")
    width, height, channels, data = dpg.load_image(loaded_image)
    img_aspectratio = width / height
    #print(width, width, img_aspectratio)
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=width, height=height, default_value=data, tag="texture_tag1")


dpg.bind_item_theme("main_window", menu_theme)
dpg.bind_theme(menu_theme)

dpg.bind_item_theme("menu_bar", bar_theme)

dpg.bind_item_theme("menu_btn1", btn_theme)
dpg.bind_item_theme("menu_btn2", btn_theme)
dpg.bind_item_theme("menu_btn3", btn_theme)
dpg.bind_item_theme("menu_btn5", btn_theme)
dpg.bind_item_theme("menu_btn6", btn_theme)

dpg.bind_item_theme("info_window", transparent_theme)
dpg.bind_item_theme("settings_window", non_transparent_theme)
dpg.bind_item_theme("list_window", transparent_theme)
dpg.bind_item_theme("cv_text", transparent_theme)
dpg.bind_item_theme("cv_rgb_shift", transparent_theme)
dpg.bind_item_theme("cv_edge_d", transparent_theme)
dpg.bind_item_theme("rgb_s_1", slider_red)
dpg.bind_item_theme("rgb_s_2", slider_green)
dpg.bind_item_theme("rgb_s_3", slider_blue)
dpg.bind_item_theme("checkbox_1", checkbox_theme)
dpg.bind_item_theme("settings_group1", checkbox_theme)
dpg.bind_item_theme("settings_group2", checkbox_theme)
dpg.bind_item_theme("welcome_window", non_transparent_theme)
dpg.bind_item_theme("message_window", non_transparent_theme)
dpg.bind_item_theme("file_dialog_ext", non_transparent_theme)


with dpg.handler_registry():
    dpg.add_key_press_handler(dpg.mvKey_Left, callback=Controls.prev_img)
    dpg.add_key_press_handler(dpg.mvKey_Right, callback=Controls.next_img)
    dpg.add_key_press_handler(dpg.mvKey_LControl, callback=Controls.clear_img)
    dpg.add_key_press_handler(dpg.mvKey_LAlt, callback=Controls.alt_keys)
    dpg.add_key_press_handler(dpg.mvKey_Return, callback=Window.maximize_window)
    dpg.add_mouse_wheel_handler(callback=Controls.scaling)
    dpg.add_key_press_handler(dpg.mvKey_F, callback=MenuBar.show_edit_mode)
    #dpg.add_mouse_drag_handler(callback=Controls.mouse_drag_handler, user_data="list_window")
    #dpg.add_mouse_down_handler(callback=Controls.mouse_down_handler, user_data="list_window", button=dpg.mvMouseButton_Left)
    #dpg.add_mouse_release_handler(callback=Controls.mouse_release_handler, user_data="list_window", button=dpg.mvMouseButton_Left)
    #dpg.add_mouse_move_handler(callback=dpg_quad)



with dpg.item_handler_registry(tag="inf_resize"):
    dpg.add_item_resize_handler(callback=lambda s,a: configure_text(image_path))

dpg.bind_item_handler_registry("info_window", "inf_resize")

dpg.set_frame_callback(1, callback=lambda s, a, u: user32.ShowWindow(get_hwnd(), SW_MAXIMIZE))

#dpg.add_render_callback(5, tag="msg_timer1", callback=MenuBar.msg_timer)
dpg.set_viewport_resize_callback(on_resize)
on_resize(None, None)
dpg.set_viewport_decorated(True)
dpg.setup_dearpygui()
#dpg.bind_font(default_font)
dpg.show_viewport()

pywinstyles.change_header_color(get_hwnd(), color=rgb2hex((50, 50, 50)))

if Theme.dynamic_theming == True and len(sys.argv) > 1:
    dynamic_img_theme(img_avg_col)

while dpg.is_dearpygui_running():
    # проверяем таймер
    if dpg.is_item_shown("message_window"):
        elapsed = time.perf_counter() - msg_timer_start
        if elapsed >= 1.5:
            dpg.hide_item("message_window")

    if image_list_loaded and not is_frame_refreshed:
        refresh_frame_pos(current_selected_image_item)
        is_frame_refreshed = True

    dpg.render_dearpygui_frame()

dpg.destroy_context()
