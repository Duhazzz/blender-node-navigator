bl_info = {
    "name": "Node Navigator",
    "author": "ChatGPT and duhazzz",
    "version": (1, 8),
    "blender": (3, 0, 0),
    "location": "Node Editor > N Panel > Node Navigator",
    "description": (
        "Navigate between connected nodes using popup panel.\n"
        "Popup panel allows fast selection and auto-centering of view on selected node.\n"
        "Works without hotkeys, accessed via a button in the N panel."
    ),
    "category": "Node",
}

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import BoolProperty, StringProperty, PointerProperty, EnumProperty


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
    bl_options = {'REGISTER'}  # Убрали 'UNDO' чтобы отключить запись в историю

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


class NODE_OT_select_specific_connected(Operator):
    bl_idname = "node.select_specific_connected"
    bl_label = "Select Connected Node"
    bl_options = {'REGISTER'}  # Также убрали 'UNDO' для этого оператора

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

        if not node:
            layout.label(text="No active node", icon='ERROR')
            return

        # Добавляем кнопки навигации
        row = layout.row(align=True)
        row.operator("node.move_connected", text="Previous Node", icon='TRIA_LEFT').direction = 'LEFT'
        row.operator("node.move_connected", text="Next Node", icon='TRIA_RIGHT').direction = 'RIGHT'
        
        layout.separator()
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


class NODE_OT_show_node_navigator(Operator):
    bl_idname = "node.show_node_navigator"
    bl_label = "Show Node Navigator"
    bl_options = {'REGISTER'}  # Убрали 'UNDO'

    def execute(self, context):
        if not context.space_data.edit_tree.nodes.active:
            self.report({'WARNING'}, "No active node selected")
            return {'CANCELLED'}

        bpy.ops.wm.call_panel(name="NODE_MT_node_navigator_popup", keep_open=False)
        return {'FINISHED'}


class NODE_PT_navigator_panel(Panel):
    bl_label = "Node Navigator"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node Navigator"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.node_navigator_settings
        
        # Настройка автовыравнивания в N-панели
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


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.node_navigator_settings = PointerProperty(type=NodeNavigatorSettings)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.node_navigator_settings


if __name__ == "__main__":
    register()
