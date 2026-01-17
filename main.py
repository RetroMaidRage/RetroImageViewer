import dearpygui.dearpygui as dpg
import os
import sys
import ctypes
import webbrowser

user32 = ctypes.windll.user32

user32.SetProcessDPIAware()

screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)

def get_hwnd():
    return user32.FindWindowW(None, "RetroImageViewer")

SW_MINIMIZE = 6
SW_RESTORE = 9
SW_MAXIMIZE = 3
SW_SHOWDEFAULT = 10

isMaximized = False
dragging = False

img_tag = 0

custom_decorator = False

print("Screen resolution:",screen_w,"x",screen_h)



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

    def start_drag(sender, app_data):
        global dragging, drag_offset
        dragging = True
        mouse_pos = dpg.get_mouse_pos()
        viewport_pos = dpg.get_viewport_pos()
        drag_offset = [mouse_pos[0] - viewport_pos[0], mouse_pos[1] - viewport_pos[1]]


    def stop_drag(sender, app_data):
        global dragging
        dragging = False

    def window_drag():
        global dragging, drag_offset
        if dragging:
            mouse_pos = dpg.get_mouse_pos()
            viewport_pos = dpg.get_viewport_pos()
            new_x = mouse_pos[0] - viewport_pos[0]
            new_y = mouse_pos[1] - viewport_pos[1]
            dpg.set_viewport_pos(mouse_pos)
            print("Dragging",mouse_pos)


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def show_about():
    webbrowser.open("https://github.com/RetroMaidRage/RetroImageViewer")

def print_me(sender):
    print(f"Menu Item: {sender}")

def show_dialogue(sender):
    dpg.show_item("file_dialog")

def app_close():
    dpg.stop_dearpygui()

def configure_image(file, width, height):
    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()

    window_height = dpg.get_item_height("main_window")

    print("VH: "+str(viewport_height)+" WH: "+str(window_height))
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
    y = window_pos[1] + (viewport_height - img_h) / 2

    dpg.set_item_width("main_window", viewport_width)
    dpg.set_item_height("main_window", viewport_height)
    dpg.configure_item("main_img", width=img_w, height=img_h, pos=[x, y])

    image_data = f"""{file} Resolution:  {str(width)}x{str(height)}"""
    dpg.configure_item("main_window", label=image_data)
    print(f"""Image size: {img_w}x{img_h}""")


def open_image(sender, app_data):
    global img_tag, img_aspectratio, loaded_image
    file_path = app_data["file_path_name"]
    found = False
    if file_path.endswith(".*"):
        folder = os.path.dirname(file_path)
        print("Dir: "+file_path)
        name = os.path.splitext(os.path.basename(file_path))[0]
        for file in os.listdir(folder):
            if file.startswith(name) and file.lower().endswith((".jpg", ".png")):
                file_path = os.path.join(folder, file)
                print("Opened: "+"Filepath: "+file_path)
                found = True
                break

        if not found:
            print("Can't open this file. "+"Filepath: "+file_path)
            return

    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()
    loaded_image = dpg.load_image(file_path)

    if loaded_image is None:
        print("Wrong image/can't load it."+"Filepath: "+file_path)
        return

    width, height, channels, data = loaded_image
    img_aspectratio = width / height

    img_tag += 1
    new_img_tag = "img_"+str(img_tag)

    print(f"""Image: {name} | Res: {width}x{height} | Tag: {new_img_tag}""")

    with dpg.texture_registry(show=False):
       dpg.add_static_texture(width=width, height=height, default_value=data, tag=new_img_tag)


    dpg.configure_item("main_img", texture_tag=new_img_tag)

    configure_image(file_path, width, height)
    on_resize(None, None)

def open_image_from_start(file_path):
    global img_tag, img_aspectratio, loaded_image

    print(file_path)

    loaded_image = dpg.load_image(file_path)

    if loaded_image is None:
        print("n")
        return

    width, height, channels, data = loaded_image
    img_aspectratio = width / height

    img_tag += 1
    new_img_tag = "img_"+str(img_tag) #тут безмыслено создавать тг каждый раз

    print(f"""Image: {file_path} | Res: {width}x{height} | Tag: {new_img_tag}""")

    with dpg.texture_registry(show=False):
       dpg.add_static_texture(width=width, height=height, default_value=data, tag=new_img_tag)


    dpg.configure_item("main_img", texture_tag=new_img_tag)

    configure_image(file_path, width, height)
    on_resize(None, None)

