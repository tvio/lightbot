"""
Testovací skript pro zobrazení kraba v různých rotacích
Vykreslí kraba na úhlech: 45°, 135°, 225°, 315°
"""
import arcade
import math

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

class TestWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Test rotace kraba")
        arcade.set_background_color(arcade.color.BLACK)
        
        # ========================================
        # NASTAVITELNÉ PROMĚNNÉ - MĚŇ SI HODNOTY TADY!
        # ========================================
        self.ROTATION_OFFSET = 0  # Offset pro rotaci obrázku (zkus 0, -90, 90, 180)
        self.SIDE_OFFSET_LEFT = -90 # Offset pro bokem doleva (zkus 90, -90, 180, -180)
        self.SIDE_OFFSET_RIGHT = +90  # Offset pro bokem doprava (zkus -90, 90, -180, 180)
        # ========================================
        
        # Načti krabí sprite
        self.crab_sprites = []
        self.crab_angles = [-45, -135, -225, -315]  # Úhly pro test
        
        try:
            from PIL import Image
            import io
            
            gif_path = "pict/crab-red.gif"
            gif_image = Image.open(gif_path)
            
            frame_count = 0
            textures = []
            
            # Načti první frame z GIFu
            try:
                while True:
                    gif_image.seek(frame_count)
                    
                    if gif_image.mode != 'RGBA':
                        frame_img = gif_image.convert('RGBA')
                    else:
                        frame_img = gif_image.copy()
                    
                    img_bytes = io.BytesIO()
                    frame_img.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    
                    texture = arcade.load_texture(img_bytes)
                    textures.append(texture)
                    frame_count += 1
            except EOFError:
                pass
            
            if textures:
                # Vytvoř 4 sprites na různých pozicích s různými rotacemi
                positions = [
                    (200, 400),  # Levý horní
                    (600, 400),  # Pravý horní
                    (200, 200),  # Levý dolní
                    (600, 200),  # Pravý dolní
                ]
                
                for i, angle in enumerate(self.crab_angles):
                    sprite = arcade.Sprite(textures[0])
                    sprite.center_x, sprite.center_y = positions[i]
                    # Použij nastavitelný offset
                    sprite.angle = angle + self.ROTATION_OFFSET
                    sprite.scale = 0.3  # Zmenšený pro lepší přehlednost
                    self.crab_sprites.append(sprite)
                
                # Vytvoř SpriteList pro správné kreslení
                self.crab_list = arcade.SpriteList()
                for sprite in self.crab_sprites:
                    self.crab_list.append(sprite)
            else:
                print("Nelze načíst texturu kraba")
                
        except Exception as e:
            print(f"Chyba při načítání: {e}")
            # Fallback - vytvoř žluté kruhy místo kraba
            positions = [
                (200, 400),
                (600, 400),
                (200, 200),
                (600, 200),
            ]
            for i, angle in enumerate(self.crab_angles):
                texture = arcade.make_soft_circle_texture(30, arcade.color.YELLOW)
                sprite = arcade.Sprite(texture)
                sprite.center_x, sprite.center_y = positions[i]
                sprite.angle = angle
                sprite.scale = 0.5  # Menší fallback kruh
                self.crab_sprites.append(sprite)
            
            self.crab_list = arcade.SpriteList()
            for sprite in self.crab_sprites:
                self.crab_list.append(sprite)
    
    def on_draw(self):
        self.clear()
        
        # Vykresli sprites
        if hasattr(self, 'crab_list'):
            self.crab_list.draw()
        else:
            # Fallback
            for sprite in self.crab_sprites:
                if hasattr(sprite, 'draw'):
                    sprite.draw()
        
        # Vykresli popisky s úhly (nastavené úhly, před offsetem)
        labels = [
            ("Nastaveno: 45°", 200, 350),
            ("Nastaveno: 135°", 600, 350),
            ("Nastaveno: 225°", 200, 150),
            ("Nastaveno: 315°", 600, 150),
        ]
        
        for text, x, y in labels:
            arcade.draw_text(
                text,
                x, y,
                arcade.color.WHITE,
                20,
                anchor_x="center",
                anchor_y="center"
            )
        
        # Vykresli šipky ukazující směr "doprava" (0°) a "nahoru" (90°)
        # Pro orientaci
        arcade.draw_text(
            "0° = doprava →",
            50, 550,
            arcade.color.YELLOW,
            16
        )
        arcade.draw_text(
            "90° = nahoru ↑",
            50, 520,
            arcade.color.YELLOW,
            16
        )
        arcade.draw_text(
            "180° = doleva ←",
            50, 490,
            arcade.color.YELLOW,
            16
        )
        arcade.draw_text(
            "270° = dolů ↓",
            50, 460,
            arcade.color.YELLOW,
            16
        )
        
        # Vykresli směr pohybu (bokem) pro každého kraba
        for i, sprite in enumerate(self.crab_sprites):
            # Jednoduše: vezmi úhel sprite (může být záporný)
            actual_angle = sprite.angle
            
            # Bokem = úhel + offset (bez normalizace, math.cos/sin to zvládnou)
            side_angle_deg_left = actual_angle + self.SIDE_OFFSET_LEFT
            side_angle_deg_right = actual_angle + self.SIDE_OFFSET_RIGHT
            
            # Převod na radiány pro kreslení
            side_angle_rad = math.radians(abs(side_angle_deg_left))
            
            # Konec šipky (200 pixelů od středu)
            arrow_length = 80
            arrow_end_x = sprite.center_x + math.cos(side_angle_rad) * arrow_length
            arrow_end_y = sprite.center_y + math.sin(side_angle_rad) * arrow_length
            
            # Nakresli šipku směru pohybu (zelená)
            arcade.draw_line(
                sprite.center_x, sprite.center_y,
                arrow_end_x, arrow_end_y,
                arcade.color.GREEN,
                3
            )
            
            # Špička šipky
            arrow_tip_size = 10
            tip_angle1 = side_angle_rad + math.pi - math.pi/6
            tip_angle2 = side_angle_rad + math.pi + math.pi/6
            tip1_x = arrow_end_x + math.cos(tip_angle1) * arrow_tip_size
            tip1_y = arrow_end_y + math.sin(tip_angle1) * arrow_tip_size
            tip2_x = arrow_end_x + math.cos(tip_angle2) * arrow_tip_size
            tip2_y = arrow_end_y + math.sin(tip_angle2) * arrow_tip_size
            arcade.draw_line(arrow_end_x, arrow_end_y, tip1_x, tip1_y, arcade.color.GREEN, 2)
            arcade.draw_line(arrow_end_x, arrow_end_y, tip2_x, tip2_y, arcade.color.GREEN, 2)
            
            # Popisek směru (zelená = doleva)
            label_x = sprite.center_x + math.cos(side_angle_rad) * (arrow_length + 30)
            label_y = sprite.center_y + math.sin(side_angle_rad) * (arrow_length + 30)
            arcade.draw_text(
                f"doleva\n{actual_angle:.0f}+{self.SIDE_OFFSET_LEFT}={side_angle_deg_left:.0f}°",
                label_x, label_y,
                arcade.color.GREEN,
                12,
                anchor_x="center",
                anchor_y="center"
            )
            
            # Zobraz i druhý směr (červeně = doprava) pro srovnání
            side_angle_rad_right = math.radians(abs(side_angle_deg_right))
            arrow_end_x2 = sprite.center_x + math.cos(side_angle_rad_right) * arrow_length
            arrow_end_y2 = sprite.center_y + math.sin(side_angle_rad_right) * arrow_length
            arcade.draw_line(
                sprite.center_x, sprite.center_y,
                arrow_end_x2, arrow_end_y2,
                arcade.color.RED,
                2
            )
            label_x2 = sprite.center_x + math.cos(side_angle_rad_right) * (arrow_length + 50)
            label_y2 = sprite.center_y + math.sin(side_angle_rad_right) * (arrow_length + 50)
            arcade.draw_text(
                f"doprava\n{actual_angle:.0f}+{self.SIDE_OFFSET_RIGHT}={side_angle_deg_right:.0f}°",
                label_x2, label_y2,
                arcade.color.RED,
                10,
                anchor_x="center",
                anchor_y="center"
            )
            
            # Vykresli šipku ukazující, kam krab kouká (modře)
            look_angle_rad = math.radians(abs(actual_angle))
            look_end_x = sprite.center_x + math.cos(look_angle_rad) * (arrow_length - 20)
            look_end_y = sprite.center_y + math.sin(look_angle_rad) * (arrow_length - 20)
            arcade.draw_line(
                sprite.center_x, sprite.center_y,
                look_end_x, look_end_y,
                arcade.color.BLUE,
                2
            )
            arcade.draw_text(
                f"kouká\n{actual_angle:.0f}°",
                look_end_x + 20, look_end_y,
                arcade.color.BLUE,
                10,
                anchor_x="left",
                anchor_y="center"
            )


def main():
    window = TestWindow()
    arcade.run()


if __name__ == "__main__":
    main()

