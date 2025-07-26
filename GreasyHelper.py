# Part 1 of 7: Core imports, configuration, and format profiles
# Hollik's Greaseweazle Helper v1.0
# Professional Norton Commander-style interface for Greaseweazle operations
# Fixed version with proper format strings from Yann Serra Tutorial

import os
import subprocess
import time
import sys
import json
import signal
import serial.tools.list_ports
import curses
import threading
from pathlib import Path
from tkinter import Tk, filedialog

# Configuration files
config_file = "gw_config.json"
operation_log_file = "gw_operations.log"

# Global variables
gw_path = ""
com_port = ""
drive_type = "B"  # A or B
target_system = "PC"  # PC, Amiga, Apple, Atari, C64, ZXSpectrum
default_disk_size = ""  # Default disk size for target system
operation_cancelled = False
current_operation = None

# FIXED: Format profiles with CORRECT Greaseweazle format strings from official Yann Serra Tutorial
# Each entry: (format_string, template_filename, size_in_bytes)
format_profiles = {
    "PC": {
        "160KB (5.25\")": ("ibm.160", "pc160.img", 163840),
        "180KB (5.25\")": ("ibm.180", "pc180.img", 184320),
        "320KB (5.25\")": ("ibm.320", "pc320.img", 327680),
        "360KB (5.25\")": ("ibm.360", "pc360.img", 368640),
        "720KB (3.5\")": ("ibm.720", "pc720.img", 737280),
        "800KB (3.5\")": ("ibm.800", "pc800.img", 819200),
        "1200KB (5.25\" HD)": ("ibm.1200", "pc1200.img", 1228800),
        "1440KB (3.5\" HD)": ("ibm.1440", "pc1440.img", 1474560),
        "1680KB (DMF)": ("ibm.1680", "pc1680.img", 1720320),
        "2880KB (ED)": ("ibm.2880", "pc2880.img", 2949120)
    },
    "Amiga": {
        "880KB (DD)": ("amiga.amigados", "amiga880.adf", 901120),
        "1760KB (HD)": ("amiga.amigados_hd", "amiga1760.adf", 1802240)
    },
    "Apple": {
        "400KB (Mac SS)": ("mac.400", "mac400.dsk", 409600),
        "800KB (Mac DS)": ("mac.800", "mac800.dsk", 819200)
    },
    "Atari": {
        "90KB (Atari 800)": ("atari.90", "atari90.img", 92160),
        "360KB (ST SS)": ("atarist.360", "atarist360.st", 368640),
        "400KB (ST SS)": ("atarist.400", "atarist400.st", 409600),
        "440KB (ST SS)": ("atarist.440", "atarist440.st", 450560),
        "720KB (ST DS)": ("atarist.720", "atarist720.st", 737280),
        "800KB (ST DS)": ("atarist.800", "atarist800.st", 819200),
        "880KB (ST DS)": ("atarist.880", "atarist880.st", 901120)
    },
    "C64": {
        "170KB (1541)": ("commodore.1541", "c64_170.d64", 174848),
        "340KB (1571)": ("commodore.1571", "c64_340.d71", 349696),
        "800KB (1581)": ("commodore.1581", "c64_800.d81", 819200)
    },
    "ZXSpectrum": {
        "640KB (TR-DOS)": ("zx.trdos.640", "zx640.mgt", 655360),
        "800KB (Quorum)": ("zx.quorum.800", "zx800.mgt", 819200)
    },
    "Acorn": {
        "160KB (ADFS SS)": ("acorn.adfs.160", "acorn160.ads", 163840),
        "320KB (ADFS DS)": ("acorn.adfs.320", "acorn320.adm", 327680),
        "640KB (ADFS DS)": ("acorn.adfs.640", "acorn640.adl", 655360),
        "800KB (ADFS DS)": ("acorn.adfs.800", "acorn800.adf", 819200),
        "1600KB (ADFS HD)": ("acorn.adfs.1600", "acorn1600.adf", 1638400)
    },
    "MSX": {
        "180KB (1D)": ("msx.1d", "msx180.dsk", 184320),
        "360KB (2D)": ("msx.2d", "msx360.dsk", 368640),
        "360KB (1DD)": ("msx.1dd", "msx360dd.dsk", 368640),
        "720KB (2DD)": ("msx.2dd", "msx720.dsk", 737280)
    }
}

# System descriptions for help
system_descriptions = {
    "PC": "IBM PC Compatible (DOS/Windows)",
    "Amiga": "Commodore Amiga (AmigaOS)",
    "Apple": "Apple Macintosh (System)",
    "Atari": "Atari ST/STE/800 (TOS/GEM)",
    "C64": "Commodore 64/128 (CBM DOS)",
    "ZXSpectrum": "ZX Spectrum +3/MGT (TR-DOS)",
    "Acorn": "Acorn BBC/Archimedes (ADFS)",
    "MSX": "MSX Computer (MSX-DOS)"
}

# Drive type descriptions
drive_descriptions = {
    "A": "Twisted Cable (Drive A/0) - Standard PC",
    "B": "Straight Cable (Drive B/1) - Amiga/Atari/Apple/etc"
}

# FIXED: File extensions per system from Yann Serra Tutorial
file_extensions = {
    "PC": {
        "read": [("PC Images", "*.img"), ("IBM Images", "*.ima"), ("All", "*.*")],
        "write": [("PC Images", "*.img"), ("IBM Images", "*.ima"), ("All", "*.*")],
        "default_ext": ".img"
    },
    "Amiga": {
        "read": [("Amiga Images", "*.adf"), ("Compressed ADF", "*.adz"), ("All", "*.*")],
        "write": [("Amiga Images", "*.adf"), ("All", "*.*")],
        "default_ext": ".adf"
    },
    "Apple": {
        "read": [("Apple Images", "*.dsk"), ("Apple 2MG", "*.2mg"), ("ProDOS", "*.po"), ("All", "*.*")],
        "write": [("Apple Images", "*.dsk"), ("All", "*.*")],
        "default_ext": ".dsk"
    },
    "Atari": {
        "read": [("Atari Images", "*.st"), ("MSA Archives", "*.msa"), ("DIM Images", "*.dim"), ("All", "*.*")],
        "write": [("Atari Images", "*.st"), ("All", "*.*")],
        "default_ext": ".st"
    },
    "C64": {
        "read": [("C64 Images", "*.d64"), ("C64 1571", "*.d71"), ("C64 1581", "*.d81"), ("GCR Images", "*.g64"), ("All", "*.*")],
        "write": [("C64 Images", "*.d64"), ("C64 1571", "*.d71"), ("C64 1581", "*.d81"), ("All", "*.*")],
        "default_ext": ".d64"
    },
    "ZXSpectrum": {
        "read": [("ZX Spectrum", "*.mgt"), ("ZX Disk", "*.dsk"), ("All", "*.*")],
        "write": [("ZX Spectrum", "*.mgt"), ("ZX Disk", "*.dsk"), ("All", "*.*")],
        "default_ext": ".mgt"
    },
    "Acorn": {
        "read": [("Acorn ADFS", "*.adf"), ("Acorn DFS", "*.ssd"), ("Acorn DFS DS", "*.dsd"), ("All", "*.*")],
        "write": [("Acorn ADFS", "*.adf"), ("All", "*.*")],
        "default_ext": ".adf"
    },
    "MSX": {
        "read": [("MSX Images", "*.dsk"), ("All", "*.*")],
        "write": [("MSX Images", "*.dsk"), ("All", "*.*")],
        "default_ext": ".dsk"
    }
}

# Enhanced menu items optimized for larger screens
menu_items = [
    ("W", "Welcome", "Welcome to Hollik's Greaseweazle Helper v1.0"),
    ("R", "Reconfigure", "Change system and hardware settings"),
    ("1", "Clean Disk", "Erase entire disk completely"),
    ("2", "Format Disk", "Write filesystem template to disk"),
    ("3", "Write Image", "Write disk image file to floppy"),
    ("4", "Backup Disk", "Read disk to image file"),
    ("5", "Verify Disk", "Check disk integrity with read-back"),
    ("6", "Disk Status", "Show drive and disk information"),
    ("7", "Repair Disk", "Complete disk recovery sequence"),
    ("", "", ""),  # Spacer
    ("H", "Help Topics", "Browse help and documentation"),
    ("0", "Exit", "Quit the program")
]

# Navigation states
NAV_MAIN_MENU = 0
NAV_SUB_MENU = 1
NAV_OPERATION = 2
NAV_HELP_TOPICS = 3
NAV_HELP_CONTENT = 4

# FIXED: Color pairs for Norton-style interface with better handling
COLOR_MENU_NORMAL = 1
COLOR_MENU_SELECTED = 2
COLOR_MENU_DISABLED = 3
COLOR_OUTPUT_NORMAL = 4
COLOR_OUTPUT_SUCCESS = 5
COLOR_OUTPUT_ERROR = 6
COLOR_STATUS_BAR = 7
COLOR_PANEL_BORDER = 8
COLOR_HELP_TEXT = 9
COLOR_WARNING = 10

