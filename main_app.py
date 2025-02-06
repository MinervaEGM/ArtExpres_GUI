from __future__ import division
import os
import http.client
import kivy
kivy.require('1.11.1')
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.animation import Animation
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.core.window import Window
from button import LitoButton
from logs import init_config, write_to_log
Window.fullscreen = 'auto'

absolute_project_directory = os.path.dirname(os.path.realpath(__file__))
init_config(absolute_project_directory)

load_screen = None
lock_screen = None
main_screen = None
lito_screen = None
full_screen = None
buy_screen = None

class MyScreen(Screen):
    event_lock = None
    wait_time = 60 
    
    def __init__(self, **kwargs):
        super(MyScreen, self).__init__(**kwargs)

    def on_touch_up(self, touch):
        self.start_countdown_to_lock_screen()

    def start_countdown_to_lock_screen(self):
        if self.event_lock:
            self.event_lock.cancel()
        self.event_lock = Clock.schedule_once(self.show_lock_screen, self.wait_time)

    def show_lock_screen(self, dt):
        global lock_screen
        lock_screen = LockScreen()
        self.manager.add_widget(lock_screen)
        self.manager.current = 'lock'

    def detected_error(self, error):
        if self.event_lock:
            self.event_lock.cancel()

        logger.error(str(error))
        write_to_log(absolute_project_directory,u'Error during code execution: ' + str(error), '')
        Clock.schedule_once(self.show_load_screen, 1.0)

    def show_load_screen(self, dt):
        global load_screen
        load_screen = LoadScreen()
        self.manager.add_widget(load_screen)
        self.manager.get_screen('load').error = True
        self.manager.current = 'load'
    
    def on_pre_leave(self):
        if self.event_lock:
            self.event_lock.cancel()

