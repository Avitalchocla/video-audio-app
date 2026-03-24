import os
import sys
import shutil
import re
from pathlib import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.video import Video
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty, BooleanProperty, ListProperty, ObjectProperty, NumericProperty
from kivy.lang import Builder
from kivy.utils import platform
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from kivy.uix.behaviors import DragBehavior

if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path

FFMPEG_FILENAME = "ffmpeg"
FONT_FILENAME = "NotoSansHebrew.ttf"


class DraggableSubtitleEntry(BoxLayout):
    """Subtitle entry with drag support"""
    text = StringProperty('')
    start_time = StringProperty('00:00:00')
    end_time = StringProperty('00:00:05')
    entry_id = ObjectProperty(0)
    is_dragging = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(70)
        self.spacing = dp(5)
        self.padding = dp(5)
        self.drag_start_pos = None
        
        # Background
        with self.canvas.before:
            Color(0.15, 0.15, 0.2, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        # Drag handle
        drag_btn = Button(
            text='☰',
            size_hint_x=0.08,
            background_color=(0.3, 0.3, 0.4, 1)
        )
        drag_btn.bind(on_touch_down=self.on_drag_start)
        drag_btn.bind(on_touch_move=self.on_drag_move)
        drag_btn.bind(on_touch_up=self.on_drag_end)
        self.add_widget(drag_btn)
        
        # Number
        self.num_label = Label(
            text=str(self.entry_id),
            size_hint_x=0.06,
            color=(0.5, 0.5, 0.5, 1)
        )
        self.add_widget(self.num_label)
        
        # Preview button
        preview_btn = Button(
            text='▶️',
            size_hint_x=0.08,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        preview_btn.bind(on_press=self.preview_subtitle)
        self.add_widget(preview_btn)
        
        # Start time
        self.start_input = TextInput(
            text=self.start_time,
            hint_text='התחלה',
            size_hint_x=0.16,
            multiline=False,
            halign='center',
            font_size='13sp'
        )
        self.add_widget(self.start_input)
        
        # End time
        self.end_input = TextInput(
            text=self.end_time,
            hint_text='סוף',
            size_hint_x=0.16,
            multiline=False,
            halign='center',
            font_size='13sp'
        )
        self.add_widget(self.end_input)
        
        # Text
        self.text_input = TextInput(
            text=self.text,
            hint_text='טקסט כתובית...',
            size_hint_x=0.38,
            multiline=False,
            halign='right',
            font_size='14sp'
        )
        self.add_widget(self.text_input)
        
        # Delete
        delete_btn = Button(
            text='🗑️',
            size_hint_x=0.08,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        delete_btn.bind(on_press=self.delete_self)
        self.add_widget(delete_btn)
        
        # Bind text changes
        self.text_input.bind(text=self.on_text_change)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def on_drag_start(self, touch):
        if touch.button == 'left':
            self.is_dragging = True
            self.drag_start_pos = touch.pos
            self.opacity = 0.7
            return True
        return False
    
    def on_drag_move(self, touch):
        if self.is_dragging:
            # Visual feedback only - actual reorder on drop
            return True
        return False
    
    def on_drag_end(self, touch):
        if self.is_dragging:
            self.is_dragging = False
            self.opacity = 1.0
            
            # Find if dropped on another entry
            parent = self.parent
            if parent:
                for child in parent.children:
                    if child != self and isinstance(child, DraggableSubtitleEntry):
                        if child.collide_point(*touch.pos):
                            # Swap positions
                            self.swap_with(child)
                            break
            
            # Reorder all IDs
            self.reorder_siblings()
            return True
        return False
    
    def swap_with(self, other):
        """Swap data with another entry"""
        # Swap all properties
        self.start_input.text, other.start_input.text = other.start_input.text, self.start_input.text
        self.end_input.text, other.end_input.text = other.end_input.text, self.end_input.text
        self.text_input.text, other.text_input.text = other.text_input.text, self.text_input.text
    
    def reorder_siblings(self):
        """Reorder all entries by start time"""
        parent = self.parent
        if not parent:
            return
        
        entries = [c for c in parent.children if isinstance(c, DraggableSubtitleEntry)]
        entries.sort(key=lambda x: x.get_seconds())
        
        for i, entry in enumerate(entries, 1):
            entry.entry_id = i
            entry.num_label.text = str(i)
    
    def get_seconds(self):
        """Get start time in seconds for sorting"""
        try:
            h, m, s = self.start_input.text.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
        except:
            return 0
    
    def preview_subtitle(self, instance):
        """Preview this subtitle in video"""
        app = App.get_running_app()
        if app.video_path:
            # Seek to start time
            start_sec = self.get_seconds()
            app.seek_video(start_sec)
            app.show_preview_text(self.text_input.text)
    
    def on_text_change(self, instance, value):
        """Update preview when text changes"""
        app = App.get_running_app()
        if app.current_preview_entry == self:
            app.show_preview_text(value)
    
    def delete_self(self, instance):
        if self.parent:
            self.parent.remove_widget(self)
            # Reorder remaining
            Clock.schedule_once(lambda dt: self.reorder_siblings(), 0.1)
    
    def get_data(self):
        return {
            'id': self.entry_id,
            'start': self.start_input.text,
            'end': self.end_input.text,
            'text': self.text_input.text
        }


class VideoAudioApp(App):
    video_path = StringProperty('')
    audio_path = StringProperty('')
    subtitle_path = StringProperty('')
    status_text = StringProperty('בחר סרטון ואודיו')
    add_subtitles = BooleanProperty(False)
    preview_text = StringProperty('')
    current_preview_entry = ObjectProperty(None, allownone=True)
    video_position = NumericProperty(0)
    
    def build(self):
        self.ffmpeg_path = None
        self.font_path = None
        self.output_path = None
        self.preview_popup = None
        
        if platform == 'android':
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.INTERNET,
            ])
        
        Window.clearcolor = (0.05, 0.05, 0.1, 1)
        Clock.schedule_once(lambda dt: self.setup_files(), 0)
        
        return Builder.load_string(self.get_kv())
    
    def get_kv(self):
        return '''
BoxLayout:
    orientation: 'vertical'
    
    TabbedPanel:
        do_default_tab: False
        tab_height: dp(50)
        
        # Tab 1: Main
        TabbedPanelHeader:
            text: 'ראשי'
            BoxLayout:
                orientation: 'vertical'
                padding: dp(15)
                spacing: dp(10)
                
                Label:
                    text: 'Video Audio Replacer'
                    font_size: '24sp'
                    size_hint_y: 0.06
                    bold: True
                    color: 0.6, 0.4, 1, 1
                
                Label:
                    text: app.status_text
                    font_size: '13sp'
                    size_hint_y: 0.04
                    color: 0.6, 0.6, 0.6, 1
                
                Button:
                    text: '📹 ' + (app.video_path.split('/')[-1][:20] if app.video_path else 'בחר סרטון')
                    size_hint_y: 0.09
                    background_color: 0.2, 0.5, 0.9, 1
                    background_normal: ''
                    on_press: app.show_filechooser('video')
                
                Button:
                    text: '🎵 ' + (app.audio_path.split('/')[-1][:20] if app.audio_path else 'בחר אודיו חדש')
                    size_hint_y: 0.09
                    background_color: 0.2, 0.7, 0.4, 1
                    background_normal: ''
                    on_press: app.show_filechooser('audio')
                
                BoxLayout:
                    size_hint_y: 0.08
                    spacing: dp(10)
                    
                    Label:
                        text: 'הוסף כתוביות:'
                        size_hint_x: 0.4
                        halign: 'right'
                    
                    Switch:
                        id: sub_switch
                        active: app.add_subtitles
                        on_active: app.add_subtitles = self.active
                        size_hint_x: 0.2
                    
                    Button:
                        text: 'ערוך כתוביות'
                        disabled: not app.add_subtitles
                        background_color: 0.9, 0.6, 0.2, 1
                        background_normal: ''
                        on_press: app.open_subtitle_editor()
                        size_hint_x: 0.4
                
                ProgressBar:
                    id: progress
                    value: 0
                    max: 100
                    size_hint_y: 0.03
                
                Button:
                    text: '▶ התחל עיבוד'
                    size_hint_y: 0.1
                    background_color: 0.8, 0.3, 0.8, 1
                    background_normal: ''
                    font_size: '18sp'
                    bold: True
                    on_press: app.start_processing()
                    disabled: not app.video_path or not app.audio_path or not app.ffmpeg_path
                
                Video:
                    id: video_player
                    size_hint_y: 0.3
                    state: 'stop'
                    on_position: app.video_position = self.position
                
                # Preview overlay
                Label:
                    id: preview_label
                    text: app.preview_text
                    size_hint_y: 0.08
                    font_size: '20sp'
                    bold: True
                    color: 1, 1, 0, 1
                    opacity: 1 if app.preview_text else 0
                
                Button:
                    text: '▶ נגן תוצאה'
                    size_hint_y: 0.07
                    background_color: 0.3, 0.6, 0.3, 1
                    background_normal: ''
                    on_press: app.play_output()
                    disabled: not app.output_path
        
        # Tab 2: Subtitle Editor with Preview
        TabbedPanelHeader:
            text: 'עורך כתוביות'
            BoxLayout:
                orientation: 'vertical'
                padding: dp(5)
                spacing: dp(5)
                
                # Video preview section
                BoxLayout:
                    size_hint_y: 0.25
                    orientation: 'vertical'
                    
                    Video:
                        id: editor_video
                        size_hint_y: 0.85
                        state: 'stop'
                    
                    # Time slider
                    Slider:
                        id: time_slider
                        size_hint_y: 0.15
                        min: 0
                        max: 100
                        value: 0
                        on_value: app.on_slider_change(self.value)
                
                # Preview text overlay
                Label:
                    id: editor_preview
                    text: app.preview_text
                    size_hint_y: 0.06
                    font_size: '18sp'
                    bold: True
                    color: 1, 0.9, 0, 1
                    canvas.before:
                        Color:
                            rgba: 0, 0, 0, 0.7
                        Rectangle:
                            pos: self.pos
                            size: self.size
                
                # Controls
                BoxLayout:
                    size_hint_y: 0.08
                    spacing: dp(5)
                    
                    Button:
                        text: '⏮️'
                        on_press: app.seek_relative(-5)
                    
                    Button:
                        text: '▶️' if editor_video.state == 'pause' else '⏸️'
                        on_press: app.toggle_editor_video()
                    
                    Button:
                        text: '⏭️'
                        on_press: app.seek_relative(5)
                    
                    Button:
                        text: '⏮️ -1s'
                        on_press: app.adjust_time(-1)
                    
                    Button:
                        text: '+1s ⏭️'
                        on_press: app.adjust_time(1)
                    
                    Button:
                        text: '👁️ תצוגה'
                        background_color: 0.2, 0.6, 0.8, 1
                        on_press: app.preview_current_subtitle()
                
                # Editor controls
                BoxLayout:
                    size_hint_y: 0.07
                    spacing: dp(5)
                    
                    Button:
                        text: '+ הוסף'
                        background_color: 0.2, 0.7, 0.4, 1
                        on_press: app.add_subtitle_entry()
                    
                    Button:
                        text: '📥 ייבוא'
                        background_color: 0.2, 0.5, 0.9, 1
                        on_press: app.import_srt()
                    
                    Button:
                        text: '💾 שמור'
                        background_color: 0.9, 0.6, 0.2, 1
                        on_press: app.save_srt()
                    
                    Button:
                        text: '🗑️ נקה'
                        background_color: 0.8, 0.2, 0.2, 1
                        on_press: app.clear_subtitles()
                    
                    Button:
                        text: '🔄 סדר'
                        background_color: 0.6, 0.2, 0.8, 1
                        on_press: app.sort_subtitles()
                
                # Headers
                BoxLayout:
                    size_hint_y: 0.05
                    spacing: dp(5)
                    
                    Label:
                        text: ''
                        size_hint_x: 0.08
                    
                    Label:
                        text: '#'
                        size_hint_x: 0.06
                        bold: True
                    
                    Label:
                        text: '▶️'
                        size_hint_x: 0.08
                        bold: True
                    
                    Label:
                        text: 'התחלה'
                        size_hint_x: 0.16
                        bold: True
                    
                    Label:
                        text: 'סוף'
                        size_hint_x: 0.16
                        bold: True
                    
                    Label:
                        text: 'טקסט'
                        size_hint_x: 0.38
                        bold: True
                    
                    Label:
                        text: ''
                        size_hint_x: 0.08
                
                # Subtitle list
                ScrollView:
                    GridLayout:
                        id: subtitle_list
                        cols: 1
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(3)
'''
    
    def setup_files(self):
        """Extract FFmpeg and font"""
        try:
            self.status_text = 'מכין קבצים...'
            app_dir = Path(self.user_data_dir)
            
            ffmpeg_dest = app_dir / FFMPEG_FILENAME
            if not ffmpeg_dest.exists():
                ffmpeg_source = self.find_ffmpeg_source()
                if ffmpeg_source:
                    shutil.copy2(ffmpeg_source, ffmpeg_dest)
                    os.chmod(ffmpeg_dest, 0o755)
                    self.ffmpeg_path = str(ffmpeg_dest)
                else:
                    self.status_text = '❌ FFmpeg לא נמצא'
                    return
            else:
                self.ffmpeg_path = str(ffmpeg_dest)
            
            font_dest = app_dir / FONT_FILENAME
            if not font_dest.exists():
                font_source = self.find_font_source()
                if font_source:
                    shutil.copy2(font_source, font_dest)
                    self.font_path = str(font_dest)
                else:
                    self.download_font()
            else:
                self.font_path = str(font_dest)
            
            self.status_text = '✅ מוכן! בחר קבצים'
            
        except Exception as e:
            self.status_text = f'שגיאה: {str(e)}'
    
    def find_ffmpeg_source(self):
        paths = ['assets/ffmpeg', './assets/ffmpeg', 
                os.path.join(os.path.dirname(__file__), 'assets', 'ffmpeg')]
        
        if platform == 'android':
            from jnius import autoclass
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            paths.extend([
                activity.getFilesDir().getAbsolutePath() + '/app/assets/ffmpeg',
            ])
        
        for path in paths:
            if os.path.isfile(path):
                return path
        
        if platform == 'android':
            return self.extract_from_apk('ffmpeg')
        return None
    
    def find_font_source(self):
        paths = ['assets/NotoSansHebrew.ttf', './assets/NotoSansHebrew.ttf',
                os.path.join(os.path.dirname(__file__), 'assets', 'NotoSansHebrew.ttf')]
        
        for path in paths:
            if os.path.isfile(path):
                return path
        
        if platform == 'android':
            return self.extract_from_apk('NotoSansHebrew.ttf')
        return None
    
    def extract_from_apk(self, filename):
        try:
            from jnius import autoclass
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            asset_manager = activity.getAssets()
            
            input_stream = asset_manager.open(filename)
            temp_path = os.path.join(self.user_data_dir, filename)
            
            with open(temp_path, 'wb') as f:
                f.write(input_stream.read())
            
            input_stream.close()
            return temp_path
        except:
            return None
    
    def download_font(self):
        try:
            import requests
            url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansHebrew/NotoSansHebrew-Regular.ttf"
            font_path = Path(self.user_data_dir) / FONT_FILENAME
            
            response = requests.get(url, timeout=30)
            with open(font_path, 'wb') as f:
                f.write(response.content)
            
            self.font_path = str(font_path)
        except:
            pass
    
    def show_filechooser(self, file_type):
        content = BoxLayout(orientation='vertical', spacing=10)
        
        if platform == 'android':
            root_path = primary_external_storage_path()
        else:
            root_path = os.path.expanduser('~')
        
        if file_type == 'video':
            filters = ['*.mp4', '*.avi', '*.mov', '*.mkv']
            title = 'בחר סרטון'
        elif file_type == 'audio':
            filters = ['*.mp3', '*.wav', '*.aac', '*.m4a']
            title = 'בחר אודיו'
        else:
            filters = ['*.srt', '*.txt']
            title = 'בחר קובץ'
        
        filechooser = FileChooserListView(path=root_path, filters=filters)
        content.add_widget(filechooser)
        
        btn_box = BoxLayout(size_hint_y=0.08, spacing=10)
        select_btn = Button(text='בחר', background_color=(0.2, 0.8, 0.4, 1))
        cancel_btn = Button(text='ביטול', background_color=(0.8, 0.2, 0.2, 1))
        
        popup = Popup(title=title, content=content, size_hint=(0.95, 0.9))
        
        def on_select(instance):
            if filechooser.selection:
                path = filechooser.selection[0]
                if file_type == 'video':
                    self.video_path = path
                    # Load video in editor too
                    Clock.schedule_once(lambda dt: self.load_video_in_editor(), 0.5)
                elif file_type == 'audio':
                    self.audio_path = path
                else:
                    self.subtitle_path = path
                    self.load_srt(path)
                popup.dismiss()
        
        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=popup.dismiss)
        
        btn_box.add_widget(select_btn)
        btn_box.add_widget(cancel_btn)
        content.add_widget(btn_box)
        
        popup.open()
    
    def load_video_in_editor(self):
        """Load video in editor tab"""
        editor_video = self.root.ids.editor_video
        if self.video_path and os.path.exists(self.video_path):
            editor_video.source = self.video_path
            editor_video.state = 'pause'
    
    def open_subtitle_editor(self):
        """Switch to editor tab"""
        self.root.switch_to(self.root.tab_list[1])
        if self.video_path:
            self.load_video_in_editor()
    
    # Video control methods
    def on_slider_change(self, value):
        """Seek video to slider position"""
        editor_video = self.root.ids.editor_video
        if editor_video.duration > 0:
            position = (value / 100) * editor_video.duration
            editor_video.seek(position / editor_video.duration)
            self.update_preview_at_time(position)
    
    def seek_video(self, seconds):
        """Seek to specific time"""
        editor_video = self.root.ids.editor_video
        if editor_video.duration > 0:
            editor_video.seek(seconds / editor_video.duration)
            self.root.ids.time_slider.value = (seconds / editor_video.duration) * 100
    
    def seek_relative(self, delta):
        """Seek relative to current position"""
        editor_video = self.root.ids.editor_video
        new_pos = editor_video.position + delta
        new_pos = max(0, min(new_pos, editor_video.duration))
        self.seek_video(new_pos)
    
    def toggle_editor_video(self):
        """Play/pause editor video"""
        editor_video = self.root.ids.editor_video
        if editor_video.state == 'play':
            editor_video.state = 'pause'
        else:
            editor_video.state = 'play'
            # Start preview update loop
            Clock.schedule_interval(self.update_preview_loop, 0.1)
    
    def update_preview_loop(self, dt):
        """Update preview text based on video position"""
        if self.root.ids.editor_video.state != 'play':
            return False  # Stop clock
        
        current_time = self.root.ids.editor_video.position
        self.update_preview_at_time(current_time)
        return True
    
    def update_preview_at_time(self, seconds):
        """Find and display subtitle at given time"""
        subtitle_list = self.root.ids.subtitle_list
        
        for child in subtitle_list.children:
            if isinstance(child, DraggableSubtitleEntry):
                start = child.get_seconds()
                try:
                    h, m, s = child.end_input.text.split(':')
                    end = int(h) * 3600 + int(m) * 60 + float(s)
                except:
                    end = start + 5
                
                if start <= seconds <= end:
                    self.show_preview_text(child.text_input.text)
                    self.current_preview_entry = child
                    # Highlight entry
                    child.canvas.before.get_group('a')[0].rgba = (0.3, 0.3, 0.5, 1)
                else:
                    # Remove highlight
                    child.canvas.before.get_group('a')[0].rgba = (0.15, 0.15, 0.2, 1)
    
    def show_preview_text(self, text):
        """Show text in preview overlay"""
        self.preview_text = text
        # Auto-hide after 3 seconds if no active entry
        if not self.current_preview_entry:
            Clock.schedule_once(lambda dt: self.hide_preview(), 3)
    
    def hide_preview(self):
        self.preview_text = ''
    
    def preview_current_subtitle(self):
        """Preview currently selected subtitle"""
        if self.current_preview_entry:
            start = self.current_preview_entry.get_seconds()
            self.seek_video(start)
            self.show_preview_text(self.current_preview_entry.text_input.text)
    
    def adjust_time(self, delta):
        """Adjust current subtitle time"""
        if self.current_preview_entry:
            entry = self.current_preview_entry
            start = entry.get_seconds() + delta
            start = max(0, start)
            
            h = int(start // 3600)
            m = int((start % 3600) // 60)
            s = start % 60
            entry.start_input.text = f"{h:02d}:{m:02d}:{s:05.2f}"
            
            # Adjust end time too
            try:
                eh, em, es = entry.end_input.text.split(':')
                end = int(eh) * 3600 + int(em) * 60 + float(es) + delta
                end = max(start + 1, end)  # At least 1 second duration
                eh = int(end // 3600)
                em = int((end % 3600) // 60)
                es = end % 60
                entry.end_input.text = f"{eh:02d}:{em:02d}:{es:05.2f}"
            except:
                entry.end_input.text = f"{h:02d}:{m:02d}:{s+5:05.2f}"
    
    # Subtitle editor methods
    def add_subtitle_entry(self, start_time=None, end_time=None, text=''):
        """Add new subtitle entry"""
        subtitle_list = self.root.ids.subtitle_list
        
        # Auto-calculate time
        if start_time is None:
            if subtitle_list.children:
                last = subtitle_list.children[0]
                try:
                    h, m, s = last.end_input.text.split(':')
                    start = int(h) * 3600 + int(m) * 60 + float(s)
                except:
                    start = 0
            else:
                current = self.root.ids.editor_video.position
                start = current if current > 0 else 0
            
            h = int(start // 3600)
            m = int((start % 3600) // 60)
            s = start % 60
            start_time = f"{h:02d}:{m:02d}:{s:05.2f}"
            end_time = f"{h:02d}:{m:02d}:{s+3:05.2f}"  # 3 seconds default
        
        entry = DraggableSubtitleEntry(
            entry_id=len(subtitle_list.children) + 1,
            start_time=start_time,
            end_time=end_time,
            text=text
        )
        
        subtitle_list.add_widget(entry)
        subtitle_list.height = subtitle_list.minimum_height
        
        # Auto preview
        self.current_preview_entry = entry
        self.seek_video(entry.get_seconds())
    
    def clear_subtitles(self):
        self.root.ids.subtitle_list.clear_widgets()
        self.root.ids.subtitle_list.height = 0
    
    def sort_subtitles(self):
        """Sort all subtitles by start time"""
        subtitle_list = self.root.ids.subtitle_list
        entries = [c for c in subtitle_list.children if isinstance(c, DraggableSubtitleEntry)]
        
        # Sort
        entries.sort(key=lambda x: x.get_seconds())
        
        # Clear and re-add
        subtitle_list.clear_widgets()
        for i, entry in enumerate(entries, 1):
            entry.entry_id = i
            entry.num_label.text = str(i)
            subtitle_list.add_widget(entry)
        
        subtitle_list.height = subtitle_list.minimum_height
    
    def import_srt(self):
        self.show_filechooser('subtitle')
    
    def load_srt(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.clear_subtitles()
            
            pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)\n\n'
            matches = re.findall(pattern, content + '\n\n', re.DOTALL)
            
            for num, start, end, text in matches:
                start_simple = start.replace(',', '.')[:8]
                end_simple = end.replace(',', '.')[:8]
                self.add_subtitle_entry(start_simple, end_simple, text.strip())
            
            self.status_text = f'נטענו {len(matches)} כתוביות'
            
        except Exception as e:
            self.status_text = f'שגיאה: {str(e)}'
    
    def save_srt(self):
        try:
            subtitle_list = self.root.ids.subtitle_list
            entries = []
            
            for child in reversed(subtitle_list.children):
                if isinstance(child, DraggableSubtitleEntry):
                    entries.append(child.get_data())
            
            entries.sort(key=lambda x: self.time_to_seconds(x['start']))
            
            srt_content = ""
            for i, entry in enumerate(entries, 1):
                start = self.format_srt_time(entry['start'])
                end = self.format_srt_time(entry['end'])
                srt_content += f"{i}\n{start} --> {end}\n{entry['text']}\n\n"
            
            srt_path = os.path.join(self.user_data_dir, 'edited_subtitles.srt')
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            self.subtitle_path = srt_path
            self.status_text = f'נשמרו {len(entries)} כתוביות'
            
        except Exception as e:
            self.status_text = f'שגיאה: {str(e)}'
    
    def time_to_seconds(self, time_str):
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s)
        except:
            pass
        return 0
    
    def format_srt_time(self, time_str):
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = parts
                return f"{h}:{m}:{s.replace('.', ',')},000"[:12]
        except:
            pass
        return "00:00:00,000"
    
    # Processing methods
    def start_processing(self):
        if not self.video_path or not self.audio_path or not self.ffmpeg_path:
            return
        
        if self.add_subtitles:
            self.save_srt()
        
        from threading import Thread
        Thread(target=self.process_video, daemon=True).start()
    
    def process_video(self):
        try:
            Clock.schedule_once(lambda dt: setattr(self, 'status_text', 'מעבד...'), 0)
            
            subtitle_file = None
            if self.add_subtitles and self.subtitle_path and os.path.exists(self.subtitle_path):
                subtitle_file = self.convert_srt_to_ass(self.subtitle_path)
            
            video_dir = Path(self.video_path).parent
            timestamp = str(int(Clock.get_time()))
            self.output_path = str(video_dir / f'output_{timestamp}.mp4')
            
            import subprocess
            
            if subtitle_file and self.font_path and os.path.exists(subtitle_file):
                filter_complex = f"subtitles={subtitle_file}:fontsdir={os.path.dirname(self.font_path)}:force_style='FontName=Noto Sans Hebrew,FontSize=24'"
                
                cmd = [
                    self.ffmpeg_path,
                    '-i', self.video_path,
                    '-i', self.audio_path,
                    '-filter_complex', filter_complex,
                    '-map', '[v]',
                    '-map', '1:a',
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '23',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-shortest',
                    '-y',
                    '-progress', 'pipe:1',
                    self.output_path
                ]
            else:
                cmd = [
                    self.ffmpeg_path,
                    '-i', self.video_path,
                    '-i', self.audio_path,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-shortest',
                    '-y',
                    '-progress', 'pipe:1',
                    self.output_path
                ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            duration = None
            for line in process.stdout:
                line = line.strip()
                
                if 'Duration' in line:
                    try:
                        time_str = line.split('Duration: ')[1].split(',')[0]
                        h, m, s = time_str.split(':')
                        duration = int(h) * 3600 + int(m) * 60 + float(s)
                    except:
                        pass
                
                elif 'out_time_ms=' in line:
                    try:
                        ms = int(line.split('out_time_ms=')[1].split()[0])
                        current = ms / 1000000.0
                        if duration and duration > 0:
                            progress = (current / duration) * 100
                            Clock.schedule_once(
                                lambda dt, p=progress: self.update_progress(p), 0
                            )
                    except:
                        pass
            
            process.wait()
            
            if process.returncode == 0:
                Clock.schedule_once(lambda dt: self.on_success(), 0)
            else:
                Clock.schedule_once(
                    lambda dt: setattr(self, 'status_text', '❌ שגיאה'), 0
                )
                
        except Exception as e:
            Clock.schedule_once(
                lambda dt: setattr(self, 'status_text', f'שגיאה: {str(e)}'), 0
            )
    
    def convert_srt_to_ass(self, srt_path):
        ass_path = srt_path.replace('.srt', '.ass')
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        entries = re.findall(
            r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)\n\n',
            srt_content + '\n\n',
            re.DOTALL
        )
        
        ass_header = f"""[Script Info]
Title: Hebrew Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans Hebrew,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        ass_body = ""
        for num, start, end, text in entries:
            start = start.replace(',', '.')
            end = end.replace(',', '.')
            text = text.replace('\n', '\\N')
            ass_body += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"
        
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_header + ass_body)
        
        return ass_path
    
    def update_progress(self, value):
        self.root.ids.progress.value = max(0, min(100, value))
    
    def on_success(self):
        self.status_text = '✅ הושלם!'
        self.root.ids.progress.value = 100
        self.root.ids.video_player.source = self.output_path
        self.root.ids.video_player.state = 'play'
    
    def play_output(self):
        if self.output_path and os.path.exists(self.output_path):
            self.root.ids.video_player.source = self.output_path
            self.root.ids.video_player.state = 'play'


if __name__ == '__main__':
    VideoAudioApp().run()