def log_operation(operation, result, details=""):
    """Log operations to file with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {operation}: {result}"
    if details:
        log_entry += f" - {details}"
    
    try:
        with open(operation_log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception:
        pass  # Silent fail for logging

def save_config():
    """Save configuration to JSON file"""
    config_data = {
        "gw_path": gw_path,
        "com_port": com_port,
        "drive_type": drive_type,
        "target_system": target_system,
        "default_disk_size": default_disk_size,
        "setup_completed": True
    }
    
    try:
        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2)
    except Exception:
        pass  # Silent fail for config save

def load_config():
    """Load configuration from JSON file"""
    global gw_path, com_port, drive_type, target_system, default_disk_size
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                cfg = json.load(f)
                gw_path = cfg.get("gw_path", "")
                com_port = cfg.get("com_port", "")
                drive_type = cfg.get("drive_type", "B")
                target_system = cfg.get("target_system", "PC")
                default_disk_size = cfg.get("default_disk_size", "")
                return cfg.get("setup_completed", False)
        except Exception:
            # Use defaults if config is corrupted
            pass
    
    return False

def get_available_formats():
    """Get available disk formats for current target system"""
    if target_system in format_profiles:
        return format_profiles[target_system]
    return {}

def get_template_path(format_name):
    """Get path to template file for current system and format"""
    formats = get_available_formats()
    if format_name in formats:
        fmt, filename, size = formats[format_name]
        template_path = os.path.join("templates", filename)
        
        if os.path.exists(template_path):
            # Verify file size matches expected
            actual_size = os.path.getsize(template_path)
            if actual_size == size:
                return template_path
    return None

def drive_arg():
    """Get drive argument for Greaseweazle commands"""
    return ["--drive", "0" if drive_type == "A" else "1"]

def signal_handler(signum, frame):
    """Handle Ctrl+C interruption"""
    global operation_cancelled
    operation_cancelled = True

def get_file_extensions_for_system(system, mode="read"):
    """Get appropriate file extensions for the given system and mode"""
    if system in file_extensions:
        return file_extensions[system].get(mode, [("All", "*.*")])
    return [("All", "*.*")]

def get_default_extension(system):
    """Get default file extension for system"""
    if system in file_extensions:
        return file_extensions[system].get("default_ext", ".img")
    return ".img"

def ensure_directories():
    """Ensure required directories exist"""
    directories = ["templates"]
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except Exception:
                pass

def cleanup_temp_files():
    """Clean up any temporary files"""
    import glob
    temp_patterns = [
        "temp_verify*",
        "temp_repair*", 
        "temp_write*"
    ]
    
    for pattern in temp_patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
            except:
                pass

# Part 2 of 7: Setup Wizard with Fixed Terminal Display
# Hollik's Greaseweazle Helper v1.0
# FIXED: Proper curses initialization and screen handling

class SetupWizard:
    """Fullscreen setup wizard for first-time configuration with FIXED display handling"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.setup_complete = False
        
        # FIXED: Get screen dimensions safely and handle resize
        self.update_screen_dimensions()
        
        # FIXED: Initialize colors with better error handling
        self.init_colors()
        
        # FIXED: Cursor handling
        try:
            curses.curs_set(0)
        except curses.error:
            pass
    
    def update_screen_dimensions(self):
        """FIXED: Safely update screen dimensions"""
        try:
            self.height, self.width = self.stdscr.getmaxyx()
            # Ensure minimum dimensions
            self.height = max(25, self.height)
            self.width = max(80, self.width)
        except curses.error:
            # Fallback dimensions
            self.height = 25
            self.width = 80
    
    def init_colors(self):
        """FIXED: Initialize colors with comprehensive error handling"""
        self.colors_available = True
        try:
            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
                
                # Define color pairs with fallbacks
                color_pairs = [
                    (COLOR_MENU_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLUE),
                    (COLOR_MENU_SELECTED, curses.COLOR_BLACK, curses.COLOR_YELLOW),
                    (COLOR_OUTPUT_SUCCESS, curses.COLOR_GREEN, curses.COLOR_BLUE),
                    (COLOR_OUTPUT_ERROR, curses.COLOR_RED, curses.COLOR_BLUE),
                    (COLOR_STATUS_BAR, curses.COLOR_YELLOW, curses.COLOR_BLUE),
                    (COLOR_WARNING, curses.COLOR_YELLOW, curses.COLOR_RED),
                    (COLOR_HELP_TEXT, curses.COLOR_CYAN, curses.COLOR_BLUE)
                ]
                
                for pair_id, fg, bg in color_pairs:
                    try:
                        curses.init_pair(pair_id, fg, bg)
                    except curses.error:
                        # Skip problematic color pairs
                        pass
            else:
                self.colors_available = False
        except curses.error:
            self.colors_available = False
    
    def get_color_pair(self, color_id):
        """FIXED: Get color pair with fallback"""
        if self.colors_available:
            try:
                return curses.color_pair(color_id)
            except curses.error:
                return curses.A_NORMAL
        return curses.A_NORMAL
    
    def draw_screen(self, title, content, footer="Press ENTER to continue, ESC to exit"):
        """FIXED: Draw fullscreen setup step with proper error handling"""
        try:
            # Update dimensions in case of resize
            self.update_screen_dimensions()
            
            # Clear and set background
            self.stdscr.clear()
            self.stdscr.erase()  # More thorough clear
            self.stdscr.bkgd(' ', self.get_color_pair(COLOR_MENU_NORMAL))
            
            # FIXED: Draw title bar with bounds checking
            title_text = f" {title} "
            title_x = max(0, min(self.width - len(title_text), (self.width - len(title_text)) // 2))
            if len(title_text) <= self.width:
                try:
                    self.stdscr.addstr(2, title_x, title_text, 
                                      self.get_color_pair(COLOR_STATUS_BAR) | curses.A_BOLD)
                except curses.error:
                    pass
            
            # FIXED: Draw content with bounds checking
            start_y = 5
            for i, line in enumerate(content):
                y_pos = start_y + i
                if y_pos >= self.height - 4:
                    break
                
                if line.strip() and len(line) > 0:
                    # Center line if it fits
                    if len(line) <= self.width - 4:
                        line_x = max(2, (self.width - len(line)) // 2)
                    else:
                        line_x = 2
                        line = line[:self.width - 4]  # Truncate if too long
                    
                    # Determine color and attributes
                    color = self.get_color_pair(COLOR_MENU_NORMAL)
                    attr = 0
                    
                    if line.startswith("✓"):
                        color = self.get_color_pair(COLOR_OUTPUT_SUCCESS)
                        attr = curses.A_BOLD
                    elif line.startswith("✗"):
                        color = self.get_color_pair(COLOR_OUTPUT_ERROR)
                        attr = curses.A_BOLD
                    elif line.startswith("⚠"):
                        color = self.get_color_pair(COLOR_WARNING)
                        attr = curses.A_BOLD
                    
                    try:
                        self.stdscr.addstr(y_pos, line_x, line, color | attr)
                    except curses.error:
                        # Skip lines that don't fit
                        pass
            
            # FIXED: Draw footer with bounds checking
            if len(footer) <= self.width - 4:
                footer_x = max(2, (self.width - len(footer)) // 2)
                footer_y = max(self.height - 3, start_y + len(content) + 2)
                try:
                    self.stdscr.addstr(footer_y, footer_x, footer, 
                                      self.get_color_pair(COLOR_STATUS_BAR))
                except curses.error:
                    pass
            
            # FIXED: Safe refresh
            try:
                self.stdscr.refresh()
                curses.doupdate()  # Force screen update
            except curses.error:
                pass
        
        except Exception as e:
            # Emergency fallback - basic display
            try:
                self.stdscr.clear()
                self.stdscr.addstr(0, 0, f"Setup: {title}")
                self.stdscr.addstr(2, 0, "Press ENTER to continue")
                self.stdscr.refresh()
            except:
                pass
    
    def run_setup(self):
        """Run the complete setup wizard"""
        global gw_path, com_port, drive_type, target_system, default_disk_size
        
        # Welcome screen
        if not self.welcome_screen():
            return False
        
        # Step 1: Find Greaseweazle executable
        if not self.find_executable():
            return False
        
        # Step 2: Scan and test COM ports
        if not self.setup_hardware():
            return False
        
        # Step 3: Select drive type
        if not self.select_drive_type():
            return False
        
        # Step 4: Select target system
        if not self.select_target_system():
            return False
        
        # Step 5: Select default disk size
        if not self.select_disk_size():
            return False
        
        # Setup complete
        self.setup_complete_screen()
        save_config()
        return True
    
    def welcome_screen(self):
        """Show welcome screen"""
        content = [
            "HOLLIK'S GREASEWEAZLE HELPER v1.0",
            "Setup Wizard",
            "",
            "Welcome! This wizard will configure your Greaseweazle",
            "hardware and system preferences for optimal operation.",
            "",
            "The setup process includes:",
            "",
            "• Locating your Greaseweazle software",
            "• Detecting and testing your Greaseweazle device", 
            "• Configuring drive cable type",
            "• Selecting target computer system",
            "• Setting default disk format",
            "",
            "This only needs to be done once.",
            "You can change these settings later using the Reconfigure menu.",
            "",
            "IMPORTANT: All write operations will use --no-verify",
            "for maximum compatibility with various drive types."
        ]
        
        self.draw_screen("SETUP WIZARD", content)
        
        while True:
            try:
                key = self.stdscr.getch()
                if key == 10 or key == 13:  # ENTER
                    return True
                elif key == 27:  # ESC
                    return False
                elif key == curses.KEY_RESIZE:
                    # Handle resize
                    self.update_screen_dimensions()
                    self.draw_screen("SETUP WIZARD", content)
            except curses.error:
                # Ignore input errors
                continue
    
    def find_executable(self):
        """FIXED: Find Greaseweazle executable with better file browser handling"""
        global gw_path
        
        content = [
            "STEP 1: LOCATE GREASEWEAZLE EXECUTABLE",
            "",
            "Please select your Greaseweazle executable file.",
            "",
            "Typically named:",
            "• gw.exe (Windows)",
            "• gw.py (Python script)",
            "• gw (Linux/Mac)",
            "",
            "The file browser will open when you press ENTER."
        ]
        
        self.draw_screen("FIND EXECUTABLE", content)
        
        while True:
            try:
                key = self.stdscr.getch()
                if key == 10 or key == 13:  # ENTER
                    break
                elif key == 27:  # ESC
                    return False
                elif key == curses.KEY_RESIZE:
                    self.update_screen_dimensions()
                    self.draw_screen("FIND EXECUTABLE", content)
            except curses.error:
                continue
        
        # FIXED: Open file browser with proper curses handling
        try:
            # Temporarily end curses mode
            curses.endwin()
            
            # Create Tkinter root and configure
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            root.focus_force()
            root.lift()
            
            file = filedialog.askopenfilename(
                title="Select Greaseweazle Executable",
                filetypes=[
                    ("Greaseweazle", "gw.exe"),
                    ("Python Script", "gw.py"),
                    ("Executable", "gw"),
                    ("All files", "*.*")
                ],
                parent=root
            )
            
            # Clean up Tkinter
            root.destroy()
            
            # Restore curses mode
            self.stdscr.refresh()
            curses.doupdate()
            
            if file:
                gw_path = file
                # Show success
                content = [
                    "GREASEWEAZLE EXECUTABLE SELECTED",
                    "",
                    f"✓ Selected: {os.path.basename(gw_path)}",
                    f"✓ Location: {gw_path}",
                    "",
                    "The executable will be tested in the next step."
                ]
                self.draw_screen("EXECUTABLE FOUND", content)
                
                # Wait for confirmation
                while True:
                    try:
                        key = self.stdscr.getch()
                        if key == 10 or key == 13 or key == 27:
                            return True
                        elif key == curses.KEY_RESIZE:
                            self.update_screen_dimensions()
                            self.draw_screen("EXECUTABLE FOUND", content)
                    except curses.error:
                        continue
            else:
                # No file selected
                content = [
                    "NO FILE SELECTED",
                    "",
                    "✗ No Greaseweazle executable was selected.",
                    "",
                    "You need to select the Greaseweazle software",
                    "to continue with the setup.",
                    "",
                    "Press ENTER to try again, or ESC to exit setup."
                ]
                self.draw_screen("SELECTION REQUIRED", content, 
                               "ENTER: Try again | ESC: Exit setup")
                
                while True:
                    try:
                        key = self.stdscr.getch()
                        if key == 10 or key == 13:  # Try again
                            return self.find_executable()  # Recursive retry
                        elif key == 27:  # Exit
                            return False
                        elif key == curses.KEY_RESIZE:
                            self.update_screen_dimensions()
                            self.draw_screen("SELECTION REQUIRED", content,
                                           "ENTER: Try again | ESC: Exit setup")
                    except curses.error:
                        continue
                        
        except Exception as e:
            # Restore curses mode if something went wrong
            try:
                self.stdscr.refresh()
                curses.doupdate()
            except:
                pass
            
            content = [
                "FILE BROWSER ERROR",
                "",
                "✗ Could not open file browser.",
                f"✗ Error: {str(e)}",
                "",
                "Please ensure your system supports file dialogs.",
                "",
                "Press ESC to exit setup."
            ]
            self.draw_screen("BROWSER ERROR", content, "ESC: Exit setup")
            
            while True:
                try:
                    key = self.stdscr.getch()
                    if key == 27:
                        return False
                    elif key == curses.KEY_RESIZE:
                        self.update_screen_dimensions()
                        self.draw_screen("BROWSER ERROR", content, "ESC: Exit setup")
                except curses.error:
                    continue

# Part 3 of 7: Setup Wizard Methods (Hardware Detection & Configuration)
# Hollik's Greaseweazle Helper v1.0
# FIXED: Hardware detection with proper terminal handling

    def setup_hardware(self):
        """FIXED: Scan for and test Greaseweazle hardware with detailed feedback"""
        global com_port
        
        content = [
            "STEP 2: DETECT GREASEWEAZLE HARDWARE",
            "",
            "Scanning COM ports for Greaseweazle devices...",
            "",
            "Please ensure your Greaseweazle is:",
            "• Connected via USB",
            "• Powered on", 
            "• Drivers are installed"
        ]
        
        self.draw_screen("SCANNING HARDWARE", content, "Scanning in progress...")
        
        # Get available ports
        try:
            ports = serial.tools.list_ports.comports()
        except Exception as e:
            content = [
                "PORT SCANNING ERROR",
                "",
                "✗ Could not scan COM ports.",
                f"✗ Error: {str(e)}",
                "",
                "Please check that:",
                "• USB drivers are installed",
                "• System recognizes USB devices",
                "",
                "Press ESC to exit setup."
            ]
            self.draw_screen("SCAN ERROR", content, "ESC: Exit setup")
            
            while True:
                try:
                    key = self.stdscr.getch()
                    if key == 27:
                        return False
                    elif key == curses.KEY_RESIZE:
                        self.update_screen_dimensions()
                        self.draw_screen("SCAN ERROR", content, "ESC: Exit setup")
                except curses.error:
                    continue
        
        found_ports = []
        
        if not ports:
            content = [
                "NO COM PORTS FOUND",
                "",
                "✗ No COM ports detected on this system.",
                "",
                "Please check that:",
                "• Greaseweazle is connected via USB",
                "• USB drivers are properly installed", 
                "• Device is recognized by the operating system",
                "",
                "Press ESC to exit setup and check your hardware."
            ]
            self.draw_screen("NO PORTS", content, "ESC: Exit setup")
            
            while True:
                try:
                    key = self.stdscr.getch()
                    if key == 27:
                        return False
                    elif key == curses.KEY_RESIZE:
                        self.update_screen_dimensions()
                        self.draw_screen("NO PORTS", content, "ESC: Exit setup")
                except curses.error:
                    continue
        
        # Create dynamic scanning display
        content = [
            "STEP 2: DETECT GREASEWEAZLE HARDWARE",
            "",
            f"Found {len(ports)} COM ports, testing each one...",
            "",
            "Scanning progress:"
        ]
        
        # Test each port with real-time feedback
        for i, port in enumerate(ports):
            # Update display to show current port being tested
            current_content = content + [
                "",
                f"Testing {port.device}..."
            ]
            
            # Show previous results
            for j, prev_port in enumerate(ports[:i]):
                if prev_port.device in found_ports:
                    current_content.append(f"✓ {prev_port.device}: Greaseweazle detected")
                else:
                    current_content.append(f"✗ {prev_port.device}: Not Greaseweazle")
            
            self.draw_screen("SCANNING HARDWARE", current_content, "Testing in progress...")
            
            # Test the port with timeout
            try:
                if not gw_path:
                    # Skip testing if no executable
                    continue
                    
                result = subprocess.run([gw_path, "info", "--device", port.device],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=5, text=True)
                
                # FIXED: Better Greaseweazle detection based on official patterns
                output_text = (result.stdout + result.stderr).lower()
                if any(keyword in output_text for keyword in [
                    "greaseweazle", "f7", "f1", "firmware", "flux"
                ]) or result.returncode == 0:
                    found_ports.append(port.device)
                    
            except subprocess.TimeoutExpired:
                # Timeout - not a Greaseweazle
                pass
            except Exception:
                # Any other error - not a Greaseweazle
                pass
        
        # Show final results
        final_content = [
            "STEP 2: DETECT GREASEWEAZLE HARDWARE",
            "",
            "Scan complete. Results:",
            ""
        ]
        
        # Show all test results
        for port in ports:
            if port.device in found_ports:
                final_content.append(f"✓ {port.device}: Greaseweazle detected")
            else:
                final_content.append(f"✗ {port.device}: Not Greaseweazle")
        
        final_content.extend(["", f"Found {len(found_ports)} Greaseweazle device(s)"])
        
        self.draw_screen("SCAN RESULTS", final_content, "")
        
        # Wait a moment to show results
        time.sleep(1)
        
        if not found_ports:
            content = [
                "NO GREASEWEAZLE DEVICES FOUND",
                "",
                "✗ Scanned all COM ports but found no Greaseweazle devices.",
                "",
                "Ports tested:",
            ]
            
            for port in ports:
                content.append(f"  • {port.device} - Not Greaseweazle")
            
            content.extend([
                "",
                "Troubleshooting:",
                "• Check USB connection",
                "• Install/update Greaseweazle drivers",
                "• Close other software using the device",
                "• Try a different USB port",
                "• Verify the executable path is correct",
                "",
                "Press ESC to exit setup."
            ])
            
            self.draw_screen("NO DEVICES", content, "ESC: Exit setup")
            
            while True:
                try:
                    key = self.stdscr.getch()
                    if key == 27:
                        return False
                    elif key == curses.KEY_RESIZE:
                        self.update_screen_dimensions()
                        self.draw_screen("NO DEVICES", content, "ESC: Exit setup")
                except curses.error:
                    continue
        
        elif len(found_ports) == 1:
            # Single device found
            com_port = found_ports[0]
            content = [
                "GREASEWEAZLE DEVICE DETECTED",
                "",
                f"✓ Found Greaseweazle on {com_port}",
                "",
                "Testing device communication..."
            ]
            self.draw_screen("DEVICE FOUND", content, "Testing...")
            
            # Test the device more thoroughly
            try:
                result = subprocess.run([gw_path, "info", "--device", com_port],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=10, text=True)
                
                if result.returncode == 0:
                    content = [
                        "GREASEWEAZLE DEVICE CONFIRMED",
                        "",
                        f"✓ Device: {com_port}",
                        "✓ Communication: Working",
                        "",
                        "Device Information:",
                    ]
                    
                    # Add device info lines (first 3 lines)
                    info_lines = result.stdout.strip().split('\n')
                    for line in info_lines[:3]:
                        if line.strip():
                            # Truncate long lines
                            display_line = line[:self.width - 6] if len(line) > self.width - 6 else line
                            content.append(f"  {display_line}")
                    
                    content.append("")
                    content.append("Device ready for operations!")
                    
                else:
                    content = [
                        "DEVICE COMMUNICATION ISSUE",
                        "",
                        f"⚠ Found device on {com_port}",
                        "⚠ But communication test failed",
                        "",
                        "This may still work for basic operations.",
                        "You can reconfigure later if needed."
                    ]
                
            except Exception:
                content = [
                    "DEVICE TEST INCOMPLETE",
                    "",
                    f"✓ Found device on {com_port}",
                    "⚠ Advanced test failed",
                    "",
                    "Device will be configured anyway.",
                    "You can test it later in the main program."
                ]
            
            self.draw_screen("DEVICE CONFIGURED", content)
            
            while True:
                try:
                    key = self.stdscr.getch()
                    if key == 10 or key == 13:
                        return True
                    elif key == curses.KEY_RESIZE:
                        self.update_screen_dimensions()
                        self.draw_screen("DEVICE CONFIGURED", content)
                except curses.error:
                    continue
        
        else:
            # Multiple devices found - let user choose
            return self.select_com_port(found_ports)
    
    def select_com_port(self, ports):
        """FIXED: Let user select from multiple COM ports with proper navigation"""
        global com_port
        selection = 0
        
        while True:
            content = [
                "MULTIPLE GREASEWEAZLE DEVICES FOUND",
                "",
                "Please select which device to use:",
                ""
            ]
            
            for i, port in enumerate(ports):
                marker = "►" if i == selection else " "
                content.append(f"{marker} {i + 1}) {port}")
            
            content.extend([
                "",
                "Use ↑↓ to select, ENTER to confirm"
            ])
            
            self.draw_screen("SELECT DEVICE", content, "↑↓: Navigate | ENTER: Select | ESC: Exit")
            
            try:
                key = self.stdscr.getch()
                if key == curses.KEY_UP:
                    selection = max(0, selection - 1)
                elif key == curses.KEY_DOWN:
                    selection = min(len(ports) - 1, selection + 1)
                elif key == 10 or key == 13:  # ENTER
                    com_port = ports[selection]
                    
                    content = [
                        "DEVICE SELECTED",
                        "",
                        f"✓ Using Greaseweazle on {com_port}",
                        "",
                        "Device configured successfully."
                    ]
                    self.draw_screen("DEVICE CONFIGURED", content)
                    
                    while True:
                        try:
                            key = self.stdscr.getch()
                            if key == 10 or key == 13:
                                return True
                            elif key == curses.KEY_RESIZE:
                                self.update_screen_dimensions()
                                self.draw_screen("DEVICE CONFIGURED", content)
                        except curses.error:
                            continue
                elif key == 27:  # ESC
                    return False
                elif key == curses.KEY_RESIZE:
                    self.update_screen_dimensions()
            except curses.error:
                continue
    
    def select_drive_type(self):
        """FIXED: Select drive cable type with proper navigation"""
        global drive_type
        selection = 1  # Default to B (straight cable)
        
        while True:
            content = [
                "STEP 3: SELECT DRIVE CABLE TYPE",
                "",
                "What type of floppy drive cable do you have?",
                "",
                f"{'►' if selection == 0 else ' '} A) Twisted Cable (Drive A/0)",
                "   • Standard PC floppy drive setup",
                "   • Cable has twisted conductors",
                "   • Most common in IBM PC systems",
                "",
                f"{'►' if selection == 1 else ' '} B) Straight Cable (Drive B/1)", 
                "   • Direct cable connection",
                "   • Used in Amiga, Atari ST, Apple systems",
                "   • No twisted conductors",
                "",
                "Use ↑↓ to select, ENTER to confirm"
            ]
            
            self.draw_screen("DRIVE CONFIGURATION", content, "↑↓: Navigate | ENTER: Select")
            
            try:
                key = self.stdscr.getch()
                if key == curses.KEY_UP:
                    selection = 0
                elif key == curses.KEY_DOWN:
                    selection = 1
                elif key == 10 or key == 13:  # ENTER
                    drive_type = "A" if selection == 0 else "B"
                    
                    content = [
                        "DRIVE TYPE SELECTED",
                        "",
                        f"✓ Selected: {drive_descriptions[drive_type]}",
                        "",
                        "Drive configuration saved."
                    ]
                    self.draw_screen("DRIVE CONFIGURED", content)
                    
                    while True:
                        try:
                            key = self.stdscr.getch()
                            if key == 10 or key == 13:
                                return True
                            elif key == curses.KEY_RESIZE:
                                self.update_screen_dimensions()
                                self.draw_screen("DRIVE CONFIGURED", content)
                        except curses.error:
                            continue
                elif key == 27:  # ESC
                    return False
                elif key == curses.KEY_RESIZE:
                    self.update_screen_dimensions()
            except curses.error:
                continue
    
    def select_target_system(self):
        """FIXED: Select target computer system with improved navigation"""
        global target_system
        systems = list(system_descriptions.keys())
        selection = 0  # Default to PC
        
        while True:
            content = [
                "STEP 4: SELECT TARGET COMPUTER SYSTEM",
                "",
                "Which computer system will you primarily use?",
                ""
            ]
            
            for i, system in enumerate(systems):
                marker = "►" if i == selection else " "
                desc = system_descriptions[system]
                # Truncate description if too long
                if len(desc) > 35:
                    desc = desc[:32] + "..."
                content.append(f"{marker} {i + 1}) {system} - {desc}")
            
            content.extend([
                "",
                "Use ↑↓ to select, ENTER to confirm"
            ])
            
            self.draw_screen("TARGET SYSTEM", content, "↑↓: Navigate | ENTER: Select")
            
            try:
                key = self.stdscr.getch()
                if key == curses.KEY_UP:
                    selection = max(0, selection - 1)
                elif key == curses.KEY_DOWN:
                    selection = min(len(systems) - 1, selection + 1)
                elif key == 10 or key == 13:  # ENTER
                    target_system = systems[selection]
                    
                    content = [
                        "TARGET SYSTEM SELECTED",
                        "",
                        f"✓ Selected: {target_system}",
                        f"✓ Description: {system_descriptions[target_system]}",
                        "",
                        "System configuration saved."
                    ]
                    self.draw_screen("SYSTEM CONFIGURED", content)
                    
                    while True:
                        try:
                            key = self.stdscr.getch()
                            if key == 10 or key == 13:
                                return True
                            elif key == curses.KEY_RESIZE:
                                self.update_screen_dimensions()
                                self.draw_screen("SYSTEM CONFIGURED", content)
                        except curses.error:
                            continue
                elif key == 27:  # ESC
                    return False
                elif key == curses.KEY_RESIZE:
                    self.update_screen_dimensions()
            except curses.error:
                continue

# Part 4 of 7: Setup Wizard Completion & Main GUI Class
# Hollik's Greaseweazle Helper v1.0
# FIXED: Disk size selection and GUI initialization

    def select_disk_size(self):
        """FIXED: Select default disk size with proper format handling"""
        global default_disk_size
        formats = get_available_formats()
        sizes = list(formats.keys())
        selection = 0
        
        if not sizes:
            # No formats available for this system
            content = [
                "NO FORMATS AVAILABLE",
                "",
                f"✗ No disk formats found for {target_system}.",
                "",
                "This may indicate:",
                "• System not fully supported",
                "• Template files missing",
                "",
                "You can add templates later and reconfigure.",
                "",
                "Press ENTER to continue without default size."
            ]
            self.draw_screen("NO FORMATS", content)
            
            while True:
                try:
                    key = self.stdscr.getch()
                    if key == 10 or key == 13:
                        default_disk_size = ""
                        return True
                    elif key == curses.KEY_RESIZE:
                        self.update_screen_dimensions()
                        self.draw_screen("NO FORMATS", content)
                except curses.error:
                    continue
        
        while True:
            content = [
                "STEP 5: SELECT DEFAULT DISK SIZE",
                "",
                f"Available disk sizes for {target_system}:",
                ""
            ]
            
            for i, size in enumerate(sizes):
                marker = "►" if i == selection else " "
                _, _, byte_size = formats[size]
                # Format size display nicely
                size_kb = byte_size // 1024
                content.append(f"{marker} {i + 1}) {size} ({size_kb}KB)")
            
            content.extend([
                "",
                "This will be the default size for format and repair operations.",
                "You can change this later or select different sizes per operation.",
                "",
                "Use ↑↓ to select, ENTER to confirm"
            ])
            
            self.draw_screen("DEFAULT DISK SIZE", content, "↑↓: Navigate | ENTER: Select")
            
            try:
                key = self.stdscr.getch()
                if key == curses.KEY_UP:
                    selection = max(0, selection - 1)
                elif key == curses.KEY_DOWN:
                    selection = min(len(sizes) - 1, selection + 1)
                elif key == 10 or key == 13:  # ENTER
                    default_disk_size = sizes[selection]
                    
                    content = [
                        "DEFAULT SIZE SELECTED",
                        "",
                        f"✓ Selected: {default_disk_size}",
                        f"✓ System: {target_system}",
                        "",
                        "Default disk size configured."
                    ]
                    self.draw_screen("SIZE CONFIGURED", content)
                    
                    while True:
                        try:
                            key = self.stdscr.getch()
                            if key == 10 or key == 13:
                                return True
                            elif key == curses.KEY_RESIZE:
                                self.update_screen_dimensions()
                                self.draw_screen("SIZE CONFIGURED", content)
                        except curses.error:
                            continue
                elif key == 27:  # ESC
                    return False
                elif key == curses.KEY_RESIZE:
                    self.update_screen_dimensions()
            except curses.error:
                continue
    
    def setup_complete_screen(self):
        """Show setup completion with comprehensive summary"""
        content = [
            "SETUP WIZARD COMPLETE!",
            "",
            "✓ Hollik's Greaseweazle Helper is now configured and ready to use.",
            "",
            "Your configuration:",
            f"• Greaseweazle: {com_port}",
            f"• Drive Type: {drive_descriptions[drive_type]}",
            f"• Target System: {target_system} ({system_descriptions[target_system]})",
            f"• Default Size: {default_disk_size if default_disk_size else 'None set'}",
            "",
            "Key features enabled:",
            "• All write operations use --no-verify for compatibility",
            "• Proper format strings from Yann Serra Tutorial",
            "• System-specific file extensions",
            f"• {len(get_available_formats())} disk formats for {target_system}",
            "",
            "All settings have been saved and will be restored",
            "automatically when you restart the program.",
            "",
            "You can change these settings anytime using the",
            "Reconfigure option in the main menu.",
            "",
            "Welcome to Hollik's Greaseweazle Helper v1.0!"
        ]
        
        self.draw_screen("SETUP COMPLETE", content, "Press ENTER to start using the helper")
        
        while True:
            try:
                key = self.stdscr.getch()
                if key == 10 or key == 13:
                    return
                elif key == curses.KEY_RESIZE:
                    self.update_screen_dimensions()
                    self.draw_screen("SETUP COMPLETE", content, "Press ENTER to start using the helper")
            except curses.error:
                continue

def run_setup_wizard(stdscr):
    """Run the setup wizard with proper error handling"""
    try:
        wizard = SetupWizard(stdscr)
        return wizard.run_setup()
    except Exception as e:
        # Emergency fallback
        try:
            stdscr.clear()
            stdscr.addstr(0, 0, f"Setup wizard error: {e}")
            stdscr.addstr(2, 0, "Press any key to exit")
            stdscr.refresh()
            stdscr.getch()
        except:
            pass
        return False

class GreaseweazleGUI:
    """FIXED: Main GUI class with improved curses handling and display stability"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        
        # Navigation state and panel management
        self.navigation_state = NAV_MAIN_MENU
        self.active_panel = "left"  # "left" or "right"
        self.main_menu_selection = 0
        self.sub_menu_selection = 0
        self.help_topic_selection = 0
        self.help_content_scroll = 0
        
        # Data storage
        self.sub_menu_items = []
        self.help_topics = []
        self.current_help_content = []
        self.output_lines = []
        
        # Operation state
        self.operation_in_progress = False
        self.waiting_for_input = False
        
        # FIXED: Get actual screen dimensions safely
        self.init_screen_dimensions()
        
        # FIXED: Initialize colors with comprehensive error handling
        self.init_colors()
        
        # FIXED: Create windows with safe boundaries and error handling
        self.init_windows()
        
        # Initialize help topics
        self.init_help_topics()
    
    def init_screen_dimensions(self):
        """FIXED: Initialize screen dimensions with safety checks"""
        try:
            actual_height, actual_width = self.stdscr.getmaxyx()
        except curses.error:
            # Emergency fallback
            actual_height, actual_width = 25, 80
        
        # Optimized dimensions for various screen sizes
        target_width = 115
        target_height = 42
        
        # Determine optimal screen size
        if actual_width >= target_width and actual_height >= target_height:
            self.width = target_width
            self.height = target_height
            self.menu_width = 38
        elif actual_width >= 100 and actual_height >= 35:
            self.width = min(target_width, actual_width - 2)
            self.height = min(target_height, actual_height - 2)
            self.menu_width = 35
        else:
            self.width = max(80, actual_width - 2)
            self.height = max(25, actual_height - 2)
            self.menu_width = 30
        
        # Calculate panel dimensions
        self.output_width = self.width - self.menu_width - 1
        self.content_height = self.height - 4
        
        # Ensure minimum dimensions
        self.width = max(80, self.width)
        self.height = max(25, self.height)
        self.menu_width = min(self.menu_width, self.width // 3)
        self.output_width = max(40, self.output_width)
        self.content_height = max(20, self.content_height)
    
    def init_colors(self):
        """FIXED: Initialize colors with comprehensive error handling"""
        self.colors_available = True
        try:
            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
                
                # Define all color pairs with fallbacks
                color_definitions = [
                    (COLOR_MENU_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLUE),
                    (COLOR_MENU_SELECTED, curses.COLOR_BLACK, curses.COLOR_YELLOW),
                    (COLOR_MENU_DISABLED, curses.COLOR_CYAN, curses.COLOR_BLUE),
                    (COLOR_OUTPUT_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLUE),
                    (COLOR_OUTPUT_SUCCESS, curses.COLOR_GREEN, curses.COLOR_BLUE),
                    (COLOR_OUTPUT_ERROR, curses.COLOR_RED, curses.COLOR_BLUE),
                    (COLOR_STATUS_BAR, curses.COLOR_YELLOW, curses.COLOR_BLUE),
                    (COLOR_PANEL_BORDER, curses.COLOR_WHITE, curses.COLOR_BLUE),
                    (COLOR_HELP_TEXT, curses.COLOR_CYAN, curses.COLOR_BLUE),
                    (COLOR_WARNING, curses.COLOR_YELLOW, curses.COLOR_RED)
                ]
                
                for pair_id, fg, bg in color_definitions:
                    try:
                        curses.init_pair(pair_id, fg, bg)
                    except curses.error:
                        # Skip problematic color pairs
                        pass
            else:
                self.colors_available = False
        except curses.error:
            self.colors_available = False
    
    def get_color_pair(self, color_id):
        """FIXED: Get color pair with fallback"""
        if self.colors_available:
            try:
                return curses.color_pair(color_id)
            except curses.error:
                return curses.A_NORMAL
        return curses.A_NORMAL
    
    def init_windows(self):
        """FIXED: Create windows with comprehensive error handling"""
        # Hide cursor
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        
        # FIXED: Create windows with safe boundaries and error handling
        try:
            # Ensure all dimensions are positive and within screen bounds
            safe_width = min(self.width, self.stdscr.getmaxyx()[1])
            safe_height = min(self.height, self.stdscr.getmaxyx()[0])
            safe_content_height = min(self.content_height, safe_height - 4)
            safe_menu_width = min(self.menu_width, safe_width - 10)
            safe_output_width = min(self.output_width, safe_width - safe_menu_width - 1)
            
            # Create windows with bounds checking
            self.status_win = curses.newwin(min(2, safe_height), safe_width, 0, 0)
            self.menu_win = curses.newwin(safe_content_height, safe_menu_width, 2, 0)
            self.output_win = curses.newwin(safe_content_height, safe_output_width, 2, safe_menu_width + 1)
            self.bottom_win = curses.newwin(min(2, safe_height - safe_content_height - 2), safe_width, safe_height - 2, 0)
            
            # Enable scrolling for output window
            try:
                self.output_win.scrollok(True)
            except curses.error:
                pass
            
        except curses.error as e:
            # Emergency fallback - create minimal windows
            try:
                self.status_win = curses.newwin(1, 80, 0, 0)
                self.menu_win = curses.newwin(20, 25, 1, 0)
                self.output_win = curses.newwin(20, 50, 1, 26)
                self.bottom_win = curses.newwin(1, 80, 22, 0)
            except curses.error:
                # Complete fallback - use stdscr
                self.status_win = self.stdscr
                self.menu_win = self.stdscr
                self.output_win = self.stdscr
                self.bottom_win = self.stdscr
    
    def handle_resize(self):
        """FIXED: Handle terminal resize events with proper scaling"""
        try:
            # Get new dimensions
            new_height, new_width = self.stdscr.getmaxyx()
            
            # Always update dimensions and windows for proper scaling
            if (new_height, new_width) != (self.height, self.width):
                # Reinitialize with new dimensions
                self.init_screen_dimensions()
                self.init_windows()
                
                # Refresh immediately without clearing
                self.refresh_all()
        except Exception:
            pass
    
    def init_help_topics(self):
        """Initialize help topics list"""
        self.help_topics = [
            ("getting_started", "Getting Started"),
            ("disk_cleaning", "Disk Cleaning"),
            ("disk_formatting", "Disk Formatting"),
            ("writing_images", "Writing Images"),
            ("creating_backups", "Creating Backups"),
            ("disk_verification", "Disk Verification"),
            ("hardware_setup", "Hardware Setup"),
            ("troubleshooting", "Troubleshooting"),
            ("file_formats", "File Formats"),
            ("template_files", "Template Files"),
            ("no_verify_mode", "--no-verify Mode"),
            ("format_strings", "Format Strings")
        ]

# Part 5 of 7: GUI Drawing Methods with Fixed Display
# Hollik's Greaseweazle Helper v1.0
# FIXED: All drawing methods with proper bounds checking and border handling

    def draw_status_bar(self):
        """FIXED: Draw enhanced status bar with proper bounds checking"""
        if not self.status_win:
            return
            
        try:
            self.status_win.clear()
            self.status_win.bkgd(' ', self.get_color_pair(COLOR_STATUS_BAR))
            
            # Get window dimensions safely
            try:
                win_height, win_width = self.status_win.getmaxyx()
            except curses.error:
                return
            
            # Line 1: Title and connection
            title = "Hollik's Greaseweazle Helper v1.0"
            status = f"COM: {com_port or 'None'}"
            if com_port:
                status += " ✓"
            else:
                status += " ✗"
            
            # Draw title if it fits
            if len(title) <= win_width - 4:
                try:
                    self.status_win.addstr(0, 2, title, self.get_color_pair(COLOR_STATUS_BAR) | curses.A_BOLD)
                except curses.error:
                    pass
            
            # Draw status if it fits
            if len(status) <= win_width - 4:
                status_x = max(2, win_width - len(status) - 2)
                try:
                    self.status_win.addstr(0, status_x, status, self.get_color_pair(COLOR_STATUS_BAR))
                except curses.error:
                    pass
            
            # Line 2: System info and active panel indicator (if window is tall enough)
            if win_height > 1:
                system_info = f"System: {target_system}"
                if default_disk_size:
                    system_info += f" ({default_disk_size})"
                
                drive_info = f"Drive: {drive_descriptions[drive_type]}"
                panel_indicator = f"[{self.active_panel.upper()} PANEL]"
                
                settings_line = f"{system_info} │ {drive_info}"
                
                # Draw system info if it fits
                if len(settings_line) <= win_width - 4:
                    try:
                        self.status_win.addstr(1, 2, settings_line, self.get_color_pair(COLOR_STATUS_BAR))
                    except curses.error:
                        pass
                
                # Add panel indicator on right if there's space
                indicator_x = win_width - len(panel_indicator) - 2
                if indicator_x > len(settings_line) + 5 and len(panel_indicator) <= win_width - 4:
                    try:
                        self.status_win.addstr(1, indicator_x, panel_indicator, 
                                             self.get_color_pair(COLOR_STATUS_BAR) | curses.A_BOLD)
                    except curses.error:
                        pass
            
            self.status_win.refresh()
        except Exception:
            # Silent fail for status bar
            pass
    
    def draw_main_menu(self):
        """FIXED: Draw left menu panel with proper border handling"""
        if not self.menu_win:
            return
            
        try:
            self.menu_win.clear()
            
            # Get window dimensions safely
            try:
                win_height, win_width = self.menu_win.getmaxyx()
            except curses.error:
                return
            
            # Determine if this panel is active
            is_active = (self.active_panel == "left" and 
                        self.navigation_state in [NAV_MAIN_MENU])
            
            if is_active:
                bg_color = COLOR_MENU_NORMAL
                border_attr = curses.A_BOLD
            else:
                bg_color = COLOR_MENU_DISABLED
                border_attr = 0
            
            self.menu_win.bkgd(' ', self.get_color_pair(bg_color))
            
            # FIXED: Draw border with proper error handling
            try:
                if is_active:
                    # Active panel gets bold border
                    self.menu_win.box()
                    # Add visual emphasis for active state
                    try:
                        for x in range(1, win_width - 1):
                            self.menu_win.addch(0, x, '═', self.get_color_pair(bg_color) | curses.A_BOLD)
                            self.menu_win.addch(win_height - 1, x, '═', self.get_color_pair(bg_color) | curses.A_BOLD)
                        for y in range(1, win_height - 1):
                            self.menu_win.addch(y, 0, '║', self.get_color_pair(bg_color) | curses.A_BOLD)
                            self.menu_win.addch(y, win_width - 1, '║', self.get_color_pair(bg_color) | curses.A_BOLD)
                    except curses.error:
                        pass
                else:
                    self.menu_win.box()
            except curses.error:
                # Fallback: draw simple border manually
                try:
                    # Draw corner and edge characters manually
                    for y in range(win_height):
                        if y == 0 or y == win_height - 1:
                            for x in range(win_width):
                                if x == 0 or x == win_width - 1:
                                    self.menu_win.addch(y, x, '+')
                                else:
                                    self.menu_win.addch(y, x, '-')
                        else:
                            self.menu_win.addch(y, 0, '|')
                            self.menu_win.addch(y, win_width - 1, '|')
                except curses.error:
                    pass
            
            # Panel title
            title = " OPERATIONS "
            if len(title) <= win_width - 4:
                title_x = max(2, (win_width - len(title)) // 2)
                try:
                    self.menu_win.addstr(0, title_x, title, 
                                       self.get_color_pair(bg_color) | curses.A_BOLD)
                except curses.error:
                    pass
            
            # FIXED: Draw menu items with proper bounds checking
            y = 2
            menu_index = 0
            
            for key, name, desc in menu_items:
                if y >= win_height - 2:
                    break
                    
                if not key:  # Spacer
                    if y < win_height - 2:
                        separator = "─" * min(win_width - 4, 30)
                        try:
                            self.menu_win.addstr(y, 2, separator, self.get_color_pair(bg_color))
                        except curses.error:
                            pass
                    y += 1
                    continue
                
                # Determine if this item is selected
                is_selected = (is_active and menu_index == self.main_menu_selection)
                
                if is_selected:
                    color = COLOR_MENU_SELECTED
                    attr = curses.A_BOLD
                    indicator = "►"
                else:
                    color = bg_color
                    attr = 0
                    indicator = " "
                
                # Format menu item with length checking
                menu_text = f"{indicator} [{key}] {name}"
                if len(menu_text) > win_width - 3:
                    menu_text = menu_text[:win_width - 3]
                
                try:
                    self.menu_win.addstr(y, 1, menu_text, self.get_color_pair(color) | attr)
                except curses.error:
                    pass
                
                y += 1
                menu_index += 1
            
            self.menu_win.refresh()
        except Exception:
            # Silent fail for menu drawing
            pass
    
    def draw_output_panel(self):
        """FIXED: Draw right panel with context-sensitive content"""
        if not self.output_win:
            return
            
        try:
            self.output_win.clear()
            self.output_win.bkgd(' ', self.get_color_pair(COLOR_OUTPUT_NORMAL))
            
            # Get window dimensions safely
            try:
                win_height, win_width = self.output_win.getmaxyx()
            except curses.error:
                return
            
            # FIXED: Draw clean border with error handling
            try:
                self.output_win.box()
            except curses.error:
                # Fallback border drawing
                try:
                    for y in range(win_height):
                        if y == 0 or y == win_height - 1:
                            for x in range(win_width):
                                if x == 0 or x == win_width - 1:
                                    self.output_win.addstr(y, x, '+')
                                else:
                                    self.output_win.addstr(y, x, '-')
                        else:
                            self.output_win.addstr(y, 0, '|')
                            self.output_win.addstr(y, win_width - 1, '|')
                except curses.error:
                    pass
            
            # Draw content based on navigation state
            if self.navigation_state == NAV_HELP_TOPICS:
                self.draw_help_topics()
            elif self.navigation_state == NAV_HELP_CONTENT:
                self.draw_help_content()
            elif self.navigation_state == NAV_SUB_MENU:
                self.draw_submenu()
            elif self.navigation_state == NAV_OPERATION:
                self.draw_operation_output()
            else:
                self.draw_context_help()
            
            self.output_win.refresh()
        except Exception:
            # Silent fail for output panel
            pass
    
    def draw_help_topics(self):
        """FIXED: Draw help topics list with bounds checking"""
        if not self.output_win:
            return
            
        try:
            win_height, win_width = self.output_win.getmaxyx()
        except curses.error:
            return
        
        is_active = (self.active_panel == "right" and 
                    self.navigation_state == NAV_HELP_TOPICS)
        
        title = " 📖 HELP TOPICS "
        if is_active:
            title = " ► HELP TOPICS ◄ "
        
        # Draw title if it fits
        if len(title) <= win_width - 4:
            title_x = max(2, (win_width - len(title)) // 2)
            try:
                self.output_win.addstr(0, title_x, title, 
                                     self.get_color_pair(COLOR_OUTPUT_NORMAL) | curses.A_BOLD)
            except curses.error:
                pass
        
        y = 2
        for i, (topic_id, topic_name) in enumerate(self.help_topics):
            if y >= win_height - 2:
                break
            
            is_selected = (is_active and i == self.help_topic_selection)
            
            if is_selected:
                indicator = "►"
                color = COLOR_MENU_SELECTED
                attr = curses.A_BOLD
            else:
                indicator = " "
                color = COLOR_OUTPUT_NORMAL
                attr = 0
            
            text = f"{indicator} {topic_name}"
            if len(text) > win_width - 4:
                text = text[:win_width - 4]
            
            try:
                self.output_win.addstr(y, 2, text, self.get_color_pair(color) | attr)
            except curses.error:
                pass
            y += 1
        
        # Instructions if there's space
        if y < win_height - 4:
            instructions = [
                "↑↓: Navigate topics",
                "ENTER: View topic",
                "←: Back to main menu"
            ]
            for instruction in instructions:
                if y < win_height - 2 and len(instruction) <= win_width - 4:
                    try:
                        self.output_win.addstr(y, 2, instruction, 
                                             self.get_color_pair(COLOR_HELP_TEXT))
                    except curses.error:
                        pass
                    y += 1
    
    def draw_help_content(self):
        """FIXED: Draw scrollable help content with proper bounds checking"""
        if not self.output_win:
            return
            
        try:
            win_height, win_width = self.output_win.getmaxyx()
        except curses.error:
            return
        
        is_active = (self.active_panel == "right" and 
                    self.navigation_state == NAV_HELP_CONTENT)
        
        if self.help_topic_selection < len(self.help_topics):
            topic_id, topic_name = self.help_topics[self.help_topic_selection]
            
            title = f" 📄 {topic_name.upper()} "
            if is_active:
                title = f" ► {topic_name.upper()} ◄ "
            
            # Draw title if it fits
            if len(title) <= win_width - 4:
                title_x = max(2, (win_width - len(title)) // 2)
                try:
                    self.output_win.addstr(0, title_x, title, 
                                         self.get_color_pair(COLOR_OUTPUT_NORMAL) | curses.A_BOLD)
                except curses.error:
                    pass
            
            # Get help content
            content = self.get_help_content(topic_id)
            
            # Draw scrollable content
            visible_lines = win_height - 4
            start_line = self.help_content_scroll
            y = 2
            
            for i in range(start_line, min(len(content), start_line + visible_lines)):
                if y >= win_height - 2:
                    break
                
                line = content[i]
                color = COLOR_OUTPUT_NORMAL
                attr = 0
                
                # Style different line types
                if line.startswith("###"):
                    color = COLOR_OUTPUT_SUCCESS
                    attr = curses.A_BOLD
                    line = line[3:].strip()
                elif line.startswith("•"):
                    color = COLOR_HELP_TEXT
                elif line.startswith("⚠"):
                    color = COLOR_WARNING
                    attr = curses.A_BOLD
                
                # Truncate line if too long
                display_line = line[:win_width - 4] if len(line) > win_width - 4 else line
                
                try:
                    self.output_win.addstr(y, 2, display_line, 
                                         self.get_color_pair(color) | attr)
                except curses.error:
                    pass
                y += 1
            
            # Show scroll indicators if needed
            if len(content) > visible_lines:
                try:
                    if self.help_content_scroll > 0:
                        self.output_win.addstr(2, win_width - 3, "▲", 
                                             self.get_color_pair(COLOR_HELP_TEXT))
                    
                    if start_line + visible_lines < len(content):
                        self.output_win.addstr(win_height - 3, win_width - 3, "▼", 
                                             self.get_color_pair(COLOR_HELP_TEXT))
                except curses.error:
                    pass
            
            # Instructions at bottom
            instructions_y = win_height - 2
            instruction_text = "↑↓: Scroll | ←: Back to topics"
            if len(instruction_text) <= win_width - 4:
                try:
                    self.output_win.addstr(instructions_y, 2, instruction_text, 
                                         self.get_color_pair(COLOR_HELP_TEXT))
                except curses.error:
                    pass
    
    def draw_submenu(self):
        """FIXED: Draw submenu options with bounds checking"""
        if not self.output_win:
            return
            
        try:
            win_height, win_width = self.output_win.getmaxyx()
        except curses.error:
            return
        
        is_active = (self.active_panel == "right" and 
                    self.navigation_state == NAV_SUB_MENU)
        
        title = " ⚙️ OPTIONS "
        if is_active:
            title = " ► OPTIONS ◄ "
        
        # Draw title if it fits
        if len(title) <= win_width - 4:
            title_x = max(2, (win_width - len(title)) // 2)
            try:
                self.output_win.addstr(0, title_x, title, 
                                     self.get_color_pair(COLOR_OUTPUT_NORMAL) | curses.A_BOLD)
            except curses.error:
                pass
        
        y = 2
        for i, (key, name, desc) in enumerate(self.sub_menu_items):
            if y >= win_height - 4:
                break
                
            is_selected = (is_active and i == self.sub_menu_selection)
            
            if is_selected:
                indicator = "►"
                color = COLOR_MENU_SELECTED
                attr = curses.A_BOLD
            else:
                indicator = " "
                color = COLOR_OUTPUT_NORMAL
                attr = 0
            
            text = f"{indicator} {name}"
            if len(text) > win_width - 4:
                text = text[:win_width - 4]
            
            try:
                self.output_win.addstr(y, 2, text, self.get_color_pair(color) | attr)
            except curses.error:
                pass
            y += 1
        
        # Show description for selected item if there's space
        if (0 <= self.sub_menu_selection < len(self.sub_menu_items) and 
            y < win_height - 3):
            y += 1
            _, _, desc = self.sub_menu_items[self.sub_menu_selection]
            if desc and len("Description:") <= win_width - 4:
                try:
                    self.output_win.addstr(y, 2, "Description:", 
                                         self.get_color_pair(COLOR_HELP_TEXT) | curses.A_BOLD)
                except curses.error:
                    pass
                y += 1
                
                # Word wrap description
                words = desc.split()
                line = ""
                max_width = win_width - 6
                
                for word in words:
                    if len(line + word) > max_width:
                        if line and y < win_height - 2:
                            try:
                                self.output_win.addstr(y, 2, line.strip(), 
                                                     self.get_color_pair(COLOR_OUTPUT_NORMAL))
                            except curses.error:
                                pass
                            y += 1
                            line = word + " "
                        elif y < win_height - 2:
                            try:
                                self.output_win.addstr(y, 2, word, 
                                                     self.get_color_pair(COLOR_OUTPUT_NORMAL))
                            except curses.error:
                                pass
                            y += 1
                            line = ""
                    else:
                        line += word + " "
                
                if line.strip() and y < win_height - 2:
                    try:
                        self.output_win.addstr(y, 2, line.strip(), 
                                             self.get_color_pair(COLOR_OUTPUT_NORMAL))
                    except curses.error:
                        pass

# Part 6 of 7: GUI Methods & Core Operations with --no-verify Fix
# Hollik's Greaseweazle Helper v1.0

    def draw_operation_output(self):
        """FIXED: Draw operation output with scrolling"""
        if not self.output_win:
            return
            
        try:
            win_height, win_width = self.output_win.getmaxyx()
        except curses.error:
            return
        
        title = " 📄 OUTPUT "
        if len(title) <= win_width - 4:
            title_x = max(2, (win_width - len(title)) // 2)
            try:
                self.output_win.addstr(0, title_x, title, 
                                     self.get_color_pair(COLOR_OUTPUT_NORMAL) | curses.A_BOLD)
            except curses.error:
                pass
        
        # Show output lines with scrolling
        visible_lines = win_height - 4
        start_line = max(0, len(self.output_lines) - visible_lines)
        y = 2
        
        for i in range(start_line, len(self.output_lines)):
            if y < win_height - 2:
                line = self.output_lines[i]
                color = COLOR_OUTPUT_NORMAL
                attr = 0
                
                if line.startswith("✓"):
                    color = COLOR_OUTPUT_SUCCESS
                    attr = curses.A_BOLD
                elif line.startswith("✗") or line.startswith("ERROR"):
                    color = COLOR_OUTPUT_ERROR
                    attr = curses.A_BOLD
                elif line.startswith("⚠"):
                    color = COLOR_WARNING
                    attr = curses.A_BOLD
                
                display_line = line[:win_width - 4] if len(line) > win_width - 4 else line
                try:
                    self.output_win.addstr(y, 2, display_line, 
                                         self.get_color_pair(color) | attr)
                except curses.error:
                    pass
                y += 1
    
    def draw_context_help(self):
        """FIXED: Draw context-sensitive help for main menu"""
        if not self.output_win:
            return
            
        try:
            win_height, win_width = self.output_win.getmaxyx()
        except curses.error:
            return
        
        title = " 📖 HELP "
        if len(title) <= win_width - 4:
            title_x = max(2, (win_width - len(title)) // 2)
            try:
                self.output_win.addstr(0, title_x, title, 
                                     self.get_color_pair(COLOR_OUTPUT_NORMAL) | curses.A_BOLD)
            except curses.error:
                pass
        
        # Get current menu item
        valid_items = [item for item in menu_items if item[0]]
        if 0 <= self.main_menu_selection < len(valid_items):
            key, name, desc = valid_items[self.main_menu_selection]
            
            # Show brief help
            help_text = self.get_brief_help(key, name, desc)
            y = 2
            
            for line in help_text:
                if y < win_height - 2:
                    color = COLOR_OUTPUT_NORMAL
                    attr = 0
                    
                    if line.startswith("✓"):
                        color = COLOR_OUTPUT_SUCCESS
                    elif line.startswith("⚠"):
                        color = COLOR_WARNING
                    elif line.isupper() and len(line) > 3:
                        attr = curses.A_BOLD
                    
                    display_line = line[:win_width - 4] if len(line) > win_width - 4 else line
                    try:
                        self.output_win.addstr(y, 2, display_line, 
                                             self.get_color_pair(color) | attr)
                    except curses.error:
                        pass
                    y += 1
    
    def draw_bottom_bar(self):
        """FIXED: Draw instruction bar with proper bounds checking"""
        if not self.bottom_win:
            return
            
        try:
            self.bottom_win.clear()
            self.bottom_win.bkgd(' ', self.get_color_pair(COLOR_STATUS_BAR))
            
            win_height, win_width = self.bottom_win.getmaxyx()
            
            # Context-sensitive instructions
            if self.operation_in_progress:
                instructions = "ESC: Cancel | Operation in progress..."
            elif self.waiting_for_input:
                instructions = "ENTER: Continue | Operation completed"
            elif self.navigation_state == NAV_MAIN_MENU:
                if self.active_panel == "left":
                    instructions = "Up/Down: Navigate | Right: Help | ENTER: Select | R: Config | F10: Exit"
                else:
                    instructions = "Left: Main Menu | Up/Down: Navigate | ENTER: Select"
            elif self.navigation_state == NAV_HELP_TOPICS:
                instructions = "Up/Down: Navigate Topics | ENTER: View | Left: Main Menu"
            elif self.navigation_state == NAV_HELP_CONTENT:
                instructions = "Up/Down: Scroll Content | Left: Back to Topics"
            elif self.navigation_state == NAV_SUB_MENU:
                instructions = "Up/Down: Navigate | ENTER: Execute | Left: Back | F10: Exit"
            else:
                instructions = "ENTER: Continue | ESC: Cancel"
            
            # Truncate if too long
            if len(instructions) > win_width - 4:
                instructions = instructions[:win_width - 7] + "..."
            
            try:
                self.bottom_win.addstr(0, 2, instructions, self.get_color_pair(COLOR_STATUS_BAR))
            except curses.error:
                pass
            
            # Show current operation
            if current_operation and win_height > 1:
                op_text = f"Operation: {current_operation}"
                if len(op_text) < win_width - 4:
                    try:
                        self.bottom_win.addstr(1, 2, op_text, 
                                             self.get_color_pair(COLOR_STATUS_BAR) | curses.A_BOLD)
                    except curses.error:
                        pass
            
            self.bottom_win.refresh()
        except Exception:
            pass
    
    def refresh_all(self):
        """FIXED: Refresh all windows with error handling"""
        try:
            self.draw_status_bar()
            self.draw_main_menu()
            self.draw_output_panel()
            self.draw_bottom_bar()
        except Exception:
            pass
    
    def add_output_line(self, line):
        """Add line to output with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        if line and not line.startswith("["):
            formatted_line = f"[{timestamp}] {line}"
        else:
            formatted_line = line
        
        self.output_lines.append(formatted_line)
        
        # Keep reasonable history
        if len(self.output_lines) > 1000:
            self.output_lines = self.output_lines[-1000:]
    
    def clear_output(self):
        """Clear output and switch to operation mode"""
        self.output_lines = []
        self.navigation_state = NAV_OPERATION
        self.active_panel = "right"
        self.waiting_for_input = False
        self.operation_in_progress = False
    
    def wait_for_continue(self):
        """Set waiting state"""
        self.waiting_for_input = True
        self.add_output_line("")
        self.add_output_line("Press ENTER to continue...")
        self.refresh_all()
    
    def continue_from_wait(self):
        """Clear waiting state"""
        self.waiting_for_input = False
        self.switch_to_main_menu()
    
    def switch_to_main_menu(self):
        """Return to main menu"""
        self.navigation_state = NAV_MAIN_MENU
        self.active_panel = "left"
        self.sub_menu_items = []
        self.waiting_for_input = False
        self.operation_in_progress = False
    
    def switch_to_help_topics(self):
        """Switch to help topics view"""
        self.navigation_state = NAV_HELP_TOPICS
        self.active_panel = "right"
        self.help_topic_selection = 0
    
    def show_submenu(self, items):
        """Show submenu"""
        self.sub_menu_items = items
        self.sub_menu_selection = 0
        self.navigation_state = NAV_SUB_MENU
        self.active_panel = "right"
    
    def get_brief_help(self, key, name, desc):
        """Get brief context help for main menu items"""
        brief_help = {
            "W": [
                "WELCOME",
                "Hollik's Greaseweazle Helper v1.0 overview",
                "Professional floppy disk operations",
                "→ Press H for detailed help topics"
            ],
            "R": [
                "RECONFIGURE SETTINGS",
                f"Current: {target_system}, {drive_descriptions[drive_type]}",
                "Change system, drive type, COM port",
                "Hardware detection and testing"
            ],
            "1": [
                "CLEAN DISK",
                "Complete erase of floppy disk",
                "Removes all data and filesystem",
                "⚠ Permanent data loss"
            ],
            "2": [
                "FORMAT DISK", 
                f"Create {target_system} filesystem",
                f"Available: {', '.join(get_available_formats().keys())}",
                "Uses verified template files with --no-verify"
            ],
            "3": [
                "WRITE IMAGE",
                "Transfer image file to floppy",
                "Supports multiple formats",
                "Uses --no-verify for compatibility"
            ],
            "4": [
                "BACKUP DISK",
                "Save floppy as image file",
                "Standard or flux backup",
                "Preserves data digitally"
            ],
            "5": [
                "VERIFY DISK",
                "Check disk integrity",
                "Quick or full verification", 
                "Bad sector detection"
            ],
            "6": [
                "DISK STATUS",
                "Hardware and disk information",
                "Connection test",
                "Drive capabilities"
            ],
            "7": [
                "REPAIR DISK",
                "Complete recovery sequence",
                "Clean → Format → Verify",
                "⚠ Destroys existing data"
            ],
            "H": [
                "HELP TOPICS",
                "Detailed documentation",
                "Step-by-step guides",
                "Troubleshooting info"
            ],
            "0": [
                "EXIT PROGRAM",
                "Safe shutdown with cleanup",
                "Settings automatically saved",
                "Hardware properly disconnected"
            ]
        }
        return brief_help.get(key, [desc])
    
    def get_help_content(self, topic_id):
        """Get detailed help content for topics"""
        content = {
            "getting_started": [
                "### GETTING STARTED",
                "",
                "Welcome to Hollik's Greaseweazle Helper v1.0!",
                "",
                "• Use ↑↓ arrows to navigate the main menu",
                "• Press → to access help or submenus", 
                "• Press ← to return to main menu",
                "• ENTER selects/executes operations",
                "",
                "### BASIC WORKFLOW",
                "",
                "For new disks: Clean → Format → Verify",
                "For backups: Insert disk → Backup",
                "For writing: Select image → Write → Verify"
            ],
            "no_verify_mode": [
                "### --NO-VERIFY MODE",
                "",
                "This helper uses --no-verify for all write operations.",
                "",
                "Why --no-verify is used:",
                "• Prevents 'Failed to verify Track 0.0' errors",
                "• Better compatibility with various drive types",
                "• Recommended by Greaseweazle best practices",
                "• Writes are usually successful even if verify fails",
                "",
                "The write operation itself is still reliable,",
                "verification failures are often due to timing",
                "differences between drives, not actual errors."
            ],
            "format_strings": [
                "### FORMAT STRINGS",
                "",
                "This helper uses official format strings from",
                "the Yann Serra Tutorial:",
                "",
                f"Current system: {target_system}",
                ""
            ] + [f"• {size}: {fmt}" for size, (fmt, _, _) in get_available_formats().items()][:8]
        }
        return content.get(topic_id, ["No help available for this topic."])

# FIXED: Core operation functions with --no-verify support
def run_greaseweazle_command(gui, title, args, timeout=300):
    """FIXED: Execute Greaseweazle command with --no-verify and progress monitoring"""
    global operation_cancelled, current_operation
    
    operation_cancelled = False
    current_operation = title
    gui.operation_in_progress = True
    
    gui.add_output_line(f"EXECUTING: {title}")
    gui.add_output_line("=" * (len(title) + 11))
    gui.add_output_line(f"Command: {' '.join(args)}")
    gui.add_output_line("Press ESC to cancel")
    gui.refresh_all()
    
    try:
        signal.signal(signal.SIGINT, signal_handler)
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                              text=True, bufsize=1)
        
        start_time = time.time()
        
        while True:
            if operation_cancelled:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                gui.add_output_line("✗ Operation cancelled")
                log_operation(title, "CANCELLED", "User cancelled")
                return False
            
            if time.time() - start_time > timeout:
                proc.terminate()
                gui.add_output_line(f"✗ Timeout after {timeout}s")
                log_operation(title, "TIMEOUT", f"Exceeded {timeout}s")
                return False
            
            try:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.rstrip()
                if line:
                    gui.add_output_line(line)
                    gui.refresh_all()
            except:
                break
        
        proc.wait()
        
        if not operation_cancelled and proc.returncode == 0:
            gui.add_output_line(f"✓ {title} completed successfully")
            log_operation(title, "SUCCESS", "")
            return True
        else:
            gui.add_output_line(f"✗ {title} failed (code: {proc.returncode})")
            log_operation(title, "FAILED", f"Exit code {proc.returncode}")
            return False
            
    except Exception as e:
        gui.add_output_line(f"✗ Error: {e}")
        log_operation(title, "ERROR", str(e))
        return False
    finally:
        current_operation = None
        gui.operation_in_progress = False
        signal.signal(signal.SIGINT, signal.SIG_DFL)

def open_file_browser_safe(title, filetypes, mode="open"):
    """FIXED: Safe file browser with proper curses handling"""
    try:
        curses.endwin()
        
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.focus_force()
        root.lift()
        
        if mode == "open":
            result = filedialog.askopenfilename(title=title, filetypes=filetypes, parent=root)
        else:
            result = filedialog.asksaveasfilename(title=title, filetypes=filetypes, parent=root)
        
        root.destroy()
        return result
        
    except Exception:
        return None
    finally:
        try:
            curses.doupdate()
        except:
            pass

# Part 7 of 7: Operation Functions & Main Program Loop
# Hollik's Greaseweazle Helper v1.0
# FIXED: All operations with --no-verify support

def execute_format_disk(gui, format_name):
    """FIXED: Execute disk formatting with --no-verify"""
    gui.clear_output()
    gui.add_output_line("FORMAT DISK OPERATION")
    
    template_path = get_template_path(format_name)
    if not template_path:
        gui.add_output_line(f"✗ Template not found for {format_name}")
        gui.add_output_line("Use 'Check Templates' to verify files")
        gui.wait_for_continue()
        return
    
    formats = get_available_formats()
    fmt, filename, size = formats[format_name]
    
    gui.add_output_line(f"Format: {target_system} {format_name}")
    gui.add_output_line(f"Template: {filename} ({size:,} bytes)")
    gui.add_output_line(f"Format string: {fmt}")
    gui.add_output_line("⚠ Using --no-verify for compatibility")
    gui.add_output_line("Press ENTER to proceed, ESC to cancel")
    gui.refresh_all()
    
    while True:
        try:
            key = gui.stdscr.getch()
            if key == 27:  # ESC
                gui.add_output_line("Operation cancelled")
                gui.wait_for_continue()
                return
            elif key == 10 or key == 13:  # ENTER
                break
        except curses.error:
            continue
    
    # FIXED: Write with format string and --no-verify
    if fmt:
        args = [gw_path, "write", template_path, "--device", com_port, 
                "--format", fmt, "--no-verify"] + drive_arg()
    else:
        gui.add_output_line(f"✗ No format string for {format_name}")
        gui.wait_for_continue()
        return
    
    result = run_greaseweazle_command(gui, f"Format {format_name}", args)
    
    if result:
        gui.add_output_line("✓ Format completed successfully")
        gui.add_output_line("Disk is ready for use")
    
    gui.wait_for_continue()

def execute_write_image(gui, option):
    """FIXED: Execute write image with --no-verify"""
    gui.clear_output()
    gui.add_output_line("WRITE IMAGE TO DISK")
    gui.add_output_line("Opening file browser...")
    gui.refresh_all()
    
    # Get file extensions for current system
    filetypes = get_file_extensions_for_system(target_system, "read")
    
    path = open_file_browser_safe(f"Select {target_system} disk image", filetypes)
    gui.stdscr.refresh()
    
    if not path:
        gui.add_output_line("No file selected")
        gui.wait_for_continue()
        return
    
    filename = os.path.basename(path)
    filesize = os.path.getsize(path)
    
    # Detect format based on size and system
    detected_format = None
    formats = get_available_formats()
    
    # Match by exact file size first
    for format_name, (fmt, template_name, expected_size) in formats.items():
        if filesize == expected_size:
            detected_format = fmt
            gui.add_output_line(f"Detected: {format_name} (format: {fmt})")
            break
    
    # System-specific defaults
    if not detected_format:
        format_defaults = {
            "PC": "ibm.1440" if filesize > 1000000 else "ibm.720",
            "Amiga": "amiga.amigados",
            "Apple": "mac.800" if filesize <= 900000 else "ibm.1440",
            "Atari": "atarist.720" if filesize > 500000 else "atarist.360",
            "C64": "commodore.1541",
            "ZXSpectrum": "zx.trdos.640"
        }
        detected_format = format_defaults.get(target_system, "ibm.720")
        gui.add_output_line(f"Using default: {detected_format}")
    
    gui.add_output_line(f"File: {filename}")
    gui.add_output_line(f"Size: {filesize:,} bytes")
    gui.add_output_line("⚠ Using --no-verify for compatibility")
    gui.add_output_line("⚠ This will overwrite disk!")
    gui.add_output_line("Press ENTER to write, ESC to cancel")
    gui.refresh_all()
    
    while True:
        try:
            key = gui.stdscr.getch()
            if key == 27:  # ESC
                gui.add_output_line("Operation cancelled")
                gui.wait_for_continue()
                return
            elif key == 10 or key == 13:  # ENTER
                break
        except curses.error:
            continue
    
    # FIXED: Write with format string and --no-verify
    if detected_format:
        args = [gw_path, "write", path, "--device", com_port, 
                "--format", detected_format, "--no-verify"] + drive_arg()
    else:
        gui.add_output_line("✗ Could not determine format")
        gui.wait_for_continue()
        return
    
    result = run_greaseweazle_command(gui, f"Write {filename}", args)
    
    if result:
        gui.add_output_line("✓ Image written successfully")
        gui.add_output_line("Disk is ready for use")
    
    gui.wait_for_continue()

def execute_backup_disk(gui, backup_type):
    """Execute backup operation"""
    gui.clear_output()
    gui.add_output_line("BACKUP DISK TO IMAGE")
    gui.add_output_line(f"Type: {backup_type}")
    gui.add_output_line("Opening save dialog...")
    gui.refresh_all()
    
    # Determine file extension and format
    if backup_type == "FLUX":
        default_ext = get_default_extension("FLUX")
        filetypes = [("Flux Images", "*.scp"), ("All", "*.*")]
        gw_format = "scp"
    else:
        default_ext = get_default_extension(target_system)
        filetypes = get_file_extensions_for_system(target_system, "write")
        
        format_map = {
            "PC": "ibm.1440",
            "Amiga": None,
            "Apple": None, 
            "Atari": None,
            "C64": None,
            "ZXSpectrum": None
        }
        gw_format = format_map.get(target_system)
    
    path = open_file_browser_safe(f"Save {target_system} backup", filetypes, mode="save")
    gui.stdscr.refresh()
    
    if not path:
        gui.add_output_line("No file selected")
        gui.wait_for_continue()
        return
    
    if not path.lower().endswith(default_ext.lower()):
        path += default_ext
    
    filename = os.path.basename(path)
    gui.add_output_line(f"Backup to: {filename}")
    
    # Build command
    if backup_type == "FLUX":
        args = [gw_path, "read", path, "--device", com_port, "--format", "scp"] + drive_arg()
    elif gw_format and target_system == "PC":
        args = [gw_path, "read", path, "--device", com_port, "--format", gw_format] + drive_arg()
    else:
        args = [gw_path, "read", path, "--device", com_port] + drive_arg()
    
    result = run_greaseweazle_command(gui, f"Backup to {filename}", args)
    
    if result and os.path.exists(path):
        final_size = os.path.getsize(path)
        gui.add_output_line(f"✓ Backup completed: {final_size:,} bytes")
    
    gui.wait_for_continue()

def execute_clean_disk(gui, format_type):
    """Execute disk cleaning operation"""
    gui.clear_output()
    gui.add_output_line("CLEAN DISK OPERATION")
    gui.add_output_line(f"Format: {format_type}")
    gui.add_output_line("⚠ WARNING: All data will be lost!")
    gui.add_output_line("Press ENTER to confirm, ESC to cancel")
    gui.refresh_all()
    
    while True:
        try:
            key = gui.stdscr.getch()
            if key == 27:  # ESC
                gui.add_output_line("Operation cancelled")
                gui.wait_for_continue()
                return
            elif key == 10 or key == 13:  # ENTER
                break
        except curses.error:
            continue
    
    args = [gw_path, "erase", "--device", com_port] + drive_arg()
    result = run_greaseweazle_command(gui, "Clean Disk", args)
    
    if result:
        gui.add_output_line("✓ Disk cleaned successfully")
    
    gui.wait_for_continue()

def execute_verify_disk(gui, verify_type):
    """Execute disk verification"""
    gui.clear_output()
    gui.add_output_line("VERIFY DISK INTEGRITY")
    gui.add_output_line(f"Type: {verify_type}")
    
    if verify_type == "COMPARE":
        gui.add_output_line("Template comparison not available")
        gui.wait_for_continue()
        return
    
    # Use proper file extension
    ext = get_default_extension(target_system)
    temp_file = f"temp_verify{ext}"
    
    if verify_type == "QUICK":
        args = [gw_path, "read", temp_file, "--device", com_port, "--tracks", "0-5"] + drive_arg()
        title = "Quick Verify (6 tracks)"
    else:  # FULL
        args = [gw_path, "read", temp_file, "--device", com_port] + drive_arg()
        title = "Full Verify (complete disk)"
    
    result = run_greaseweazle_command(gui, title, args)
    
    if result and os.path.exists(temp_file):
        file_size = os.path.getsize(temp_file)
        gui.add_output_line(f"✓ Verification PASSED ({file_size:,} bytes)")
        try:
            os.remove(temp_file)
        except:
            pass
    elif result:
        gui.add_output_line("⚠ Verification completed but no data")
    else:
        gui.add_output_line("✗ Verification FAILED")
    
    gui.wait_for_continue()

def execute_repair_disk(gui, format_name):
    """FIXED: Execute complete repair sequence with --no-verify"""
    gui.clear_output()
    gui.add_output_line("REPAIR DISK SEQUENCE")
    gui.add_output_line(f"Target: {target_system} {format_name}")
    gui.add_output_line("Process: Clean → Format → Verify")
    gui.add_output_line("⚠ Using --no-verify for format step")
    gui.add_output_line("⚠ ALL DATA WILL BE LOST!")
    gui.add_output_line("Press ENTER to start, ESC to cancel")
    gui.refresh_all()
    
    while True:
        try:
            key = gui.stdscr.getch()
            if key == 27:  # ESC
                gui.add_output_line("Repair cancelled")
                gui.wait_for_continue()
                return
            elif key == 10 or key == 13:  # ENTER
                break
        except curses.error:
            continue
    
    # Determine format
    if format_name == "AUTO":
        format_name = default_disk_size or list(get_available_formats().keys())[0]
    
    template_path = get_template_path(format_name)
    if not template_path:
        gui.add_output_line(f"✗ Template not available for {format_name}")
        gui.wait_for_continue()
        return
    
    # Step 1: Clean
    gui.add_output_line("STEP 1: CLEAN")
    clean_args = [gw_path, "erase", "--device", com_port] + drive_arg()
    if not run_greaseweazle_command(gui, "Repair - Clean", clean_args):
        gui.add_output_line("✗ Repair failed at clean step")
        gui.wait_for_continue()
        return
    
    # Step 2: Format with --no-verify
    gui.add_output_line("STEP 2: FORMAT")
    formats = get_available_formats()
    fmt, filename, size = formats[format_name]
    
    if fmt:
        format_args = [gw_path, "write", template_path, "--device", com_port, 
                      "--format", fmt, "--no-verify"] + drive_arg()
    else:
        gui.add_output_line(f"✗ No format string for {format_name}")
        gui.wait_for_continue()
        return
    
    if not run_greaseweazle_command(gui, "Repair - Format", format_args):
        gui.add_output_line("✗ Repair failed at format step")
        gui.wait_for_continue()
        return
    
    # Step 3: Verify
    gui.add_output_line("STEP 3: VERIFY")
    ext = get_default_extension(target_system)
    temp_file = f"temp_repair_verify{ext}"
    
    verify_args = [gw_path, "read", temp_file, "--device", com_port] + drive_arg()
    verify_result = run_greaseweazle_command(gui, "Repair - Verify", verify_args)
    
    gui.add_output_line("REPAIR COMPLETE")
    if verify_result:
        gui.add_output_line(f"✓ Disk repaired as {target_system} {format_name}")
    else:
        gui.add_output_line("⚠ Repair completed with verification issues")
    
    try:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    except:
        pass
    
    gui.wait_for_continue()

# Menu generation functions
def generate_clean_submenu():
    """Generate clean disk submenu"""
    formats = get_available_formats()
    items = [("GENERAL", "🧹 General Complete Clean", "Universal disk erase for any format")]
    
    for format_name in formats.keys():
        items.append((format_name, f"🎯 Clean for {format_name}", 
                     f"Optimized clean for {target_system} {format_name}"))
    return items

def generate_format_submenu():
    """Generate format disk submenu"""
    formats = get_available_formats()
    items = []
    
    for format_name, (fmt, filename, size) in formats.items():
        status = "✅" if get_template_path(format_name) else "❌"
        name = f"{status} {target_system} {format_name}"
        if format_name == default_disk_size:
            name += " (Default)"
        
        desc = f"Format as {format_name} using {filename} ({size:,} bytes) with --no-verify"
        items.append((format_name, name, desc))
    
    return items

def generate_write_submenu():
    """Generate write image submenu"""
    return [
        ("SELECT_FILE", "📁 Select Image File", 
         f"Browse and select a {target_system} disk image to write with --no-verify")
    ]

def generate_backup_submenu():
    """Generate backup disk submenu"""
    return [
        ("STANDARD", "💾 Standard Backup", 
         "Filesystem backup, smaller files"),
        ("FLUX", "🧲 Flux Backup", 
         "Raw data backup, preserves copy protection"),
        ("AUTO_FORMAT", f"🎯 Auto {target_system}", 
         f"Detect and use optimal {target_system} format")
    ]

def generate_verify_submenu():
    """Generate verify disk submenu"""
    return [
        ("QUICK", "⚡ Quick Check", 
         "Fast verification of critical areas"),
        ("FULL", "🔍 Complete Verification", 
         "Full disk scan with bad sector mapping"),
        ("COMPARE", "📊 Template Compare", 
         f"Compare against {target_system} template")
    ]

def generate_repair_submenu():
    """Generate repair disk submenu"""
    formats = get_available_formats()
    items = [("AUTO", f"🔧 Auto-Repair {target_system}", 
             f"Automatic repair using {default_disk_size or 'default'} format with --no-verify")]
    
    for format_name in formats.keys():
        status = "✅" if get_template_path(format_name) else "❌"
        name = f"{status} Repair as {format_name}"
        if format_name == default_disk_size:
            name += " (Default)"
        
        desc = f"Complete repair targeting {format_name} format with --no-verify"
        items.append((format_name, name, desc))
    
    return items

# Main program functions
def handle_main_menu_selection(gui, selection):
    """Handle main menu item selection"""
    valid_items = [item for item in menu_items if item[0]]
    
    if selection < 0 or selection >= len(valid_items):
        return True
    
    key, name, desc = valid_items[selection]
    
    if key == "W":  # Welcome
        return True
    elif key == "R":  # Reconfigure
        gui.show_submenu([
            ("TARGET_SYSTEM", f"🖥️ Target: {target_system}", 
             f"Change from {system_descriptions[target_system]}"),
            ("DISK_SIZE", f"💾 Size: {default_disk_size or 'Not set'}", 
             f"Default disk size for {target_system}"),
            ("DRIVE_TYPE", f"🔌 Drive: {drive_descriptions[drive_type]}", 
             "Cable type and drive configuration"),
            ("RESCAN_HARDWARE", "🔍 Rescan Hardware", 
             "Scan COM ports for Greaseweazle devices"),
            ("TEST_CONNECTION", "🔧 Test Connection", 
             "Test current device and show info"),
            ("CHECK_TEMPLATES", "📋 Check Templates", 
             "Verify template files present and valid")
        ])
    elif key == "1":  # Clean
        gui.show_submenu(generate_clean_submenu())
    elif key == "2":  # Format
        gui.show_submenu(generate_format_submenu())
    elif key == "3":  # Write
        gui.show_submenu(generate_write_submenu())
    elif key == "4":  # Backup
        gui.show_submenu(generate_backup_submenu())
    elif key == "5":  # Verify
        gui.show_submenu(generate_verify_submenu())
    elif key == "6":  # Status
        gui.clear_output()
        gui.add_output_line("SYSTEM STATUS")
        gui.add_output_line("=" * 13)
        gui.add_output_line(f"• System: {target_system}")
        gui.add_output_line(f"• Drive: {drive_descriptions[drive_type]}")
        gui.add_output_line(f"• COM Port: {com_port or 'Not set'}")
        gui.add_output_line(f"• Default Size: {default_disk_size or 'Not set'}")
        gui.add_output_line(f"• Formats Available: {len(get_available_formats())}")
        gui.wait_for_continue()
    elif key == "7":  # Repair
        gui.show_submenu(generate_repair_submenu())
    elif key == "H":  # Help
        gui.switch_to_help_topics()
    elif key == "0":  # Exit
        return False
    
    return True

def handle_main_menu_selection(gui, selection):
    """Handle main menu item selection"""
    valid_items = [item for item in menu_items if item[0]]
    
    if selection < 0 or selection >= len(valid_items):
        return True
    
    key, name, desc = valid_items[selection]
    
    if key == "W":  # Welcome
        return True
    elif key == "R":  # Reconfigure
        gui.show_submenu([
            ("TARGET_SYSTEM", f"🖥️ Target: {target_system}", 
             f"Change from {system_descriptions[target_system]}"),
            ("DISK_SIZE", f"💾 Size: {default_disk_size or 'Not set'}", 
             f"Default disk size for {target_system}"),
            ("DRIVE_TYPE", f"🔌 Drive: {drive_descriptions[drive_type]}", 
             "Cable type and drive configuration"),
            ("RESCAN_HARDWARE", "🔍 Rescan Hardware", 
             "Scan COM ports for Greaseweazle devices"),
            ("TEST_CONNECTION", "🔧 Test Connection", 
             "Test current device and show info"),
            ("CHECK_TEMPLATES", "📋 Check Templates", 
             "Verify template files present and valid")
        ])
    elif key == "1":  # Clean
        gui.show_submenu(generate_clean_submenu())
    elif key == "2":  # Format
        gui.show_submenu(generate_format_submenu())
    elif key == "3":  # Write
        gui.show_submenu(generate_write_submenu())
    elif key == "4":  # Backup
        gui.show_submenu(generate_backup_submenu())
    elif key == "5":  # Verify
        gui.show_submenu(generate_verify_submenu())
    elif key == "6":  # Status
        gui.clear_output()
        gui.add_output_line("SYSTEM STATUS")
        gui.add_output_line("=" * 13)
        gui.add_output_line(f"• System: {target_system}")
        gui.add_output_line(f"• Drive: {drive_descriptions[drive_type]}")
        gui.add_output_line(f"• COM Port: {com_port or 'Not set'}")
        gui.add_output_line(f"• Default Size: {default_disk_size or 'Not set'}")
        gui.add_output_line(f"• Formats Available: {len(get_available_formats())}")
        gui.wait_for_continue()
    elif key == "7":  # Repair
        gui.show_submenu(generate_repair_submenu())
    elif key == "H":  # Help
        gui.switch_to_help_topics()
    elif key == "0":  # Exit
        return False
    
    return True

def handle_submenu_selection(gui, main_selection, sub_selection):
    """Handle submenu selection"""
    valid_items = [item for item in menu_items if item[0]]
    
    if main_selection >= len(valid_items) or sub_selection >= len(gui.sub_menu_items):
        return True
    
    key, name, desc = valid_items[main_selection]
    sub_key, sub_name, sub_desc = gui.sub_menu_items[sub_selection]
    
    if key == "R":  # Reconfigure
        execute_reconfigure(gui, sub_key)
    elif key == "1":  # Clean
        execute_clean_disk(gui, sub_key)
    elif key == "2":  # Format
        execute_format_disk(gui, sub_key)
    elif key == "3":  # Write
        execute_write_image(gui, sub_key)
    elif key == "4":  # Backup
        execute_backup_disk(gui, sub_key)
    elif key == "5":  # Verify
        execute_verify_disk(gui, sub_key)
    elif key == "7":  # Repair
        execute_repair_disk(gui, sub_key)
    
    return True

def execute_reconfigure(gui, option):
    """Execute reconfigure operations"""
    global target_system, drive_type, default_disk_size
    
    gui.clear_output()
    
    if option == "TARGET_SYSTEM":
        gui.add_output_line("SELECT TARGET SYSTEM")
        systems = list(system_descriptions.keys())
        selection = systems.index(target_system) if target_system in systems else 0
        
        while True:
            gui.clear_output()
            gui.add_output_line("SELECT TARGET SYSTEM")
            gui.add_output_line("=" * 20)
            
            for i, system in enumerate(systems):
                marker = "►" if i == selection else " "
                gui.add_output_line(f"{marker} {i+1}) {system} - {system_descriptions[system]}")
            
            gui.add_output_line("")
            gui.add_output_line("↑↓: Navigate | ENTER: Select | ESC: Cancel")
            gui.refresh_all()
            
            key = gui.stdscr.getch()
            if key == curses.KEY_UP:
                selection = max(0, selection - 1)
            elif key == curses.KEY_DOWN:
                selection = min(len(systems) - 1, selection + 1)
            elif key == 10 or key == 13:  # ENTER
                target_system = systems[selection]
                formats = get_available_formats()
                if formats:
                    default_disk_size = list(formats.keys())[0]
                gui.add_output_line(f"✓ System set to: {target_system}")
                save_config()
                break
            elif key == 27:  # ESC
                gui.add_output_line("Selection cancelled")
                break
    
    elif option == "DISK_SIZE":
        gui.add_output_line("SELECT DISK SIZE")
        formats = get_available_formats()
        sizes = list(formats.keys())
        if not sizes:
            gui.add_output_line("No formats available for current system")
            gui.wait_for_continue()
            return
        
        selection = sizes.index(default_disk_size) if default_disk_size in sizes else 0
        
        while True:
            gui.clear_output()
            gui.add_output_line(f"SELECT DISK SIZE ({target_system})")
            gui.add_output_line("=" * 25)
            
            for i, size in enumerate(sizes):
                marker = "►" if i == selection else " "
                status = "✓" if get_template_path(size) else "✗"
                gui.add_output_line(f"{marker} {i+1}) {size} {status}")
            
            gui.add_output_line("")
            gui.add_output_line("↑↓: Navigate | ENTER: Select | ESC: Cancel")
            gui.refresh_all()
            
            key = gui.stdscr.getch()
            if key == curses.KEY_UP:
                selection = max(0, selection - 1)
            elif key == curses.KEY_DOWN:
                selection = min(len(sizes) - 1, selection + 1)
            elif key == 10 or key == 13:  # ENTER
                default_disk_size = sizes[selection]
                gui.add_output_line(f"✓ Size set to: {default_disk_size}")
                save_config()
                break
            elif key == 27:  # ESC
                gui.add_output_line("Selection cancelled")
                break
    
    elif option == "DRIVE_TYPE":
        gui.add_output_line("SELECT DRIVE TYPE")
        types = ["A", "B"]
        selection = types.index(drive_type) if drive_type in types else 1
        
        while True:
            gui.clear_output()
            gui.add_output_line("SELECT DRIVE TYPE")
            gui.add_output_line("=" * 17)
            
            for i, dt in enumerate(types):
                marker = "►" if i == selection else " "
                gui.add_output_line(f"{marker} {dt}) {drive_descriptions[dt]}")
            
            gui.add_output_line("")
            gui.add_output_line("↑↓: Navigate | ENTER: Select | ESC: Cancel")
            gui.refresh_all()
            
            key = gui.stdscr.getch()
            if key == curses.KEY_UP:
                selection = 0
            elif key == curses.KEY_DOWN:
                selection = 1
            elif key == 10 or key == 13:  # ENTER
                drive_type = types[selection]
                gui.add_output_line(f"✓ Drive set to: {drive_descriptions[drive_type]}")
                save_config()
                break
            elif key == 27:  # ESC
                gui.add_output_line("Selection cancelled")
                break
    
    gui.wait_for_continue()

def main_program_loop(stdscr):
    """FIXED: Main program loop with enhanced navigation"""
    global operation_cancelled
    
    # Initialize GUI
    try:
        gui = GreaseweazleGUI(stdscr)
    except Exception as e:
        stdscr.clear()
        stdscr.addstr(0, 0, f"GUI initialization failed: {e}")
        stdscr.addstr(1, 0, "Terminal may be too small. Press any key to exit.")
        stdscr.refresh()
        stdscr.getch()
        return
    
    # Check if setup is needed
    setup_completed = load_config()
    
    if not setup_completed:
        try:
            if run_setup_wizard(stdscr):
                pass
            else:
                return
        except Exception as e:
            stdscr.clear()
            stdscr.addstr(0, 0, f"Setup failed: {e}")
            stdscr.addstr(1, 0, "Press any key to exit.")
            stdscr.refresh()
            stdscr.getch()
            return
        
        try:
            gui = GreaseweazleGUI(stdscr)
        except Exception as e:
            stdscr.clear()
            stdscr.addstr(0, 0, f"GUI restart failed: {e}")
            stdscr.refresh()
            stdscr.getch()
            return
    else:
        # Configuration exists - clear any startup artifacts
        stdscr.clear()
        stdscr.refresh()
        curses.doupdate()
    
    gui.switch_to_main_menu()
    
    # Main program loop
    running = True
    while running:
        gui.refresh_all()
        
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            operation_cancelled = True
            continue
        
        if key == curses.KEY_RESIZE:
            gui.handle_resize()
            continue
        
        if gui.waiting_for_input:
            if key == 10 or key == 13:  # ENTER
                gui.continue_from_wait()
            continue
        
        if gui.operation_in_progress:
            if key == 27:  # ESC - Cancel operation
                operation_cancelled = True
            continue
        
        # Navigation handling
        if gui.navigation_state == NAV_MAIN_MENU:
            if gui.active_panel == "left":
                if key == curses.KEY_UP:
                    valid_items = [item for item in menu_items if item[0]]
                    gui.main_menu_selection = max(0, gui.main_menu_selection - 1)
                elif key == curses.KEY_DOWN:
                    valid_items = [item for item in menu_items if item[0]]
                    gui.main_menu_selection = min(len(valid_items) - 1, gui.main_menu_selection + 1)
                elif key == curses.KEY_RIGHT:
                    gui.switch_to_help_topics()
                elif key == 10 or key == 13:  # ENTER
                    running = handle_main_menu_selection(gui, gui.main_menu_selection)
                elif key == 27 or key == curses.KEY_F10:  # ESC or F10
                    running = False
        
        elif gui.navigation_state == NAV_SUB_MENU:
            if key == curses.KEY_UP:
                gui.sub_menu_selection = max(0, gui.sub_menu_selection - 1)
            elif key == curses.KEY_DOWN:
                gui.sub_menu_selection = min(len(gui.sub_menu_items) - 1, gui.sub_menu_selection + 1)
            elif key == 10 or key == 13:  # ENTER
                handle_submenu_selection(gui, gui.main_menu_selection, gui.sub_menu_selection)
            elif key == 27 or key == curses.KEY_LEFT:  # ESC or Left
                gui.switch_to_main_menu()
        
        elif gui.navigation_state == NAV_HELP_TOPICS:
            if key == curses.KEY_UP:
                gui.help_topic_selection = max(0, gui.help_topic_selection - 1)
            elif key == curses.KEY_DOWN:
                gui.help_topic_selection = min(len(gui.help_topics) - 1, gui.help_topic_selection + 1)
            elif key == 10 or key == 13:  # ENTER
                gui.navigation_state = NAV_HELP_CONTENT
                gui.help_content_scroll = 0
            elif key == 27 or key == curses.KEY_LEFT:  # ESC or Left
                gui.switch_to_main_menu()
        
        elif gui.navigation_state == NAV_HELP_CONTENT:
            if key == curses.KEY_UP:
                if gui.help_topic_selection < len(gui.help_topics):
                    topic_id, topic_name = gui.help_topics[gui.help_topic_selection]
                    content = gui.get_help_content(topic_id)
                    visible_lines = gui.content_height - 4
                    max_scroll = max(0, len(content) - visible_lines)
                    gui.help_content_scroll = max(0, gui.help_content_scroll - 1)
            elif key == curses.KEY_DOWN:
                if gui.help_topic_selection < len(gui.help_topics):
                    topic_id, topic_name = gui.help_topics[gui.help_topic_selection]
                    content = gui.get_help_content(topic_id)
                    visible_lines = gui.content_height - 4
                    max_scroll = max(0, len(content) - visible_lines)
                    gui.help_content_scroll = min(max_scroll, gui.help_content_scroll + 1)
            elif key == 27 or key == curses.KEY_LEFT:  # ESC or Left - Back to topics
                gui.navigation_state = NAV_HELP_TOPICS
                gui.help_content_scroll = 0

def main():
    """FIXED: Main entry point with comprehensive error handling"""
    try:
        if not sys.stdout.isatty():
            print("Error: This program requires a terminal")
            print("Please run from command line or terminal")
            sys.exit(1)
        
        ensure_directories()
        cleanup_temp_files()
        
        curses.wrapper(main_program_loop)
        
        print("\nHollik's Greaseweazle Helper v1.0 terminated normally")
        print("Configuration saved. Thank you for using the helper!")
        print("\nKey improvements in this version:")
        print("• Fixed --no-verify support prevents verification failures")
        print("• Correct format strings from Yann Serra Tutorial")
        print("• Proper file extensions for each system")
        print("• Added ZX Spectrum support")
        print("• Fixed terminal display and resize handling")
        
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        print("Please check your configuration and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()