bl_info = {
    "name": "Node Navigator",
    "author": "ChatGPT and duhazzz",
    "version": (1, 9),
    "blender": (3, 0, 0),
    "location": "Node Editor > N Panel > Node Navigator",
    "description": "Navigate between nodes with hotkeys and popup panel",
    "category": "Node",
}

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import BoolProperty, StringProperty, PointerProperty, EnumProperty

# Глобальная переменная для хранения keymap
addon_keymaps = []

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
    bl_options = {'REGISTER'}

    direction: EnumProperty(
        items=[("LEFT", "Previous", ""),
               ("RIGHT", "Next", "")],
        default="RIGHT"
    )

    def execute(self, context):
        space = context.space_data
        if space.type != 'NODE_EDITOR':
            return {'CANCELLED'}

        tree = space.edit_tree
        active_node = tree.nodes.active if tree else None

        if not active_node:
            return {'CANCELLED'}

        connected = get_connected_nodes(active_node, 
                                     "PREV" if self.direction == "LEFT" else "NEXT")

        if connected:
            for node in tree.nodes:
                node.select = False
            connected[0].select = True
            tree.nodes.active = connected[0]
            
            if context.scene.node_navigator_settings.auto_center:
                bpy.ops.node.view_selected()

        return {'FINISHED'}

class NODE_OT_select_specific_connected(Operator):
    bl_idname = "node.select_specific_connected"
    bl_label = "Select Connected Node"
    bl_options = {'REGISTER'}

    node_name: StringProperty()

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

class NODE_MT_node_navigator_popup(Panel):
    bl_idname = "NODE_MT_node_navigator_popup"
    bl_label = "Node Navigator"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        node = context.space_data.edit_tree.nodes.active

        if not node:
            layout.label(text="No active node", icon='ERROR')
            return

        row = layout.row(align=True)
        row.operator("node.move_connected", text="", icon='TRIA_LEFT').direction = 'LEFT'
        row.operator("node.move_connected", text="", icon='TRIA_RIGHT').direction = 'RIGHT'
        
        layout.separator()
        layout.label(text=f"Active: {node.name}", icon='NODE')
        layout.separator()

        next_nodes = get_connected_nodes(node, "NEXT")
        prev_nodes = get_connected_nodes(node, "PREV")

        row = layout.row()
        if prev_nodes:
            col = row.column()
            col.label(text="Inputs:")
            for n in prev_nodes:
                col.operator("node.select_specific_connected", text=n.name).node_name = n.name
        else:
            row.label(text="No inputs")

        if next_nodes:
            col = row.column()
            col.label(text="Outputs:")
            for n in next_nodes:
                col.operator("node.select_specific_connected", text=n.name).node_name = n.name
        else:
            row.label(text="No outputs")

class NODE_OT_show_node_navigator(Operator):
    bl_idname = "node.show_node_navigator"
    bl_label = "Show Node Navigator"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if context.space_data.edit_tree.nodes.active:
            bpy.ops.wm.call_panel(name="NODE_MT_node_navigator_popup", keep_open=False)
            return {'FINISHED'}
        return {'CANCELLED'}

class NODE_PT_navigator_panel(Panel):
    bl_label = "Node Navigator"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node Navigator"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.node_navigator_settings
        layout.prop(settings, "auto_center")
        layout.separator()
        layout.operator("node.show_node_navigator", icon='NODE')

class NodeNavigatorSettings(PropertyGroup):
    auto_center: BoolProperty(
        name="Auto-center view",
        description="Automatically center the view on selected node",
        default=True
    )

classes = (
    NodeNavigatorSettings,
    NODE_OT_move_connected,
    NODE_OT_select_specific_connected,
    NODE_MT_node_navigator_popup,
    NODE_OT_show_node_navigator,
    NODE_PT_navigator_panel,
)

def register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        
        # Назначение горячих клавиш
        kmi_prev = km.keymap_items.new("node.move_connected", 'LEFT_ARROW', 'PRESS', alt=True)
        kmi_prev.properties.direction = 'LEFT'
        
        kmi_next = km.keymap_items.new("node.move_connected", 'RIGHT_ARROW', 'PRESS', alt=True)
        kmi_next.properties.direction = 'RIGHT'
        
        kmi_show = km.keymap_items.new("node.show_node_navigator", 'UP_ARROW', 'PRESS', alt=True)
        
        addon_keymaps.append((km, kmi_prev))
        addon_keymaps.append((km, kmi_next))
        addon_keymaps.append((km, kmi_show))

def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.node_navigator_settings = PointerProperty(type=NodeNavigatorSettings)
    register_keymap()

def unregister():
    unregister_keymap()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.node_navigator_settings

if __name__ == "__main__":
    register()
