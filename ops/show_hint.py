import bpy
import textwrap
from bpy.props import StringProperty
from bpy.types import Operator
from ..hints.loader import HINTS

# Constants
MAX_LINE_LENGTH = 80  # Maximum characters per line before wrapping
POPUP_WIDTH = 500     # Width of the popup dialog


class MRFL_OT_show_hint(Operator):
    """Show a popup hint with custom text"""
    bl_idname = "metareforge_lite.show_hint"
    bl_label = "Show Hint"
    bl_description = "Display a popup window with a hint"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    # Operator properties
    hint_name: StringProperty(
        name="Hint Name",
        description="Name of the hint to display in the popup",
        default=""
    )

    hint_title: StringProperty(
        name="Hint Title",
        description="Title to display in the hint popup",
        default="Info"
    )
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        # Get hint text and prepare for display
        raw_hint_text = HINTS.get(self.hint_name, 'ERROR! The hint is not loaded!')
        self.processed_lines = self._process_text(raw_hint_text)
        
        # Show the popup dialog
        return context.window_manager.invoke_props_dialog(
            self, 
            width=POPUP_WIDTH, 
            title=self.hint_title
        )
    
    def _process_text(self, text):
        """Process text by splitting newlines and wrapping long lines"""
        if not text:
            return ["No content available"]
        
        processed_lines = []
        
        # First split by explicit newlines (both \n and \\n)
        lines = text.replace('\\n', '\n').split('\n')
        
        for line in lines:
            if not line.strip():
                # Empty line - add separator
                processed_lines.append("")
            elif len(line) <= MAX_LINE_LENGTH:
                # Line is short enough, add as-is
                processed_lines.append(line)
            else:
                # Line is too long, wrap it
                wrapped_lines = textwrap.wrap(
                    line,
                    width=MAX_LINE_LENGTH,
                    break_long_words=False,
                    break_on_hyphens=True,
                    expand_tabs=False
                )
                processed_lines.extend(wrapped_lines)
        
        return processed_lines
    
    def draw(self, context):
        layout = self.layout
        
        # Check if we have processed lines
        if not hasattr(self, 'processed_lines') or not self.processed_lines:
            layout.label(text="No content to display", icon='ERROR')
            return
        
        # Create a column for better text layout
        col = layout.column(align=True)
        
        # Display each processed line
        for line in self.processed_lines:
            if line == "":
                # Empty line - add separator
                col.separator()
            else:
                # Regular text line
                col.label(text=line)
    
    @classmethod
    def poll(cls, context):
        """Optional: Add conditions when this operator can run"""
        return True


# Utility function to call the operator easily
def show_hint(hint_name, title="Info"):
    """Convenience function to show a hint popup"""
    if hint_name not in HINTS:
        print(f"Warning: Hint '{hint_name}' not found in HINTS")
    
    bpy.ops.metareforge_lite.show_hint(
        'INVOKE_DEFAULT',
        hint_name=hint_name,
        hint_title=title
    )


# Registration
classes = (
    MRFL_OT_show_hint,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)