class LoadScreen(Screen):
    project_directories = ['data', 'design']
    image_files = ['artist.png', 'back_0.png', 'back_1.png', 'back_2.png', 'back_3.png',
                   'back_4.png', 'back_5.png', 'back_lang_0_off.png', 'back_lang_0_on.png',
                   'back_lang_1_off.png', 'back_lang_1_on.png', 'back_lang_2_off.png',
                   'back_lang_2_on.png', 'background.png', 'buy.png', 'cancel.png',
                   'error.png', 'focus.png', 'full.png', 'home.png', 'info.png',
                   'insert.png', 'lito.png', 'logo_0.png', 'logo_1.png', 'logo_2.png',
                   'logo_lock.png', 'move.png', 'out_1.png', 'out_2.png', 'out_3.png',
                   'out_4.png', 'out_5.png', 'start_buy.png', 'success.png', 'take.png',
                   'touch.png', 'transaction.png', 'zoom.png']
    text_files = ['bottom_message.txt', 'card.txt', 'confirm.txt', 'connecting.txt',
                  'dimentions.txt', 'languages.txt', 'more_information.txt',
                  'processing.txt', 'release.txt', 'sold_out_message.txt', 'step.txt',
                  'success.txt', 'top_message.txt', 'transaction.txt',]
    lito_directories = ['lito_0', 'lito_1', 'lito_2', 'lito_3', 'lito_4',
                        'lito_5', 'lito_6', 'lito_7', 'lito_8', 'lito_9']
    lito_files = ['artist.jpg', 'artist_info_0.txt', 'artist_info_1.txt', 'artist_info_2.txt',
                  'lito.jpg', 'lito_info_0.txt', 'lito_info_1.txt', 'lito_info_2.txt']
    
    errors = []
    
    lbl_action = ObjectProperty()
    pgr_load_progress = ObjectProperty()
    lbl_info = ObjectProperty()

    event_internet = None
    no_internet_connection = False
    error = False
    
    def __init__(self, **kwargs):
        super(LoadScreen, self).__init__(**kwargs)
        
    def on_enter(self):
        if self.error:
            self.error = False
            self.manager.remove_widget(main_screen)
            self.manager.remove_widget(lito_screen)
            self.manager.remove_widget(full_screen)
            self.manager.remove_widget(buy_screen)
            
        if self.no_internet_connection:
            self.no_internet_connection = False
            self.manager.remove_widget(lock_screen)
            
        self.lbl_action.text = u'Starting'
        Animation(value = 50, duration = 10.0, t = 'out_expo').start(self.pgr_load_progress)
        Clock.schedule_once(self.try_internet_connection, 10.0)
            
    def try_internet_connection(self, dt):
        if self.internet_connection_available():
            self.check_data()
        else:
            self.lbl_action.text = u'No internet connection'
            self.lbl_info.text = ''
            Animation(value = 100, duration = 2, t = 'out_expo').start(self.pgr_load_progress)
            write_to_log(absolute_project_directory,u'No internet connection', '')
            self.event_internet = Clock.schedule_interval(self.reload_app, 60.0)
        
    def reload_app(self, dt):
        if self.internet_connection_available():
            write_to_log(absolute_project_directory,u'Internet connection reestablished', '')
            self.event_internet.cancel()
            self.check_data()

    def internet_connection_available(self):
        connection = http.client.HTTPConnection('www.python.org', timeout = 5)
        try:
            connection.request("HEAD", "/")
            connection.close()
            return True
        except:
            connection.close()
            return False
                
    def check_data(self):
        self.lbl_action.text = u'Verifying files'
        
        #Verifying folders
        actual_project_directories = []
        try:
            actual_project_directories = [ f.name for f in os.scandir(absolute_project_directory) if f.is_dir() ]
        except Exception as e:
            logger.warning(e)
            
        for project_directory in self.project_directories:
            self.lbl_info.text = u'Checking folder: /' + project_directory
            if not project_directory in actual_project_directories:
                self.errors.append(u'[ERROR] Folder: /' + project_directory)
                self.errors.append(u'Folder not found')

        #Verifying images
        actual_image_files = []
        try:
            actual_image_files = [ f.name for f in os.scandir(absolute_project_directory + '/design') if f.is_file() ]
        except Exception as e:
            logger.warning(e)
            
        for image_file in self.image_files:
            self.lbl_info.text = u'Checking file: /design/' + image_file
            if not image_file in actual_image_files:
                self.errors.append(u'[ERROR] File: /design/' + image_file)
                self.errors.append(u'File not found')

        #Verifying text
        actual_text_files = []
        try:
            actual_text_files = [ f.name for f in os.scandir(absolute_project_directory + '/data/text') if f.is_file() ]
        except Exception as e:
            logger.warning(e)
        for text_file in self.text_files:
            self.lbl_info.text = u'Checking file: /data/text/' + text_file
            if text_file in actual_text_files:
                try:
                    with open(absolute_project_directory + '/data/text/' + text_file, 'r', encoding = 'utf-8') as file:
                        content = [line.strip() for line in file.readlines()]

                        if not 'end' in content:
                            self.errors.append(u'[ERROR] File: /data/text/' + text_file)
                            self.errors.append(u'Missing key word: end')
                        else:
                            if len(content) < 4:
                                self.errors.append(u'[ERROR] File: /data/text/' + text_file)
                                self.errors.append(u'Missing parameter')
                            else:
                                if not content[-1] == 'end':
                                    self.errors.append(u'[ERROR] File: /data/text/' + text_file)
                                    self.errors.append(u'Key word in incorrect place: end')

                except Exception as e:
                    self.errors.append(u'[ERROR] File: /data/text/' + text_file)
                    self.errors.append(e)
            else:
                self.errors.append(u'[ERROR] File: /data/text/' + text_file)
                self.errors.append(u'File not found')
                
        #Verifying files
        actual_lito_directories = []
        try:
            actual_lito_directories = [ f.name for f in os.scandir(absolute_project_directory + '/data') if f.is_dir() ]
        except Exception as e:
            logger.warning(e)
            
        for lito_directory in self.lito_directories:
            self.lbl_info.text = u'Checking folder: /data/' + lito_directory
            
            if lito_directory in actual_lito_directories:
                
                actual_lito_files = []
                try:
                    actual_lito_files = [ f.name for f in os.scandir(absolute_project_directory + '/data/' + lito_directory) if f.is_file() ]
                except Exception as e:
                    logger.warning(e)
                
                for lito_file in self.lito_files:
                    if lito_file in actual_lito_files:
                        if lito_file.startswith('artist_info_'):
                            try:
                                with open(absolute_project_directory + '/data/' + lito_directory + '/' + lito_file, 'r', encoding = 'utf-8') as file:
                                    content = [line.strip() for line in file.readlines()]

                                    if not 'end' in content:
                                        self.errors.append(u'[ERROR] File: /data/' + lito_directory + '/' + lito_file)
                                        self.errors.append(u'Missing key word: end')
                                    else:
                                        if len(content) < 3:
                                            self.errors.append(u'[ERROR] File: /data/' + lito_directory + '/' + lito_file)
                                            self.errors.append(u'Missing parameter')
                                        else:
                                            if not content[-1] == 'end':
                                                self.errors.append(u'[ERROR] File: /data/' + lito_directory + '/' + lito_file)
                                                self.errors.append(u'Key word in the wrong place: end')

                            except Exception as e:
                                self.errors.append(u'[ERROR] File: /data/' + lito_directory + '/' + lito_file)
                                self.errors.append(e)

                        elif lito_file.startswith('lito_info_'):
                            try:
                                with open(absolute_project_directory + '/data/' + lito_directory + '/' + lito_file, 'r', encoding = 'utf-8') as file:
                                    content = [line.strip() for line in file.readlines()]

                                    if not 'end' in content:
                                        self.errors.append(u'[ERROR] File: /data/' + lito_directory + '/' + lito_file)
                                        self.errors.append(u'Missing key word: end')
                                    else:
                                        if len(content) < 6:
                                            self.errors.append(u'[ERROR] File: /data/' + lito_directory + '/' + lito_file)
                                            self.errors.append(u'Missing parameter')
                                        else:
                                            if not content[-1] == 'end':
                                                self.errors.append(u'[ERROR] File: /data/' + lito_directory + '/' + lito_file)
                                                self.errors.append(u'Key word in the wrong place: end')

                                            try:
                                                float(content[-2])
                                                
                                            except ValueError:
                                                self.errors.append(u'[ERROR] File: /data/' + lito_directory + '/' + lito_file)
                                                self.errors.append(u'Price not valid: ' + content[-2])
                                                self.errors.append(u'It must be a real positive number')
                                                
                            except Exception as e:
                                self.errors.append(u'[ERROR] File: /data/' + lito_directory + '/' + lito_file)
                                self.errors.append(e)
                    else:
                        self.errors.append(u'[ERROR] File: /data/' + lito_directory + '/' + lito_file)
                        self.errors.append(u'File not found')
            else:
                self.errors.append(u'[ERROR] Folder: /data/' + lito_directory)
                self.errors.append(u'Folder not found')
                
        #Verifying counting files
        self.lbl_info.text = u'Checking file: /data/count.txt'
        try:
            with open(absolute_project_directory + '/data/count.txt', 'r', encoding = 'utf-8') as file:
                content = [line.strip() for line in file.readlines()]

                if not 'end' in content:
                    self.errors.append(u'[ERROR] File: /data/count.txt')
                    self.errors.append(u'Missing key word: end')
                else:
                    if len(content) < 11:
                        self.errors.append(u'[ERROR] File: /data/count.txt')
                        self.errors.append(u'Missing parameter')
                    else:
                        if content[-1] == 'end':
                            for line in content:
                                try:
                                    if line == 'end':
                                        break
                                    total = int(line)

                                    if not (0 <= total and total <= 10):
                                        self.errors.append(u'[ERROR] File: /data/count.txt')
                                        self.errors.append(u'Value out of allowed range: ' + line)
                                        self.errors.append(u'It must be an integer between 0 and 10')
                                
                                except ValueError:
                                    self.errors.append(u'[ERROR] File: /data/count.txt')
                                    self.errors.append(u'Value not valid for total elements: ' + line)
                                    self.errors.append(u'It must be an integer between 0 and 10')
                        else:
                            self.errors.append(u'[ERROR] File: /data/count.txt')
                            self.errors.append(u'Key word in the wrong place: end')

        except FileNotFoundError:
            self.errors.append(u'[ERROR] File: /data/count.txt')
            self.errors.append(u'File not found')
        except Exception as e:
            self.errors.append(u'[ERROR] File: /data/count.txt')
            self.errors.append(e)

        #Starting the program if the necesary files exist and are correct
        if (len(self.errors) > 0):
            error_list = ''
            for error in self.errors:
                error_list = error_list + error + '\n'

            self.lbl_action.text = u'Error loading files'
            self.lbl_info.text = error_list
            Animation(value = 100, duration = 2, t = 'out_expo').start(self.pgr_load_progress)
        else:
            self.lbl_action.text = u'Files loaded correctly'
            self.lbl_info.text = ''
            
            global lock_screen
            lock_screen = LockScreen()
            self.manager.add_widget(lock_screen)

            Animation(value = 100, duration = 1, t = 'out_expo').start(self.pgr_load_progress)
            Clock.schedule_once(self.go_to_lock_screen, 1.0)
            write_to_log(absolute_project_directory,u'Program started correctly', '')

    def go_to_lock_screen(self, dt):
        self.manager.get_screen('lock').from_load = True
        self.manager.current = 'lock'

