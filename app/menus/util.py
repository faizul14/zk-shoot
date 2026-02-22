import app.menus.banner as banner
ascii_art = banner.load("https://me.mashu.lol/mebanner880.png", globals())

from html.parser import HTMLParser
import os
import re
import textwrap
from app.menus.ui import console, print_banner

ascii_art = r"""
                                      
                             .^^                  
                          :~7?J7                  
                        ~7JJJJJ!                  
                       :JJJJJJJ!                  
       .777777777~.    :JJJJJJJ!                  
       .?B#BBBBBBBP!  ..7JJJJJJ!                  
         .?BBBBBBBBB57P~^JJJJJJ7                  
           :JBBBBBBBBBBP.7JJJJJ?77777777777?!     
             ^YBBBBBBBBB5:7JJJJJJJJJJJJJJJJ7.     
               7BBBBBBBBBP~7JJJJJJJJJJJJJJ!.      
             :JGBBBBBBBBBBG?7??JJJJJJJJJ?~        
           .?GBBBBBBBBBBBBBBPJ??!:::::::.         
          7GBBBBBBBBGJGBBBBBBBG5?                 
        !P##BBBBBBG?. :JBBBBBBB#BP~               
       .JJJJJJJJJ7:     :?JJJJJJJJ?.              
                            
        Dor MyXL by FMP
"""

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print(ascii_art, style="bold cyan")

def pause():
    console.input("\n[dim]Tekan [bold cyan]Enter[/bold cyan] untuk lanjut...[/dim]")

class HTMLToText(HTMLParser):
    def __init__(self, width=80):
        super().__init__()
        self.width = width
        self.result = []
        self.in_li = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.in_li = True
        elif tag == "br":
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag == "li":
            self.in_li = False
            self.result.append("\n")

    def handle_data(self, data):
        text = data.strip()
        if text:
            if self.in_li:
                self.result.append(f"- {text}")
            else:
                self.result.append(text)

    def get_text(self):
        # Join and clean multiple newlines
        text = "".join(self.result)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        # Wrap lines nicely
        return "\n".join(textwrap.wrap(text, width=self.width, replace_whitespace=False))

def display_html(html_text, width=80):
    parser = HTMLToText(width=width)
    parser.feed(html_text)
    return parser.get_text()

def format_quota_byte(quota_byte: int) -> str:
    GB = 1024 ** 3 
    MB = 1024 ** 2
    KB = 1024

    if quota_byte >= GB:
        return f"{quota_byte / GB:.2f} GB"
    elif quota_byte >= MB:
        return f"{quota_byte / MB:.2f} MB"
    elif quota_byte >= KB:
        return f"{quota_byte / KB:.2f} KB"
    else:
        return f"{quota_byte} B"