dpg.create_context()
#dpg.create_viewport(title='RetroImageViewer', width=screen_w//2, height=screen_h//2, x_pos=screen_w//4, y_pos=screen_h//4)
dpg.create_viewport(title='RetroImageViewer', width=screen_w, height=screen_h, x_pos=0, y_pos=0)
with dpg.font_registry():
    default_font = dpg.add_font(resource_path("fonts/selawk.ttf"), 24)

dpg.bind_font(default_font)
with dpg.texture_registry(show=False):
    dpg.add_static_texture(1, 1, default_value=[50/255,50/255,50/255,255], tag="texture_tag")
#main
with dpg.viewport_menu_bar(tag="menu_bar"):

    with dpg.group(horizontal=True, tag="left_menu_group"):
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="Save", callback=print_me)
            dpg.add_menu_item(label="Save As", callback=print_me)
            dpg.add_menu_item(label="Open...", callback=show_dialogue)
        with dpg.menu(label="Edit"):
            dpg.add_menu_item(label="0", callback=print_me)
        with dpg.menu(label="View"):
            dpg.add_menu_item(label="0", callback=print_me)
        dpg.add_menu_item(label="About", callback=show_about)

    dpg.add_spacer(width=0, tag="spacer")
    dpg.set_item_pos("left_menu_group", [0, 0])

    if custom_decorator == True:
        dpg.set_viewport_decorated(False)
        with dpg.group(horizontal=True, tag="right_menu_group"):
            dpg.add_menu_item(label="-", callback=Window.minimize_window)
            dpg.add_menu_item(label="[]", callback=Window.maximize_window)
            dpg.add_menu_item(label="x", callback=app_close)


with dpg.window(label="", tag="main_window", pos=[0,30],
 no_move=True, no_collapse=True,no_close=True, no_scrollbar=False, no_scroll_with_mouse=False, no_resize=True):



    dpg.add_image("texture_tag", tag='main_img')

with dpg.file_dialog(directory_selector=False,show=False,callback=open_image,tag="file_dialog", width=screen_w//3, height=screen_h//3):
    dpg.add_file_extension(".*", color=(255, 255, 255, 255))
    dpg.add_file_extension(".jpg", color=(144, 238, 144, 255))
    dpg.add_file_extension(".png", color=(144, 238, 143, 255))

def on_resize(sender, app_data):
    global img_aspectratio
    viewport_width = dpg.get_viewport_width()
    viewport_height = dpg.get_viewport_height()

    title_offset = 30  # смещение под title barы
    # Считаем доступное место для картинки
    available_height = viewport_height - title_offset
    available_width = viewport_width

    # Подгоняем картинку по меньшей стороне
    aspect_img = img_aspectratio
    aspect_view = available_width / available_height

    if aspect_img > aspect_view:
        img_w = available_width*0.975
        img_h = img_w / aspect_img
    else:
        img_h = available_height*0.975 #добавить в open image
        img_w = img_h * aspect_img

    # Центрируем картинку с учётом смещения
    x = (viewport_width - img_w) / 2
    y = (available_height - img_h) / 2 + title_offset

    dpg.set_item_width("main_window", viewport_width)
    dpg.set_item_height("main_window", viewport_height)
    dpg.configure_item("main_img", width=img_w, height=img_h, pos=[x, y])

    print(f"""Image size after resize: {str(int(img_w))}x{img_h}""")

#with dpg.handler_registry() as drag_handlers:
#    dpg.add_mouse_down_handler(button=0, callback=Window.start_drag)
#    dpg.add_mouse_release_handler(button=0, callback=Window.stop_drag)
#    dpg.add_mouse_move_handler(callback=Window.window_drag)

# привязываем к menu_bar


with dpg.theme() as menu_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (65, 65, 65, 255))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (65, 65, 65, 255))
        #dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 0, 0, 255))       # цвет рамки
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (50, 50, 50, 255))     #
        dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.5, 0.5)

if len(sys.argv) > 1:
    open_image_from_start(sys.argv[1])
else:
    loaded_image = resource_path("1.jpg")
    width, height, channels, data = dpg.load_image(loaded_image)
    img_aspectratio = width / height
    print(width, width, img_aspectratio)
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=width, height=height, default_value=data, tag="texture_tag1")


dpg.bind_item_theme("main_window", menu_theme)
dpg.bind_theme(menu_theme)

dpg.set_viewport_resize_callback(on_resize)
on_resize(None, None)

dpg.set_viewport_decorated(True)
dpg.setup_dearpygui()
dpg.bind_font(default_font)
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
