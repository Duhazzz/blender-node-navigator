bl_info = {
    "name": "Node Navigator",
    "author": "ChatGPT and duhazzz",
    "version": (1, 7),
    "blender": (3, 0, 0),
    "location": "Node Editor > Alt + Arrow keys or Alt + Mouse buttons/wheel",
    "description": (
        "Navigate between connected nodes using keyboard or mouse:\n"
        "- Alt + Left/Right Arrow or Alt + LMB/RMB: move to previous/next connected node.\n"
        "- Alt + Up Arrow or Alt + MMB: show popup with all connected neighbor nodes.\n"
        "Popup panel allows fast selection and auto-centering of view on selected node."
    ),
    "category": "Node",
}

import bpy
from bpy.types import Operator, Panel
from bpy.props import BoolProperty, EnumProperty

addon_keymaps = []

# Navigation core

def get_connected_nodes(node, direction="NEXT"):
    connected = []
    if direction == "NEXT":
        for output in node.outputs:
            for link in output.links:
                if link.to_node:
                    connected.append(link.to_node)
    else:
        for input in node.inputs:
            for link in input.links:
                if link.from_node:
                    connected.append(link.from_node)
    return connected

class NODE_OT_move_connected(Operator):
    bl_idname = "node.move_connected"
    bl_label = "Move to Connected Node"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        items=[
            ("LEFT", "Previous", "Go to previous (input) node"),
            ("RIGHT", "Next", "Go to next (output) node"),
        ],
        default="RIGHT"
    )

    def execute(self, context):
        space = context.space_data
        if space.type != 'NODE_EDITOR':
            self.report({'WARNING'}, "Not in Node Editor")
            return {'CANCELLED'}

        tree = space.edit_tree
        if not tree:
            return {'CANCELLED'}

        active_node = tree.nodes.active

        if not active_node:
            self.report({'INFO'}, "No active node")
            return {'CANCELLED'}

        dir_key = "PREV" if self.direction == "LEFT" else "NEXT"
        connected = get_connected_nodes(active_node, dir_key)

        if not connected:
            self.report({'INFO'}, "No connected node found")
            return {'CANCELLED'}

        target_node = connected[0]
        for node in tree.nodes:
            node.select = False
        target_node.select = True
        tree.nodes.active = target_node

        if context.scene.node_navigator_settings.auto_center:
            bpy.ops.node.view_selected()

        return {'FINISHED'}

class NODE_OT_move_connected_mouse(Operator):
    bl_idname = "node.move_connected_mouse"
    bl_label = "Move to Connected Node via Mouse"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        items=[
            ("LEFT", "Previous", "Go to previous (input) node"),
            ("RIGHT", "Next", "Go to next (output) node"),
        ],
        default="RIGHT"
    )

    def execute(self, context):
        return bpy.ops.node.move_connected('INVOKE_DEFAULT', direction=self.direction)

class NODE_OT_show_node_navigator_mouse(Operator):
    bl_idname = "node.show_node_navigator_mouse"
    bl_label = "Show Node Navigator via Mouse"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return bpy.ops.node.show_node_navigator('INVOKE_DEFAULT')

class NODE_OT_select_specific_connected(Operator):
    bl_idname = "node.select_specific_connected"
    bl_label = "Select Connected Node"
    bl_options = {'REGISTER', 'UNDO'}

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        tree = context.space_data.edit_tree
        node = tree.nodes.get(self.node_name)
        if node:
            for n in tree.nodes:
                n.select = False
            node.select = True
            tree.nodes.active = node
            if context.scene.node_navigator_settings.auto_center:
                bpy.ops.node.view_selected()
            return {'FINISHED'}
        self.report({'WARNING'}, f"Node '{self.node_name}' not found")
        return {'CANCELLED'}

