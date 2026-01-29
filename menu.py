"""
Menu systém pro LightBot
Parametrizované třídy pro herní menu
"""
import arcade
from typing import List, Tuple, Optional, Callable


class MenuItem:
    """Parametrizovaná položka menu - snadno rozšiřitelná"""
    
    def __init__(
        self,
        label: str,
        item_type: str = "action",  # "action", "toggle", "submenu"
        value: str = None,  # Aktuální hodnota pro toggle
        options: List[str] = None,  # Možné hodnoty pro toggle
        action: Callable = None,  # Callback pro action
        submenu_items: List['MenuItem'] = None,  # Položky submenu
        enabled: bool = True
    ):
        self.label = label
        self.item_type = item_type
        self.value = value
        self.options = options or []
        self.action = action
        self.submenu_items = submenu_items or []
        self.enabled = enabled
    
    def toggle_value(self):
        """Přepne hodnotu na další v seznamu options"""
        if self.item_type == "toggle" and self.options:
            current_idx = self.options.index(self.value) if self.value in self.options else 0
            next_idx = (current_idx + 1) % len(self.options)
            self.value = self.options[next_idx]
    
    def get_display_text(self) -> str:
        """Vrátí text pro zobrazení v menu"""
        if self.item_type == "toggle" and self.value:
            return f"{self.label}: {self.value}"
        return self.label


