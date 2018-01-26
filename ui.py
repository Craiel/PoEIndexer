import core
from kivy.clock import Clock

from kivy.app import App
from kivy.uix.button import Button
from kivy.animation import Animation

# TODO:
# https://kivy.org/docs/api-kivy.uix.recycleview.html#kivy.uix.recycleview.RecycleView
# https://github.com/kivy/kivy/tree/master/examples/demo/showcase/data/screens

class UIApp(App):

    def build(self):
        indexer_core = core.IndexerCore()
        Clock.schedule_interval(indexer_core.update, 1.0 / 60.0)
        return indexer_core