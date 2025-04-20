import customtkinter as ctk


def configure_theme():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def get_neobrutalist_styles():
    return {
        "font_title": ("Helvetica", 24, "bold"),
        "font_label": ("Helvetica", 14, "bold"),
        "font_button": ("Helvetica", 12, "bold"),
        "bg_color": "#F5F5F5",  # Light gray
        "fg_color": "#FFFFFF",  # White
        "accent_color": "#1E90FF",  # Bright blue
        "text_color": "#333333",  # Dark gray
        "border_color": "#000000",  # Black for neobrutalist contrast
        "highlight_color": "#B0E0E6",  # Light blue for selected option
        "cancel_button_color": "#FF4500",  # Orange-red for cancel button
        "cancel_button_hover": "#CC3700",  # Darker orange-red
        "switch_color": "#1E90FF",  # Bright blue for switch
        "switch_hover_color": "#4682B4",  # Darker blue for switch hover
    }