class GameMenu:
    """Hlavní herní menu - parametrizované a snadno rozšiřitelné"""
    
    # Barvy menu (lze snadno změnit)
    BACKGROUND_COLOR = (20, 20, 40, 230)  # Tmavě modrá s průhledností
    TITLE_COLOR = (255, 215, 0)  # Zlatá
    ITEM_COLOR = (200, 200, 200)  # Světle šedá
    SELECTED_COLOR = (100, 255, 100)  # Zelená pro vybranou položku
    DISABLED_COLOR = (80, 80, 80)  # Tmavě šedá pro neaktivní
    TOGGLE_VALUE_COLOR = (150, 200, 255)  # Světle modrá pro hodnoty toggle
    
    # Rozměry a pozice
    MENU_WIDTH = 500
    MENU_PADDING = 40
    TITLE_FONT_SIZE = 32
    ITEM_FONT_SIZE = 24
    ITEM_HEIGHT = 45
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        self.selected_index = 0
        self.items: List[MenuItem] = []
        self.title = "MENU"
        
        # Submenu stack (pro navigaci zpět)
        self.menu_stack: List[Tuple[str, List[MenuItem], int]] = []
        
        # Inicializuj položky menu
        self._init_menu_items()
    
    def _init_menu_items(self):
        """Inicializace položek menu - snadno upravitelné"""
        self.items = [
            MenuItem(
                label="Obtížnost",
                item_type="toggle",
                value="normal",
                options=["normal", "pro děti"]
            ),
            MenuItem(
                label="Ovládání",
                item_type="submenu"
            ),
            MenuItem(
                label="Popis nepřátel",
                item_type="submenu"
            ),
            MenuItem(
                label="Popis bonusů",
                item_type="submenu"
            ),
            MenuItem(
                label="High score",
                item_type="submenu"
            ),
            MenuItem(
                label="Konec hry",
                item_type="action"
            ),
        ]
    
    def show(self):
        """Zobrazí menu"""
        self.visible = True
        self.selected_index = 0
    
    def hide(self):
        """Skryje menu"""
        self.visible = False
        # Reset menu stack při zavření
        self.menu_stack.clear()
        self._init_menu_items()
    
    def toggle(self):
        """Přepne viditelnost menu"""
        if self.visible:
            self.hide()
        else:
            self.show()
    
    def move_selection(self, direction: int):
        """Posune výběr nahoru (-1) nebo dolů (+1)"""
        if not self.items:
            return
        
        new_index = self.selected_index + direction
        # Wrap around
        if new_index < 0:
            new_index = len(self.items) - 1
        elif new_index >= len(self.items):
            new_index = 0
        
        self.selected_index = new_index
    
    def select_by_number(self, number: int):
        """Vybere položku podle čísla (1-6)"""
        index = number - 1
        if 0 <= index < len(self.items):
            self.selected_index = index
            return self.activate_selected()
        return None
    
    def select_by_mouse(self, x: int, y: int) -> bool:
        """Zjistí, zda je myš nad některou položkou a vybere ji"""
        if not self.visible:
            return False
        
        menu_x = (self.screen_width - self.MENU_WIDTH) // 2
        menu_y_start = self.screen_height // 2 + 100  # Horní okraj položek
        
        # Kontrola, zda je myš v oblasti menu
        if not (menu_x <= x <= menu_x + self.MENU_WIDTH):
            return False
        
        # Spočítej, nad kterou položkou je myš
        for i, item in enumerate(self.items):
            item_y = menu_y_start - (i * self.ITEM_HEIGHT) - self.ITEM_HEIGHT // 2
            item_top = item_y + self.ITEM_HEIGHT // 2
            item_bottom = item_y - self.ITEM_HEIGHT // 2
            
            if item_bottom <= y <= item_top:
                self.selected_index = i
                return True
        
        return False
    
    def activate_selected(self) -> Optional[str]:
        """Aktivuje vybranou položku, vrátí akci nebo None"""
        if not self.items or self.selected_index >= len(self.items):
            return None
        
        item = self.items[self.selected_index]
        
        if not item.enabled:
            return None
        
        if item.item_type == "toggle":
            item.toggle_value()
            return f"toggle_{item.label}"
        
        elif item.item_type == "action":
            if item.action:
                item.action()
            return f"action_{item.label}"
        
        elif item.item_type == "submenu":
            # TODO: Implementovat submenu navigaci
            return f"submenu_{item.label}"
        
        return None
    
    def draw(self):
        """Vykreslí menu"""
        if not self.visible:
            return
        
        # Pozice menu (na střed obrazovky)
        menu_x = (self.screen_width - self.MENU_WIDTH) // 2
        menu_height = len(self.items) * self.ITEM_HEIGHT + 150  # +150 pro titulek a padding
        menu_y = (self.screen_height - menu_height) // 2
        
        # Pozadí menu
        arcade.draw_lrbt_rectangle_filled(
            menu_x,
            menu_x + self.MENU_WIDTH,
            menu_y,
            menu_y + menu_height,
            self.BACKGROUND_COLOR
        )
        
        # Rámeček
        arcade.draw_lrbt_rectangle_outline(
            menu_x,
            menu_x + self.MENU_WIDTH,
            menu_y,
            menu_y + menu_height,
            self.TITLE_COLOR,
            3
        )
        
        # Titulek
        title_y = menu_y + menu_height - 50
        arcade.draw_text(
            self.title,
            self.screen_width // 2,
            title_y,
            self.TITLE_COLOR,
            self.TITLE_FONT_SIZE,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # Oddělovací čára pod titulkem
        line_y = title_y - 30
        arcade.draw_line(
            menu_x + self.MENU_PADDING,
            line_y,
            menu_x + self.MENU_WIDTH - self.MENU_PADDING,
            line_y,
            self.TITLE_COLOR,
            2
        )
        
        # Položky menu
        items_start_y = line_y - 40
        
        for i, item in enumerate(self.items):
            item_y = items_start_y - (i * self.ITEM_HEIGHT)
            
            # Určení barvy
            if not item.enabled:
                color = self.DISABLED_COLOR
            elif i == self.selected_index:
                color = self.SELECTED_COLOR
            else:
                color = self.ITEM_COLOR
            
            # Indikátor výběru (dvojitá šipka) - vlevo od čísla
            indicator_x = menu_x + 15
            if i == self.selected_index:
                arcade.draw_text(
                    ">>",
                    indicator_x,
                    item_y,
                    self.SELECTED_COLOR,
                    self.ITEM_FONT_SIZE,
                    anchor_x="left",
                    anchor_y="center",
                    bold=True
                )
            
            # Číslo položky (s mezerou za indikátorem)
            number_x = menu_x + self.MENU_PADDING + 20
            arcade.draw_text(
                f"{i + 1}. ",
                number_x,
                item_y,
                color,
                self.ITEM_FONT_SIZE,
                anchor_x="left",
                anchor_y="center"
            )
            
            # Text položky (s dostatečnou mezerou za číslem)
            text_x = number_x + 45
            display_text = item.get_display_text()
            
            # Pro toggle položky - rozděl label a hodnotu
            if item.item_type == "toggle" and item.value:
                # Label s dvojtečkou a mezerou
                label_text = f"{item.label}:   "
                arcade.draw_text(
                    label_text,
                    text_x,
                    item_y,
                    color,
                    self.ITEM_FONT_SIZE,
                    anchor_x="left",
                    anchor_y="center"
                )
                # Hodnota (jiná barva) - přibližně 14px na znak při fontu 24
                value_x = text_x + len(label_text) * 14
                value_color = self.SELECTED_COLOR if i == self.selected_index else self.TOGGLE_VALUE_COLOR
                arcade.draw_text(
                    item.value,
                    value_x,
                    item_y,
                    value_color,
                    self.ITEM_FONT_SIZE,
                    anchor_x="left",
                    anchor_y="center",
                    bold=True
                )
            else:
                arcade.draw_text(
                    display_text,
                    text_x,
                    item_y,
                    color,
                    self.ITEM_FONT_SIZE,
                    anchor_x="left",
                    anchor_y="center"
                )
        
        # Nápověda dole
        help_y = menu_y + 25
        help_text = "Sipky nebo 1-6: vyber | Enter: potvrdit | ESC: zpet"
        arcade.draw_text(
            help_text,
            self.screen_width // 2,
            help_y,
            (150, 150, 150),
            14,
            anchor_x="center",
            anchor_y="center"
        )