class LockScreen(Screen):
    from_load = False
    number = 9
    for i in range(1, 6): 
        exec(f'event_flash_{i}=None')
        exec(f'img_flash_{i}=ObjectProperty()')

    img_anim_1 = ObjectProperty()
    img_anim_2 = ObjectProperty()
    lbl_lock = ObjectProperty()
    img_bottom = ObjectProperty()
    img_logo = ObjectProperty()
    lbl_unam = ObjectProperty()
    lbl_subtitle = ObjectProperty()
    img_focus = ObjectProperty()
    
    def __init__(self, **kwargs):
        super(LockScreen, self).__init__(**kwargs)

    def on_pre_enter(self):
        self.lbl_unam.text = u'M É X I C O / U N A M'
        self.lbl_subtitle.text = u'En apoyo a jóvenes artistas'
        try:
            with open(absolute_project_directory + '/data/text/bottom_message.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]

                self.lbl_subtitle.text = str(content[0])
        except FileNotFoundError as e:
            logger.warning(e)
        except Exception as e:
            logger.warning(e)
            
    def on_enter(self):
        Clock.schedule_interval(self.touch_hint, 2.0)
        Clock.schedule_once(self.animation_loop)
        Clock.schedule_interval(self.animation_loop, 30.0)
        Clock.schedule_interval(self.check_internet_connection, 60.0)

        if self.from_load:
            self.from_load = False
            self.manager.remove_widget(load_screen)
        else:
            self.manager.remove_widget(main_screen)
            self.manager.remove_widget(lito_screen)
            self.manager.remove_widget(full_screen)
            self.manager.remove_widget(buy_screen)

    def check_internet_connection(self, dt):
        if not self.internet_connection_available():
            self.go_to_load_screen()

    def go_to_load_screen(self):
        global load_screen
        load_screen = LoadScreen()
        self.manager.add_widget(load_screen)
        self.manager.get_screen('load').no_internet_connection = True
        self.manager.current = 'load'

    #Animation cicle
    def animation_loop(self, dt):
        #LOGO
        self.background_color = [1, 1, 1, 1]
        self.img_anim_1.source = ''
        self.img_anim_2.source = ''
        self.img_anim_1.pos_hint = {'x':1, 'y':0}
        self.img_anim_2.pos_hint = {'x':1, 'y':0}
        self.img_anim_1.size_hint = (0, 0)
        self.img_anim_2.size_hint = (0, 0)
        
        self.img_logo.opacity = 1
        self.lbl_unam.opacity = 1
        self.lbl_subtitle.opacity = 1
        self.lbl_lock.opacity = 0
        self.img_bottom.opacity = 0
        self.img_bottom.source = 'design/back_0.png'
        Animation(opacity = 1, duration = 0.5, t = 'linear').start(self.img_bottom)
        
        for i, delay in enumerate([3.7, 3.2, 2.5, 1.8, 1.3], start=1):
            event = getattr(self, f"event_flash_{i}")
            image = getattr(self, f"img_flash_{i}")
            image.opacity = 0
            image.source = f'design/back_{i}.png'
            event = Clock.schedule_interval(lambda dt, i=i: self.flash(image),delay)

        logo_schedule=[9.0,9.2,9.4,9.6,9.8]
        for i in range(1,6):
            exec(f"Clock.schedule_once(self.out_{i}, logo_schedule[{i-1}])")

        image_schedule = [10.0,11.0,17.0,18.0,23.5,24.5]
        for i in range(1,7):
            exec(f"Clock.schedule_once(self.animation_{i}, image_schedule[{i-1}])")

    def flash(self, widget):
        anim = Animation(opacity = 0.4, duration = 0.5) + Animation(opacity = 0, duration = 0.5)
        anim.start(widget)
        
    def out_1(self, dt):
        self.event_flash_1.cancel()
        Animation.stop_all(self.img_flash_1)
        self.img_flash_1.source = 'design/back_0.png'
        self.img_flash_1.opacity = 1
        self.img_bottom.source = 'design/out_1.png'
        Animation(opacity = 0, duration = 0.2, t = 'linear').start(self.img_flash_1)
        Animation(opacity = 0, duration = 1.0, t = 'in_expo').start(self.img_logo)

    def out_2(self, dt):
        self.img_flash_1.source = 'design/out_2.png'
        Animation(opacity = 1, duration = 0.2, t = 'linear').start(self.img_flash_1)

    def out_3(self, dt):
        self.img_bottom.source = 'design/out_3.png'
        Animation(opacity = 0, duration = 0.2, t = 'linear').start(self.img_flash_1)

    def out_4(self, dt):
        self.img_flash_1.source = 'design/out_4.png'
        Animation(opacity = 1, duration = 0.2, t = 'linear').start(self.img_flash_1)

    def out_5(self, dt):
        self.img_bottom.source = 'design/out_5.png'
        Animation(opacity = 0, duration = 0.2, t = 'linear').start(self.img_flash_1)

    def animation_1(self, dt):
        for i in range(6):
            event = getattr(self, f"event_flash_{i}")
            image = getattr(self, f"img_flash_{i}")
            event.cancel()
            Animation.stop_all(image)
            image.opacity = 0
            image.source = ''

        Animation(background_color = [0, 0, 0, 1], duration = 2, t = 'linear').start(self)

        self.lbl_unam.opacity = 0
        self.lbl_subtitle.opacity = 0
        self.img_bottom.opacity = 0

        self.img_anim_1.opacity = 1
        self.img_anim_2.opacity = 1
        
        self.number = self.number + 1

        if self.number > 9:
            self.number = 0
        
        self.img_anim_1.source = self.get_lito_path(self.number)
        self.img_anim_2.source = self.get_lito_path(self.number)

        self.img_anim_1.size_hint = (1, 1)
        self.img_anim_1.pos_hint = {'x':1, 'y':0}

        #Moving from the right
        Animation(pos_hint = {'x':0, 'y':0}, duration = 1, t = 'in_out_quart').start(self.img_anim_1)

    def animation_2(self, dt):
        #Close up
        Animation(size_hint = (1.1, 1.1), pos_hint = {'x':-0.05, 'y':-0.05}, duration = 6, t = 'linear').start(self.img_anim_1)

        try:
            with open(absolute_project_directory + '/data/lito_' + str(self.number) + '/lito_info_0.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]

                self.lbl_lock.text = '"' + content[0] + '"\n' + content[1]
                Animation(opacity = 1, duration = 0.5).start(self.lbl_lock)
        except FileNotFoundError as e:
            logger.warning(e)
        except Exception as e:
            logger.warning(e)

    def animation_3(self, dt):
        self.img_anim_2.size_hint = (1.5, 4)
        self.img_anim_2.pos_hint = {'x':1.1, 'y':-1.5}

        #Moving from the right
        Animation(pos_hint = {'x':-1.1, 'y':-0.05}, duration = 1, t = 'in_out_quart').start(self.img_anim_1)
        Animation(pos_hint = {'x':0, 'y':-1.5}, duration = 1, t = 'in_out_quart').start(self.img_anim_2)

    def animation_4(self, dt):
        #Horizontal movement
        Animation(pos_hint = {'x':-0.5, 'y':-1.5}, duration = 5.5, t = 'in_out_quad').start(self.img_anim_2)
        Animation(opacity = 0, duration = 2).start(self.lbl_lock)

    def animation_5(self, dt):
        self.img_anim_1.size_hint = (2, 1.5)
        self.img_anim_1.pos_hint = {'x':-0.5, 'y':-1.5}

        ##Moving from below
        Animation(pos_hint = {'x':-0.5, 'y':-0.5}, duration = 1, t = 'in_out_quart').start(self.img_anim_1)
        Animation(pos_hint = {'x':-0.5, 'y':1}, duration = 1, t = 'in_out_quart').start(self.img_anim_2)

    def animation_6(self, dt):
        #Vertical movement
        Animation(pos_hint = {'x':-0.5, 'y':0}, duration = 5.5, t = 'in_out_quad').start(self.img_anim_1)

    def touch_hint(self, dt):
        self.img_focus.size_hint = (0, 0)
        self.img_focus.pos_hint = {'x':0.9, 'y':0.85}
        self.img_focus.opacity = 1
        Animation(size_hint = (0.2, 0.3), pos_hint = {'x':0.8, 'y':0.7}, opacity = 0, duration = 1, t = 'linear').start(self.img_focus)

    def show_main_screen(self):
        if self.internet_connection_available():
            global main_screen, lito_screen, full_screen, buy_screen
            main_screen = MainScreen()
            lito_screen = LitoScreen()
            full_screen = FullScreen()
            buy_screen = BuyScreen()
            self.manager.add_widget(main_screen)
            self.manager.add_widget(lito_screen)
            self.manager.add_widget(full_screen)
            self.manager.add_widget(buy_screen)
            
            self.manager.get_screen('main').selection = -1
            self.manager.get_screen('main').from_lock = True
            self.manager.current = 'main'
        else:
            self.go_to_load_screen()

    def on_pre_leave(self):
        for event in Clock.get_events():
            event.cancel()
        
    def get_lito_path(self, number):
        if (0 <= number) and (number <= 9):
            return 'data/lito_' + str(number) + '/lito.jpg'
        else:
            return 'design/error.png'

    def internet_connection_available(self):
        connection = http.client.HTTPConnection('www.python.org', timeout = 5)
        try:
            connection.request("HEAD", "/")
            connection.close()
            return True
        except:
            connection.close()
            return False

class MainScreen(MyScreen):
    selection = -1
    language = 0
    available = []
    first_load = True
    first_more_info = True
    from_lock = False
    for i in range(10):
        exec(f"btn_lito_{i} = ObjectProperty(None)")
        exec(f"lbl_lito_{i}_info = ObjectProperty(None)")

    lyt_start = ObjectProperty()
    lbl_top_message = ObjectProperty()
    img_logo = ObjectProperty()
    lbl_bottom_message = ObjectProperty()
    for i in range(3):
        exec(f"btn_lang_{i} = ObjectProperty(None)")
        exec(f"lbl_lang_{i} = ObjectProperty(None)")

    lyt_center = ObjectProperty()
    img_center = ObjectProperty()
    lbl_title = ObjectProperty()
    img_info = ObjectProperty()

    bbl_more_info = ObjectProperty()
    bblbtn_more_info = ObjectProperty()

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

    def on_pre_enter(self):
        try:
            with open(absolute_project_directory + '/data/count.txt', 'r', encoding = 'utf-8') as file:
                self.available = file.readlines()
                self.available = [line.strip() for line in self.available]
        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        if self.selection == -1:
            self.first_more_info = True
            self.first_load = True
            self.lyt_start.opacity = 0
            for i in range(10):
                getattr(self, f'btn_lito_{i}').opacity = 0

            self.lyt_start.pos_hint = {'x':0.255, 'y':0.205}
            self.lyt_center.pos_hint = {'x':1, 'y':0}
            self.img_center.source = ''
            self.lbl_title.text = ''

    def on_enter(self):
        if self.selection == -1:
            self.load_language(self.language)
            self.animate_in(0)

        if self.from_lock:
            self.from_lock = False
            self.manager.remove_widget(lock_screen)
            
            write_to_log(absolute_project_directory,u'Pantalla desbloqueada', '')

        Clock.schedule_once(self.fit_images)
        self.start_countdown_to_lock_screen()
        
    def fit_images(self, dt):
        for i in range(10):
            getattr(self, f'btn_lito_{i}').fit_container()

    def load_language(self, number):
        if (number != self.language) or self.first_load:
            self.first_load = False
            self.first_more_info = True
            self.language = number

            for i in range(3):
                getattr(self, f'btn_lang_{i}').source = f'design/back_lang_{i}_off.png'
                getattr(self, f'lbl_lang_{i}').color = [0, 0, 0, 1]

            for i in range(3):
                if self.language == i:
                    getattr(self, f"btn_lang_{i}").source = f'design/back_lang_{i}_on.png'
                    getattr(self, f"lbl_lang_{i}").color = [1, 1, 1, 1]
            for message in ['languages','top_message','bottom_message']:
                try:
                    with open(absolute_project_directory + f'/data/text/{message}.txt', 'r', encoding = 'utf-8') as file:
                        content = file.readlines()
                        content = [line.strip() for line in content]
                        if message == 'languages':
                            exec(f'self.lbl_lang_0.text = content[0]')
                            exec('self.lbl_lang_1.text = content[1]')
                            exec('self.lbl_lang_2.text = content[2]')
                        else:
                            exec(f"self.lbl_{message}.text = content[self.language]")

                except FileNotFoundError as e:
                    self.detected_error(e)
                except Exception as e:
                    self.detected_error(e)
            
            sold_out_message = StringProperty()
            try:
                with open(absolute_project_directory + '/data/text/sold_out_message.txt', 'r', encoding = 'utf-8') as file:
                    content = file.readlines()
                    content = [line.strip() for line in content]

                    sold_out_message = content[self.language].upper()
            except FileNotFoundError as e:
                self.detected_error(e)
            except Exception as e:
                self.detected_error(e)
            
            try:
                for i in range(10):
                    available_count = int(self.available[i])
                    label = getattr(self, f"lbl_lito_{i}_info")
                    if 0 < available_count:
                        self.show_remaining(label,self.available[i])
                    else:
                        self.show_sold_out(label,sold_out_message)
            except Exception as e:
                self.detected_error(e)

            self.img_logo.source = 'design/logo_' + str(self.language) + '.png'
            self.lyt_start.opacity = 0
            Animation(opacity = 1, duration = 0.5).start(self.lyt_start)

    def show_remaining(self, widget, total):
        widget.text = total + '/10'
        widget.halign = 'left'
        widget.valign = 'bottom'            

    def show_sold_out(self, widget, message):
        widget.text = message
        widget.background_color = [0, 0, 0, 0.4]
        widget.halign = 'center'
        widget.valign = 'center'
        size_y = widget.size_hint_y
        widget.size_hint_y = 0
        Animation(size_hint_y = size_y, duration = 1, t = 'out_expo').start(widget)

    def animate_in(self, start):
        for i in range(10):
            btn = getattr(self, f"btn_lito_{i}")  
            delay = self.delay_time(i, start)
            Clock.schedule_once(lambda dt, button=btn: self.animation_in(button), delay) 

    def animation_in(self, widget):
        Animation(opacity = 1, duration = 0.4).start(widget)
        
    def delay_time(self, item, start):
        delay = 0.2
        timed = item - start        
        if timed < 0:
            timed += 10
        if 0 <= timed <= 5:
            return delay + timed * 0.1
        elif 6 <= timed <= 9:
            return delay + (10 - timed) * 0.1
        else:
            return 0
        
    def animate_out(self, start):
        for i in range(10):
            btn = getattr(self, f"btn_lito_{i}")
            if start != i:  
                delay = self.delay_time(i, start)
                Clock.schedule_once(lambda dt, button=btn: self.animation_out(button), delay)
            else:
                btn.opacity = 1

    def animation_out(self, widget):
        Animation(opacity = 0.2, duration = 0.2).start(widget)

    def get_lito_path(self, number):
        if (0 <= number) and (number <= 9):
            return 'data/lito_' + str(number) + '/lito.jpg'
        else:
            return 'design/error.png'

    def dismiss_more_info_bubble(self, dt):
        Animation(opacity = 0, duration = 1, t = 'linear').start(self.bbl_more_info)

    def onClickLito(self, selection):
        
        if selection == self.selection:
            self.selection = -1
            self.animate_in(selection)
            self.lyt_center.pos_hint = {'x':1, 'y':0}
            self.lyt_start.opacity = 0
            self.lyt_start.pos_hint = {'x':0.255, 'y':0.205}
            Animation(opacity = 1, duration = 0.5, t = 'linear').start(self.lyt_start)
            
        else:
            self.selection = selection
            self.animate_out(self.selection)

            self.lyt_start.pos_hint = {'x':1, 'y':0}
            self.lyt_center.opacity = 0
            self.lyt_center.pos_hint = {'x':0.255, 'y':0.205}
            self.img_center.source = self.get_lito_path(self.selection)
            Animation(opacity = 1, duration = 0.5, t = 'linear').start(self.lyt_center)

            try:
                with open(absolute_project_directory + '/data/lito_' + str(self.selection) + '/lito_info_' + str(self.language) + '.txt', 'r', encoding = 'utf-8') as file:
                    content = file.readlines()
                    content = [line.strip() for line in content]
                    self.lbl_title.text = '"' + content[0] + '"\n' + content[1]
            except FileNotFoundError as e:
                self.detected_error(e)
            except Exception as e:
                self.detected_error(e)
            
            #Label adjustment with the name over the image
            image_ratio = self.img_center.texture.size[0] / self.img_center.texture.size[1]
            window_ratio = self.size[0] / self.size[1]
            layout_center_ratio = (self.lyt_center.size_hint_x * window_ratio) / self.lyt_center.size_hint_y
            
            if (image_ratio > layout_center_ratio):
                self.lbl_title.size_hint_x = 1
                self.lbl_title.pos_hint = {'x':0, 'y':(1 - layout_center_ratio / image_ratio) / 2}
                self.img_info.pos_hint = {'x':0.85, 'y': 1 - (1 - layout_center_ratio / image_ratio) / 2 - 0.15}
                self.bbl_more_info.pos_hint = {'x':0.25, 'y': 1 - (1 - layout_center_ratio / image_ratio) / 2 - 0.15}
            else:
                self.lbl_title.size_hint_x = image_ratio / layout_center_ratio
                self.lbl_title.pos_hint = {'x':(1 - image_ratio / layout_center_ratio) / 2, 'y':0}
                self.img_info.pos_hint = {'x':0.5 + 0.5 * self.lbl_title.size_hint_x - 0.13, 'y':.85}
                self.bbl_more_info.pos_hint = {'x':0.5 + 0.5 * self.lbl_title.size_hint_x - 0.13 - 0.60, 'y':.85}
            
            if self.first_more_info:
                self.first_more_info = False
                try:
                    with open(absolute_project_directory + '/data/text/more_information.txt', 'r', encoding = 'utf-8') as file:
                        content = file.readlines()
                        content = [line.strip() for line in content]
                        self.bblbtn_more_info.text = content[self.language]
                except FileNotFoundError as e:
                    self.detected_error(e)
                except Exception as e:
                    self.detected_error(e)
                    
                Animation(opacity = 1, duration = 0.5, t = 'linear').start(self.bbl_more_info)
                Clock.schedule_once(self.dismiss_more_info_bubble, 2.5)

    def on_click_lito_info(self):
        self.manager.get_screen('lito').selection = self.selection
        self.manager.get_screen('lito').language = self.language
        self.manager.get_screen('lito').from_main = True
        try:
            self.manager.get_screen('lito').available = 0 < int(self.available[self.selection])
        except Exception as e:
            self.detected_error(e)
        
        self.manager.current = 'lito'

class LitoScreen(MyScreen):
    from_main = False
    showing_artist = False
    selection = -1
    language = 0
    available = True
    
    title = StringProperty()
    artist = StringProperty()
    dimentions = StringProperty()
    dimen = StringProperty()
    price_mx = NumericProperty()

    lito_info = StringProperty()
    artist_info = StringProperty()

    btn_lito = ObjectProperty()
    btn_layout = ObjectProperty()
    img_background = ObjectProperty()
    for i in range(6):
        exec(f"lbl_info_{i} = ObjectProperty()")
    btn_home = ObjectProperty()
    btn_artist = ObjectProperty()
    btn_buy = ObjectProperty()
    img_full = ObjectProperty()
    scr_info = ObjectProperty()

    def __init__(self, **kwargs):
        super(LitoScreen, self).__init__(**kwargs)

    #REVISADO
    def on_pre_enter(self):
        try:
            with open(absolute_project_directory + '/data/lito_' + str(self.selection) + '/lito_info_' + str(self.language) + '.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]
            
                self.title = content[0]
                self.artist = content[1]
                self.dimen = content[2]
    
                total_lines_description = len(content) - 5
                self.lito_info = ''
                for index in range(3, 3 + total_lines_description):
                    self.lito_info = self.lito_info + content[index] + '\n\n'

                self.price_mx = float(content[-2])
        except FileNotFoundError as e:
            self.detected_error(e)
        except ValueError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        try:
            with open(absolute_project_directory + '/data/text/dimentions.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]

                self.dimentions = content[self.language]
        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        try:
            with open(absolute_project_directory + '/data/lito_' + str(self.selection) + '/artist_info_' + str(self.language) + '.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content] 
            
                total_lines_description = len(content) - 2
                self.artist_info = ''
                for index in range(1, 1 + total_lines_description):
                    self.artist_info = self.artist_info + content[index] + '\n\n'

        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        if (self.from_main):
            self.load_lito_info()
            self.showing_artist = False
            self.btn_lito.opacity = 0
            self.btn_layout.opacity = 0
            self.img_background.opacity = 0
            self.btn_home.opacity = 0
            self.btn_artist.opacity = 0
            self.btn_buy.opacity = 0
            self.img_full.opacity = 0
            self.scr_info.opacity = 0
            self.lbl_info_5.opacity = 0

    def on_enter(self):
        if (self.from_main):
            self.from_main = False
            self.animation_in_0()
            self.animate_info()

            write_to_log(absolute_project_directory,u'Litografía seleccionada', self.selection)
            write_to_log(absolute_project_directory,u'Idioma utilizado', self.language)
            
        self.start_countdown_to_lock_screen()

    def animation_in_0(self):
        self.btn_lito.size_hint = (0.49, 0.59)
        self.btn_lito.pos_hint = {'x':0.255, 'y':0.205}
        self.btn_lito.opacity = 1
        Animation(size_hint = (2, 1), pos_hint = {'x':-0.2, 'y':0}, duration = 1.2, t = 'out_expo').start(self.btn_lito)
        
        self.btn_layout.size_hint = (0, 1)
        Animation(opacity = 1, size_hint = (0.6, 1), duration = 1.2, t = 'out_expo').start(self.btn_layout)

        Clock.schedule_once(lambda dt: self.animation_in(self.btn_home), 1.0)
        Clock.schedule_once(lambda dt: self.animation_in(self.btn_artist), 1.1)
        Clock.schedule_once(self.animation_in_buy, 1.2)
        Clock.schedule_once(lambda dt: self.animation_in(self.img_full), 1.3)
        Clock.schedule_once(self.animation_in_background, 1.4)

    def get_lito_path(self, number):
        if (0 <= number) and (number <= 9):
            return 'data/lito_' + str(number) + '/lito.jpg'
        else:
            return 'design/error.png'

    def get_artist_path(self, number):
        if (0 <= number) and (number <= 9):
            return 'data/lito_' + str(number) + '/artist.jpg'
        else:
            return 'design/error.png'

    def load_lito_info(self):
        self.btn_lito.disabled = False
        self.btn_lito.source = self.get_lito_path(self.selection)
        self.btn_artist.source = 'design/artist.png'
        self.img_full.opacity = 1
        self.scr_info.pos_hint = {'x':0.05, 'y':0.3}
        self.lbl_info_1.text = self.title.upper()
        self.lbl_info_2.text = self.artist.upper()
        self.lbl_info_3.text = self.dimentions.upper() + ': ' + self.dimen
        self.lbl_info_4.text = self.lito_info.upper()
        self.lbl_info_5.text = 'MXN $' + "{:.2f}".format(self.price_mx)

    def load_artist_info(self):
        self.btn_lito.disabled = True
        self.btn_lito.source = self.get_artist_path(self.selection)
        self.btn_artist.source = 'design/lito.png'
        self.img_full.opacity = 0
        self.scr_info.pos_hint = {'x':0.05, 'y':0.25}
        self.lbl_info_1.text = self.artist.upper()
        self.lbl_info_2.text = ''
        self.lbl_info_3.text = ''
        self.lbl_info_4.text = self.artist_info.upper()
        self.lbl_info_5.text = ''

    def animate_info(self):
        self.scr_info.opacity = 0
        for i in range(1, 6):
            getattr(self, f'lbl_info_{i}').opacity = 0

        Clock.schedule_once(self.show_scrollview, 0.4)
        for i, delay in enumerate([0.4, 0.5, 0.6, 0.7, 0.8], start=1):
            Clock.schedule_once(lambda dt, i=i: self.animation_in(getattr(self, f'lbl_info_{i}')), delay)

    def animation_in(self, widget):
        Animation(opacity = 1, duration = 0.4).start(widget)
        
    def show_scrollview(self, dt):
        self.scr_info.scroll_to(self.lbl_info_1, padding = 20, animate = False)
        self.scr_info.opacity = 1

    def animation_in_buy(self, dt):
        if self.available:
            self.btn_buy.disabled = False
            Animation(opacity = 1, duration = 0.4).start(self.btn_buy)
        else:
            self.btn_buy.disabled = True
            Animation(opacity = 0.3, duration = 0.4).start(self.btn_buy)

    def animation_in_background(self, dt):
        Animation(opacity = 0.1, duration = 2, t = 'linear').start(self.img_background)

    def on_click_buy(self, selection):
        self.manager.get_screen('buy').selection = self.selection
        self.manager.get_screen('buy').language = self.language
        self.manager.get_screen('buy').title = self.title
        self.manager.get_screen('buy').artist = self.artist
        self.manager.get_screen('buy').dimentions = self.dimentions
        self.manager.get_screen('buy').dimen = self.dimen
        self.manager.get_screen('buy').price_mx = self.price_mx
        self.manager.current = 'buy'

    def on_click_info_artist(self):
        if self.showing_artist:
            self.showing_artist = False
            self.load_lito_info()
        else:
            self.showing_artist = True
            self.load_artist_info()

        self.animate_info()
        self.btn_lito.opacity = 0
        Animation(opacity = 1, duration = 0.5).start(self.btn_lito)
        
    def on_click_lito_full(self):
        self.manager.get_screen('full').selection = self.selection
        self.manager.current = 'full'

class FullScreen(MyScreen):
    selection = -1

    img_lito = ObjectProperty()
    img_close = ObjectProperty()
    scatter = ObjectProperty()
    lbl_zoom = ObjectProperty()
    sld_zoom = ObjectProperty()
    img_move = ObjectProperty()
    
    def __init__(self, **kwargs):
        super(FullScreen, self).__init__(**kwargs)
        self.sld_zoom.bind(value = self.on_slider_change)

    def on_pre_enter(self):
        self.background_color = [1, 1, 1, 1]
        self.img_lito.opacity = 0
        self.img_lito.source = self.get_lito_path(self.selection)
        self.img_move.opacity = 0
        self.scatter.scale = 1
        self.scatter.pos = (0, 0)
        self.sld_zoom.value = 1
        self.lbl_zoom.text = 'x' + "{:.1f}".format(self.scatter.scale)
        
    def on_enter(self):
        Animation(background_color = [0, 0, 0, 1], duration = 0.5, t = 'out_expo').start(self)
        Clock.schedule_once(self.show_image, 0.3)
        self.start_countdown_to_lock_screen()

    def show_image(self, dt):
        Animation(opacity = 1, duration = 1, t = 'out_expo').start(self.img_lito)

    def on_change(self):
        screen_size = (self.size[0], self.size[1])
        texture_size = self.img_lito.texture.size

        scatter_pos = self.scatter.pos
        scater_scale = self.scatter.scale

        containerRatio = self.size[0] / self.size[1]
        textureRatio = texture_size[0] / texture_size[1]

        image_size = (0, 0)
        if (textureRatio <= containerRatio):
            image_size = (screen_size[1] * textureRatio, screen_size[1])
        else:
            image_size = (screen_size[0], screen_size[0] / textureRatio)

        offset_x = (screen_size[0] - image_size[0]) * scater_scale / 2
        offset_y = (screen_size[1] - image_size[1]) * scater_scale / 2

        total_position_x = scatter_pos[0] + offset_x
        total_position_y = scatter_pos[1] + offset_y

        total_size_x = image_size[0] * scater_scale
        total_size_y = image_size[1] * scater_scale

        left_limit = screen_size[0] - total_size_x
        right_limit = total_size_x
        top_limit = total_size_y
        bottom_limit = screen_size[1] - total_size_y

        if (total_size_x > screen_size[0]):
            if (total_position_x < left_limit):
                self.scatter.pos = (left_limit - offset_x, self.scatter.pos[1])
            if (total_position_x + total_size_x > right_limit):
                self.scatter.pos = (- offset_x, self.scatter.pos[1])
        else:
            self.scatter.pos = ((screen_size[0] / 2) - (screen_size[0] * scater_scale) / 2 , self.scatter.pos[1])
            
        if (total_size_y > screen_size[1]):
            if (total_position_y + total_size_y > top_limit):
                self.scatter.pos = (self.scatter.pos[0], - offset_y)
            if (total_position_y < bottom_limit):
                self.scatter.pos = (self.scatter.pos[0], bottom_limit - offset_y)
        else:
            self.scatter.pos = (self.scatter.pos[0], (screen_size[1] / 2) - (screen_size[1] * scater_scale) / 2)

        if (scater_scale > 1.1):
            self.img_move.opacity = 0.6
        else:
            self.img_move.opacity = 0

        self.lbl_zoom.text = 'x' + "{:.1f}".format(scater_scale)
        self.sld_zoom.value = scater_scale

    def on_slider_change(self, instance, value):
        screen_size = (self.size[0], self.size[1])
        scater_scale = self.scatter.scale

        self.scatter.pos = ((screen_size[0] / 2) - (screen_size[0] * scater_scale) / 2 ,
                            (screen_size[1] / 2) - (screen_size[1] * scater_scale) / 2)
        
        self.scatter.scale = value
        self.lbl_zoom.text = 'x' + "{:.1f}".format(value)

        if (self.scatter.scale > 1.1):
            self.img_move.opacity = 0.6
        else:
            self.img_move.opacity = 0
            
    def get_lito_path(self, number):
        if (0 <= number) and (number <= 9):
            return 'data/lito_' + str(number) + '/lito.jpg'
        else:
            return 'design/error.png'

class BuyScreen(MyScreen):
    selection = -1
    language = 0
    
    title = StringProperty()
    artist = StringProperty()
    dimentions = StringProperty()
    dimen = StringProperty()
    price_mx = NumericProperty()
    step_message = StringProperty()

    layout_buy = ObjectProperty()
    img_buy = ObjectProperty()
    lbl_details_1 = ObjectProperty()
    lbl_details_2 = ObjectProperty()
    lbl_details_3 = ObjectProperty()
    lbl_details_4 = ObjectProperty()
    btn_buy = ObjectProperty()
    lbl_message_buy = ObjectProperty()
    pgr_progress = ObjectProperty()
    img_back = ObjectProperty()
    img_hint = ObjectProperty()
    btn_cancel = ObjectProperty()
    layout_info = ObjectProperty()
    lbl_step = ObjectProperty()
    layout_buttons = ObjectProperty()
    lbl_hint = ObjectProperty()
    
    def __init__(self, **kwargs):
        super(BuyScreen, self).__init__(**kwargs)

    def on_pre_enter(self):
        try:
            with open(absolute_project_directory + '/data/text/transaction.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]
                self.lbl_message_buy.text = content[self.language]
        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        try:
            with open(absolute_project_directory + '/data/text/confirm.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]
                self.lbl_details_1.text = content[self.language].upper()
        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        self.lbl_details_2.text = '"' + self.title + '"\n' + self.artist
        self.lbl_details_3.text = self.dimentions + ': ' + self.dimen
        self.lbl_details_4.text = 'MXN $' + "{:.2f}".format(self.price_mx)

        self.pgr_progress.value = 0
        self.img_buy.opacity = 0
        self.img_buy.source = self.get_lito_path(self.selection)

        self.img_back.opacity = 1
        self.img_back.source = self.get_lito_path(self.selection)
        self.img_back.size_hint = (1.4, 3.4)
        self.img_back.pos_hint = {'x':-0.2, 'y':-1.2}
        
        self.layout_buy.size_hint = (0.45, 0.5)
        self.layout_buy.pos_hint = {'x':0.5, 'y':0.4}
        self.layout_buy.opacity = 0
        
        self.layout_buttons.size_hint = (0.45, 0.1)
        self.layout_buttons.pos_hint = {'x':0.5, 'y':0.25}
        self.layout_buttons.opacity = 0
        
        self.layout_info.pos_hint = {'x':1, 'y':0}

    def on_enter(self):
        anim = Animation(pos_hint = {'x':0, 'y':-1}, size_hint = (1, 3), duration = 1.2, t = 'out_expo')
        anim &= Animation(opacity = 0.25, duration = 0.6, t = 'linear')
        anim.start(self.img_back)

        write_to_log(absolute_project_directory,u'Intento de compra de litografía', self.selection)
        
        Clock.schedule_once(self.animate_in, 0.5)
        self.start_countdown_to_lock_screen()
        
    def animate_in(self, dt):
        Animation(opacity = 1, duration = 0.5, t = 'out_expo').start(self.img_buy)
        Animation(opacity = 1, duration = 0.5, t = 'out_expo').start(self.layout_buy)
        Animation(opacity = 1, duration = 0.5, t = 'out_expo').start(self.layout_buttons)
        
    def get_lito_path(self, number):
        if (0 <= number) and (number <= 9):
            return 'data/lito_' + str(number) + '/lito.jpg'
        else:
            return 'design/error.png'
    
    def start_transaction(self):
        try:
            with open(absolute_project_directory + '/data/text/processing.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]
                self.lbl_details_1.text = content[self.language].upper()
        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        #Code to activate the terminal. When the terminal is ready, it has to call self.on_terminal_ready()
        Clock.schedule_once(self.on_terminal_ready, 1.0)

    def on_terminal_ready(self, dt):
        try:
            with open(absolute_project_directory + '/data/text/card.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]
                self.lbl_hint.text = content[self.language]
        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        try:
            with open(absolute_project_directory + '/data/text/step.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]
                self.step_message = content[self.language]
        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        self.layout_buttons.pos_hint = {'x':1, 'y':0}
        
        self.layout_info.pos_hint = {'x':0.5, 'y':-0.05}
        self.layout_info.opacity = 0
        
        self.lbl_step.opacity = 1
        self.lbl_step.text = self.step_message + ' 1/3'

        self.pgr_progress.opacity = 1
        self.pgr_progress.value = 0
        
        self.img_hint.source = 'design/insert.png'

        Animation(pos_hint = {'x':0.5, 'y':0.5}, duration = 1, t = 'out_expo').start(self.layout_buy)
        Animation(pos_hint = {'x':0.5, 'y':0.05}, opacity = 1, duration = 1, t = 'out_expo').start(self.layout_info)
        Animation(value = 33, duration = 0.5, t = 'linear').start(self.pgr_progress)

        self.wait_for_lecture()
        
    def wait_for_lecture(self):
        #Code to read the credit card. When it reads it, call self.transaction()
        Clock.schedule_once(self.transaction, 2.0)

    def transaction(self, dt): #Include credit card data as argument
        try:
            with open(absolute_project_directory + '/data/text/connecting.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]
                self.lbl_hint.text = content[self.language]
        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        self.lbl_step.text = self.step_message + ' 2/3'
        self.img_hint.source = 'design/transaction.png'

        Animation(value = 66, duration = 0.5, t = 'linear').start(self.pgr_progress)
        Clock.schedule_once(self.release, 1.5)

    def release(self, dt):
        try:
            with open(absolute_project_directory + '/data/text/release.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]
                self.lbl_hint.text = content[self.language]
        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        self.lbl_step.text = self.step_message + ' 3/3'
        self.img_hint.source = 'design/take.png'

        Animation(value = 100, duration = 0.5, t = 'linear').start(self.pgr_progress)
        self.release_lito()

    def release_lito(self):
        print(u'Compra de litografía ' + str(self.selection))
        Clock.schedule_once(self.servo_back, 2.0)

    def servo_back(self, dt):
        self.finish()
    def finish(self):
        try:
            with open(absolute_project_directory + '/data/text/success.txt', 'r', encoding = 'utf-8') as file:
                content = file.readlines()
                content = [line.strip() for line in content]
                self.lbl_hint.text = content[self.language]
        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)
            
        self.img_hint.source = 'design/success.png'

        self.lbl_step.opacity = 0
        self.pgr_progress.opacity = 0

        available = []
        try:
            with open(absolute_project_directory + '/data/count.txt', 'r', encoding = 'utf-8') as file:
                available = file.readlines()
                available = [line.strip() for line in available]

                available[self.selection] = str(int(available[self.selection]) - 1)
                
        except FileNotFoundError as e:
            self.detected_error(e)
        except ValueError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        try:
            with open(absolute_project_directory + '/data/count.txt', 'w') as file:
                for i in range(10):
                    file.write(str(available[i]) + '\n')
                file.write('end')
        except FileNotFoundError as e:
            self.detected_error(e)
        except Exception as e:
            self.detected_error(e)

        write_to_log(absolute_project_directory,u'Compra de litografía completada', self.selection)
        Clock.schedule_once(self.go_to_home, 2.5)
         
    def go_to_home(self, dt):
        self.manager.get_screen('main').selection = -1
        self.manager.current = 'main'

    def on_click_cancel(self):
        self.manager.current = 'lito'
        
Builder.load_file('design.kv')

class Application(App):
    def build(self):
        global load_screen
        load_screen = LoadScreen()
        screen_manager = ScreenManager(transition = NoTransition())
        screen_manager.add_widget(load_screen)
        return screen_manager

if __name__ == '__main__':
    Application().run()
