bl_info = {
    "name": "GotoAndPlay",
    "author": "pongbuster",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "View3D > N sidebar",
    "description": "Add ability loop timeline ranges and mouse 'hitbox' interaction",
    "warning": "",
    "doc_url": "",
    "category": "Sequencer",
}

import bpy
from bpy.props import IntProperty

class GotoAndPlayOperator(bpy.types.Operator):
    fullscreen : IntProperty(default=1)
    """Operator which controls VSE timeline"""
    bl_idname = "wm.goto_and_play_operator"
    bl_label = "GotoAndPlay"

    _timer = None
    _prev = None
    
    def get_markerframe(self, context, marker_name):
        marker = context.scene.timeline_markers.get(marker_name)
        if marker: return marker.frame
        if marker_name.isnumeric(): return int(marker_name)
        print("marker: " + str(marker_name) + " not found")
        return None        

    def modal(self, context, event):
        if event.type in {'ESC'}:
            self.cancel(context)
            context.scene.frame_start = 1
            context.scene.frame_current = 1
            bpy.ops.screen.animation_cancel()
            if self.fullscreen:
                bpy.ops.screen.screen_full_area(use_hide_panels=True)
                bpy.ops.wm.window_fullscreen_toggle()
            return {'CANCELLED'}
        
        elif event.type == 'LEFTMOUSE':
            return {'PASS_THROUGH'}
        
        elif event.type == 'TIMER':
            nFrame = int(context.scene.frame_current)
            for seq in context.scene.sequence_editor.sequences_all:
                if nFrame >= seq.frame_start and nFrame < seq.frame_start + seq.frame_final_duration:
                    if seq.get('loop') and seq.get('loop') == True:
                        context.scene.frame_start = int(seq.frame_start)
                        context.scene.frame_end = int(seq.frame_start + seq.frame_final_duration)
                        if nFrame >= seq.frame_start + seq.frame_final_duration - 2:
                            context.scene.frame_current = context.scene.frame_start
                    
                    if seq.get('goto'):
                        goto_frame = self.get_markerframe(context, str(seq.get('goto')))
                        if goto_frame:
                            clickable = seq.get("clickable")
                            if clickable == True and seq.select == True:
                                context.scene.frame_start = goto_frame
                                context.scene.frame_current = context.scene.frame_start
                                context.scene.frame_end = 36000
                            elif nFrame >= seq.frame_start + seq.frame_final_duration:
                                context.scene.frame_start = goto_frame
                                context.scene.frame_current = context.scene.frame_start
                seq.select = False
                    
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if self.fullscreen: # set preview window fullscreen
            area = [a for a in context.screen.areas if a.type == 'SEQUENCE_EDITOR' if a.spaces[0].view_type == 'PREVIEW']
            
            if len(area) == 0:
                print("No Video Sequencer preview area found")
                return {'CANCELLED'}
            space = [s for s in area[0].spaces if s.type == 'SEQUENCE_EDITOR']
            
            override = {'screen' : context.screen, 'area' : area[0], 'region' : area[0].regions[-1], 'space' : space }
            with context.temp_override(**override):
                bpy.ops.sequencer.view_all_preview()
                bpy.ops.screen.screen_full_area(use_hide_panels=True)
                bpy.ops.wm.window_fullscreen_toggle()
            
        for seq in context.scene.sequence_editor.sequences_all: seq.select = False
        
        wm = context.window_manager
        self._timer = wm.event_timer_add(1/24, window=context.window)
        wm.modal_handler_add(self)
        
        bpy.ops.screen.animation_play(sync=True)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


def menu_func(self, context):
    self.layout.operator(GotoAndPlayOperator.bl_idname, text=GotoAndPlayOperator.bl_label)


def register():
    bpy.utils.register_class(GotoAndPlayOperator)
    bpy.types.SEQUENCER_MT_view.append(menu_func)


def unregister():
    bpy.utils.unregister_class(GotoAndPlayOperator)
    bpy.types.SEQUENCER_MT_view.remove(menu_func)


if __name__ == "__main__":
    #register()

    # test call
    bpy.ops.wm.goto_and_play_operator(fullscreen=1)