class NODE_MT_node_navigator_popup(Panel):
    bl_idname = "NODE_MT_node_navigator_popup"
    bl_label = "Node Navigator"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        node = context.space_data.edit_tree.nodes.active
        settings = context.scene.node_navigator_settings

        if not node:
            layout.label(text="No active node", icon='ERROR')
            return

        layout.label(text=f"Active Node: {node.name}", icon='NODE')
        layout.separator()

        next_nodes = get_connected_nodes(node, "NEXT")
        prev_nodes = get_connected_nodes(node, "PREV")

        row = layout.row()
        col_inputs = row.column()
        col_outputs = row.column()

        if prev_nodes:
            col_inputs.label(text="Inputs:")
            for n in prev_nodes:
                col_inputs.operator("node.select_specific_connected", text=n.name).node_name = n.name
        else:
            col_inputs.label(text="No input nodes")

        if next_nodes:
            col_outputs.label(text="Outputs:")
            for n in next_nodes:
                col_outputs.operator("node.select_specific_connected", text=n.name).node_name = n.name
        else:
            col_outputs.label(text="No output nodes")

        layout.separator()
        layout.prop(settings, "auto_center")

class NODE_OT_show_node_navigator(Operator):
    bl_idname = "node.show_node_navigator"
    bl_label = "Show Node Navigator"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not context.space_data.edit_tree.nodes.active:
            self.report({'WARNING'}, "No active node selected")
            return {'CANCELLED'}

        bpy.ops.wm.call_panel(name="NODE_MT_node_navigator_popup", keep_open=False)
        return {'FINISHED'}

class NodeNavigatorSettings(bpy.types.PropertyGroup):
    auto_center: BoolProperty(
        name="Auto-center view",
        description="Automatically center the view on selected node",
        default=True
    )

def register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

        kmi_popup = km.keymap_items.new("node.show_node_navigator", 'UP_ARROW', 'PRESS', alt=True)
        addon_keymaps.append((km, kmi_popup))

        for key, dir in [('LEFT_ARROW', 'LEFT'), ('RIGHT_ARROW', 'RIGHT')]:
            kmi = km.keymap_items.new("node.move_connected", key, 'PRESS', alt=True)
            kmi.properties.direction = dir
            addon_keymaps.append((km, kmi))

        kmi_mouse_l = km.keymap_items.new("node.move_connected_mouse", 'LEFTMOUSE', 'PRESS', alt=True)
        kmi_mouse_l.properties.direction = 'LEFT'
        addon_keymaps.append((km, kmi_mouse_l))

        kmi_mouse_r = km.keymap_items.new("node.move_connected_mouse", 'RIGHTMOUSE', 'PRESS', alt=True)
        kmi_mouse_r.properties.direction = 'RIGHT'
        addon_keymaps.append((km, kmi_mouse_r))

        kmi_mouse_m = km.keymap_items.new("node.show_node_navigator_mouse", 'MIDDLEMOUSE', 'PRESS', alt=True)
        addon_keymaps.append((km, kmi_mouse_m))

def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

def register():
    bpy.utils.register_class(NodeNavigatorSettings)
    bpy.types.Scene.node_navigator_settings = bpy.props.PointerProperty(type=NodeNavigatorSettings)

    bpy.utils.register_class(NODE_OT_move_connected)
    bpy.utils.register_class(NODE_OT_move_connected_mouse)
    bpy.utils.register_class(NODE_OT_select_specific_connected)
    bpy.utils.register_class(NODE_MT_node_navigator_popup)
    bpy.utils.register_class(NODE_OT_show_node_navigator)
    bpy.utils.register_class(NODE_OT_show_node_navigator_mouse)
    register_keymap()
    bpy.app.handlers.load_post.append(lambda _: register_keymap())

def unregister():
    unregister_keymap()
    bpy.utils.unregister_class(NODE_OT_show_node_navigator_mouse)
    bpy.utils.unregister_class(NODE_OT_show_node_navigator)
    bpy.utils.unregister_class(NODE_MT_node_navigator_popup)
    bpy.utils.unregister_class(NODE_OT_select_specific_connected)
    bpy.utils.unregister_class(NODE_OT_move_connected_mouse)
    bpy.utils.unregister_class(NODE_OT_move_connected)
    bpy.utils.unregister_class(NodeNavigatorSettings)
    del bpy.types.Scene.node_navigator_settings

if __name__ == "__main__":
    register()
