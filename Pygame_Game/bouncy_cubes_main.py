import pygame
import sys
import time
import sqlite3

# Initialization and setting window caption
pygame.init()
pygame.font.init()
pygame.mixer.init()
pygame.display.set_caption("Bouncy Cubes")

# Database setup
conn = sqlite3.connect("assets/database/game_data.db")
cursor = conn.cursor()
database_inserted = False # Ensures only 1 score and date gets added to the database per round


cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_data (
        id INTEGER PRIMARY KEY,
        score INTEGER,
        datestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Window dimensions and fps
WIDTH, HEIGHT = 1000, 700
FPS = 60
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Load font files
PIXEL_FONT_LARGE = pygame.font.Font('assets/fonts/Pixeltype.ttf', 86)
PIXEL_FONT_MEDIUM = pygame.font.Font('assets/fonts/Pixeltype.ttf', 54)

# Load music and sound files
MAIN_THEME = "assets/audio/main_theme.mp3"
JUMP_SOUND = pygame.mixer.Sound("assets/audio/jump.wav")
HIT_SOUND = pygame.mixer.Sound("assets/audio/hit.wav")
CRASH_SOUND = pygame.mixer.Sound("assets/audio/crash.wav")
GAME_START_SOUND = pygame.mixer.Sound("assets/audio/horn.wav")
GAME_OVER_SOUND = pygame.mixer.Sound("assets/audio/drums.wav")

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path, keys):
        super().__init__()
        # Player dimensions and image
        self.width = 100
        self.height = 100
        self.image = pygame.transform.scale(pygame.image.load(image_path), (self.width, self.height)).convert_alpha()
        self.rect = self.image.get_rect()
        # Initial position of the player
        self.rect.x = x
        self.rect.y = y
        # Player movement settings
        self.speed = 5
        self.jump_height = -30
        self.jumping = False
        self.gravity = 1
        self.y_speed = 0
        self.x_speed = 0
        self.keys = keys
    
    def reset_position(self, x, y):
        # Resets position and speed after each round
        self.rect.x = x
        self.rect.y = y
        self.y_speed = 0
        self.x_speed = 0
        self.jumping = False

    def detect_collisions(self, other_players):
        # Check for collision with other player
        for player in other_players:
            if pygame.sprite.collide_rect(self, player) and player != self:
                # Determine the direction of the collision
                if self.rect.centerx < player.rect.centerx:
                    direction = 0.4  # Collided from the left
                else:
                    direction = -0.4  # Collided from the right

                # Calculate overlap
                overlap = abs(self.rect.right - player.rect.left) if direction == -1 else abs(self.rect.left - player.rect.right)

                # Adjust positions and reverse horizontal speeds
                self.rect.x -= direction * overlap / 2
                player.rect.x += direction * overlap / 2
                self.x_speed += direction * abs(self.x_speed)
                player.x_speed -= direction * abs(player.x_speed)

                # Reverse vertical speed to create a bounce
                self.y_speed = -abs(self.y_speed // 1.85)
        
        # Check for collision with platforms
        for platform in platforms:
            if pygame.sprite.collide_rect(self, platform):
                if self.y_speed > 0:
                    # Only set the player on top of the platform if moving downward
                    self.jumping = False
                    if not self.fall_through_platform:
                        self.rect.bottom = platform.rect.y
                        self.y_speed = 0
                        
        # Check for collision with ground
        if self.rect.y > HEIGHT - self.height - 10:
            self.jumping = False
            self.rect.y = HEIGHT - self.height - 10
            self.rect.bottom = min(self.rect.bottom, platform.rect.top)
            self.y_speed = 0
            # Play sound if play hits ground hard
            if self.gravity > 15:
                CRASH_SOUND.play()
            self.gravity = 1

    def detect_vertical_movement(self):
        keys = pygame.key.get_pressed()

        # Check for the up arrow key or w key
        if keys[self.keys[2]] and not self.jumping:
            JUMP_SOUND.play()
            self.jumping = True
            self.y_speed = self.jump_height

        # Check for the down arrow key or s key
        if keys[self.keys[3]]:
            self.fall_through_platform = True
            self.gravity += 1
        else:
            self.fall_through_platform = False
            self.gravity = 1

    def detect_horizontal_movement(self):
        keys = pygame.key.get_pressed()

        # check for left and right arrow keys and a and d keys
        if keys[self.keys[0]] and self.rect.x > 0:
            self.x_speed = -self.speed
        elif keys[self.keys[1]] and self.rect.x < WIDTH - self.width:
            self.x_speed = self.speed
        else:
            self.x_speed = 0

    def update(self):
        # Handle player movement
        self.detect_horizontal_movement()
        self.detect_vertical_movement()

        # Reset and apply gravity
        self.y_speed += self.gravity
        self.rect.y += self.y_speed

        # Update horizontal position based on x_speed
        self.rect.x += self.x_speed


# Platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path):
        super().__init__()
        # Platform dimensions and image
        self.width = 200
        self.height = 60
        self.image = pygame.transform.scale(pygame.image.load(image_path), (self.width, self.height)).convert_alpha()
        self.rect = self.image.get_rect()
        # Platform position
        self.rect.x = x
        self.rect.y = y


# Ground class
class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Ground image
        self.image = pygame.transform.scale(pygame.image.load("assets/images/background_ground.png"), (50, 100)).convert_alpha()
        self.rect = self.image.get_rect()
        # Ground tile position
        self.rect.x = x
        self.rect.y = y


# Leaderboard rendering
def leaderboard():
    
    cursor.execute("SELECT score, datestamp FROM game_data WHERE score IS NOT NULL ORDER BY score ASC LIMIT 5")
    top_scores = cursor.fetchall()

    box_width = 700
    box_height = len(top_scores) * 50 + 20

    border_thickness = 8
    pygame.draw.rect(WINDOW, BLACK, ((WIDTH - box_width) // 2 - border_thickness,
                                     HEIGHT // 2 - 120 - border_thickness,
                                     box_width + 2 * border_thickness,
                                     box_height + 2 * border_thickness))

    pygame.draw.rect(WINDOW, WHITE, ((WIDTH - box_width) // 2, HEIGHT // 2 - 120, box_width, box_height))

    y_offset = 0
    for i, (score, datestamp) in enumerate(top_scores):
        if score is not None:
            time_text = PIXEL_FONT_MEDIUM.render("{}. {:.2f} seconds - {}".format(i + 1, float(score), datestamp), True, BLACK)
        else:
            time_text = PIXEL_FONT_MEDIUM.render("{}. No score available".format(i + 1), True, BLACK)

        WINDOW.blit(time_text, ((WIDTH - time_text.get_width()) // 2, HEIGHT // 2 - 100 + y_offset))
        y_offset += 50


# Create sprite groups
player_sprites = pygame.sprite.Group()
platforms = pygame.sprite.Group()

# Create player and add it to the sprite groups
player1 = Player(300, 300, 'assets/images/player3.png', [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s])
player2 = Player(1025, 300, 'assets/images/player5.png', [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN])
player_sprites.add(player1, player2)

# Create platforms and add them to the sprite groups
platform1 = Platform(30, HEIGHT - 210, 'assets/images/platform.png')
platform2 = Platform(WIDTH // 2 - 100, HEIGHT - 300, 'assets/images/platform.png')
platform3 = Platform(WIDTH - 230, HEIGHT - 210, 'assets/images/platform.png')
platform4 = Platform(30, HEIGHT - 550, 'assets/images/platform.png')
platform5 = Platform(WIDTH // 2 - 100, HEIGHT - 650, 'assets/images/platform.png')
platform6 = Platform(WIDTH - 230, HEIGHT - 550, 'assets/images/platform.png')
platform7 = Platform(280, HEIGHT - 375, 'assets/images/platform.png')
platform8 = Platform(920, HEIGHT -375, 'assets/images/platform.png')
platforms.add(platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8)

# Creates ground and adds to sprite group
ground_segments = 50
for i in range(ground_segments):
    ground = Ground(i * 50, HEIGHT - 50)
    platforms.add(ground)


# Main game loop
def main():
    # Set state to menu and draw background
    game_state = MENU
    background = pygame.transform.scale(pygame.image.load("assets/images/mountains.png"), (WIDTH, HEIGHT))

    # Tracking time and players scores
    player1_score = 0
    player2_score = 0
    start_time = time.time()
    clock = pygame.time.Clock()

    # Play game music
    pygame.mixer.music.load(MAIN_THEME)
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and game_state == MENU:
                    # Reset player positions before starting a new game
                    player1.reset_position(300, 300)
                    player2.reset_position(1025, 300)
                    
                    # Declare game variables
                    GAME_START_SOUND.play()
                    game_state = PLAYING
                    database_inserted = False

                elif event.key == pygame.K_RETURN and game_state == GAME_OVER:
                    # Reset player positions before restarting the game
                    player1.reset_position(300, 300)
                    player2.reset_position(1025, 300)

                    # Reset game variables and start a new game
                    GAME_START_SOUND.play()
                    player1_score = 0
                    player2_score = 0
                    start_time = time.time()
                    game_state = PLAYING
                    database_inserted = False

        if game_state == MENU:
            # Load text for menu
            title_text = PIXEL_FONT_LARGE.render("Bouncy Cubes", True, WHITE)
            start_text = PIXEL_FONT_MEDIUM.render("Press ENTER to start", True, WHITE)
            
            # Draw background and text for menu state
            WINDOW.blit(background, (0, 0))
            WINDOW.blit(title_text, ((WIDTH - title_text.get_width()) // 2, 300))
            WINDOW.blit(start_text, ((WIDTH - start_text.get_width()) // 2, 700))
            
            leaderboard()
        
        elif game_state == PLAYING:
            # Loading time and text for game round
            current_time = time.time() - start_time
            timer_text = PIXEL_FONT_MEDIUM.render("Time: {:.2f}".format(current_time), True, BLACK)
            player1_score_text = PIXEL_FONT_MEDIUM.render("Player 1: {}".format(player1_score), True, BLACK)
            player2_score_text = PIXEL_FONT_MEDIUM.render("Player 2: {}".format(player2_score), True, BLACK)
            
            # Drawing background and text for playing state
            WINDOW.blit(background, (0,0))
            WINDOW.blit(timer_text, ((WIDTH - timer_text.get_width()) // 2, 10))
            WINDOW.blit(player1_score_text, (10, 10))
            WINDOW.blit(player2_score_text, (WIDTH - player2_score_text.get_width() - 10, 10))

            # Drawing sprite classes
            player_sprites.draw(WINDOW)
            platforms.draw(WINDOW)
            
            # Updating sprite classes
            player_sprites.update()
            platforms.update()
            player1.detect_collisions(player_sprites)
            player2.detect_collisions(player_sprites)

            # Check for collisions between players and update scores
            if pygame.sprite.collide_rect(player1, player2) and player1.gravity > 8:
                player1_score += 1
                HIT_SOUND.play()
            elif pygame.sprite.collide_rect(player1, player2) and player2.gravity > 8:
                player2_score += 1
                HIT_SOUND.play()

            # Check for game over condition
            if player1_score >= 3 or player2_score >= 3:
                game_state = GAME_OVER

        elif game_state == GAME_OVER and not database_inserted:
            # Insert the winner's time into the database
            winner_time = time.time() - start_time
            cursor.execute("INSERT INTO game_data (score, datestamp) VALUES (?, datetime('now', 'localtime'))", (winner_time,))
            conn.commit()
            database_inserted = True

            # Load text for game over screen and end game
            GAME_OVER_SOUND.play()
            game_over_text = PIXEL_FONT_LARGE.render("Game Over", True, WHITE)
            winner_text = PIXEL_FONT_MEDIUM.render("Player {} wins!".format(1 if player1_score > player2_score else 2), True, WHITE)
            restart_text = PIXEL_FONT_MEDIUM.render("Press ENTER to restart", True, WHITE)

            # Drawing background and text for game over state
            WINDOW.blit(background, (0, 0))
            WINDOW.blit(game_over_text, ((WIDTH - game_over_text.get_width()) // 2, 300))
            WINDOW.blit(winner_text, ((WIDTH - winner_text.get_width()) // 2, 675))
            WINDOW.blit(restart_text, ((WIDTH - restart_text.get_width()) // 2, 750))

            leaderboard()

        # Update display
        pygame.display.flip()


if __name__ == "__main__":
    main()