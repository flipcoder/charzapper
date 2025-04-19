#!/usr/bin/python3

# "CharZapper"
# A character map snippet engine
# Copyright (c) 2023 Grady O'Connell <flipcoder@gmail.com>

import sys
import yaml # To read our dictionary
import pygame # The library we'll use for input and rendering
import pyperclip # Clipboard access
# from pygame_emojis import load_emoji # emojis
from glm import ivec2, ivec3, vec2, vec3 # math vectors
import traceback

# Constants
SCREEN_SIZE = ivec2(400, 300)
FPS = 30 # frames per sec
VERBOSE = False # whether we want debug output
TITLEBAR_RECT = pygame.Rect(0, 0, SCREEN_SIZE.x, 32)
OUTPUT_FIELD_RECT = pygame.Rect(
    0, TITLEBAR_RECT.height, # x, y
    SCREEN_SIZE.x, (SCREEN_SIZE.y - TITLEBAR_RECT.height)/2 # w, h
)
INPUT_FIELD_RECT = pygame.Rect(
    0, OUTPUT_FIELD_RECT.y + OUTPUT_FIELD_RECT.height, # x, y
    SCREEN_SIZE.x, OUTPUT_FIELD_RECT.height
)
TITLE = "CharZapper"
MAX_MATCHES=10

class App:
    
    def __init__(self):

        # initialize pygame library and font system
        pygame.init()
        pygame.font.init()
        
        # set display mode with no frame around the window
        self.screen = pygame.display.set_mode(SCREEN_SIZE, pygame.NOFRAME)

        # window title
        pygame.display.set_caption(TITLE)

        # clock/timer
        self.clock = pygame.time.Clock()
        
        # create background surface and clear it
        self.background = pygame.Surface(SCREEN_SIZE).convert()
        self.background.fill((255, 255, 255))
        
        # load our unicode font
        self.title_font = pygame.font.Font('fonts/MPLUSRounded1c-Regular.ttf', 20)
        if not self.title_font:
            raise Exception('Could not load title font')
        
        self.font = pygame.font.Font('fonts/MPLUSRounded1c-Regular.ttf', 48)
        if not self.font:
            raise Exception('Failed to load font')

        # we want key repeat since the user will be typing
        pygame.key.set_repeat(500, 30)

        # Load our dictionary from our snippets yaml file
        # It's important we use utf-8 to get our unicode symbols
        with open('snippets.yaml', 'r', encoding='utf-8') as f:
            self.dictionary = yaml.safe_load(f)

        # set default values for our app state
        self.best_match = None # the best snippet match
        self.matches = []
        self.shift = False # whether shift is being held
        self.redraw_screen = True # whether we need to redraw the screen
        
        # if the shift key is pressed, this is the capitalized best match
        self.best_match_shift = None # our best match, but in uppercase
        self.matches_shift = []
        self.build_dictionary() # build our snippet dictionary
        
        # preserve the clipboard contents
        # self.old_clipboard = pyperclip.paste()
        
        # clear the clipboard so we don't accidentally paste in the previous
        #   contents
        pyperclip.copy('')

        # set up the cursor blink timer
        self.cursor_time = 0.0
        self.cursor_blink = True # cursor visibility
        self.cursor_blink_speed = 3.0
        
        self.input_text = "" # The string the user types in
        self.done = False # our app's quit flag

        # index of your selection (multiple matches)
        self.selection = 0

    def build_dictionary(self):
        # Generate dictionary of all tags, characters, and exact matches
        #  associated with each snippet
        
        # Initialize our snippet engine's state
        # This is where we'll store the matches that we calculate
        self.tags = {}
        self.chars = {}
        self.lowercase_names = {}
        self.names = {}
        self.lowercase_snippets = {}
        self.tag_matches = {}
        self.char_matches = {}
        
        # Go through every entry in our snippets.yaml file
        # We call each entry key our target 'word'
        for word, data in self.dictionary.items():

            # Associate the lowercase word to the word with its original case
            lowercase_word = word.lower()
            self.lowercase_snippets[lowercase_word] = word
            
            # Read the "tags" section for our target word
            # Tags are words that the user can type that will match our snippet
            try:
                tag_data = data['tags']
            except KeyError:
                tag_data = []
            
            # Add each tag to its set
            for tag in tag_data:
                # print(tag)
                try:
                    self.tags[tag].add(lowercase_word)
                except KeyError:
                    self.tags[tag] = set([lowercase_word])

            # Read the "chars" section for our target word
            # These are indiviual characters that are important to this snippet
            try:
                char_data = data['chars']
            except KeyError:
                char_data = []

            # Add each character to its set
            for ch in char_data:
                try:
                    self.chars[ch].add(lowercase_word)
                except KeyError:
                    self.chars[ch] = set([lowercase_word])

            # Get the exact name that should trigger this snippet
            #   and keep track of it as well as a copy in lowercase
            name = data['name']
            assert name
            lowercase_name = name.lower()
            assert lowercase_name
            self.names[name] = lowercase_word
            self.lowercase_names[lowercase_name] = lowercase_word

        # Debug info for the above code
        if VERBOSE:
            print("Dictionary loaded")
            print("Tags:", len(self.tags))
            print("Chars:", len(self.chars))
            print("Names:", len(self.lowercase_names))

    def update_text(self):
        
        # The text will be updated, so we need to redraw the screen
        self.redraw_screen = True
        
        self.tag_matches = {}
        self.char_matches = {}
        self.best_match = None
        self.matches = []
        self.shift = False
        self.selection = 0
        self.matches = []
        self.matches_shift = []
        
        # Get rid of any whitespace
        input_text = self.input_text.strip()

        # If the input is blank, we can stop here
        if not input_text:
            return

        # preserve initial input case
        self.has_leading_uppercase = self.input_text[0].isupper()
        self.is_all_lowercase = self.input_text.islower()

        input_text = self.input_text.lower()

        # exact target match? (typing pi symbol -> pi symbol)
        try:
            best_match = self.lowercase_snippets[input_text]
            best_match_shift = best_match.upper()
            if self.has_leading_uppercase:
                best_match = best_match_shift
            self.matches = [best_match]
            self.matches_shift = [best_match_shift]
            if VERBOSE:
                print("Exact match:", best_match)
            return True
        except KeyError:
            pass

        # exact name match? (typing "pi" -> pi symbol)
        try:
            best_match = self.lowercase_names[input_text]
            best_match_shift = best_match.upper()
            if self.has_leading_uppercase:
                best_match = best_match_shift
            self.matches = [best_match]
            self.matches_shift = [best_match_shift]
            if VERBOSE:
                print("Exact match:", best_match)
            return True
        except KeyError:
            pass

        # Without an exact match, we now have to look up match possiblities

        # Assume each word in the input text is a tag?
        words = input_text.split()
        # each of our input tags
        for word in words:
            try:
                # look up to see all snippets that use this tag
                snippets = self.tags[word]
                for snippet in snippets:
                    # count the number of similar occurences our input
                    #   text has to the word we're iterating on
                    try:
                        self.tag_matches[snippet] += 1
                    except KeyError:
                        self.tag_matches[snippet] = 1
            except KeyError:
                # no word matches this tag
                pass
        
        # We found tag matches
        if self.tag_matches:
            if VERBOSE:
                print("Tag matches: {}".format(self.tag_matches))

            self.matches = list(
                sorted(self.tag_matches, key=self.tag_matches.get)[:MAX_MATCHES]
            )
            self.matches_shift = [None] * len(self.matches)

            for i in range(len(self.matches)):
                self.matches_shift[i] = self.matches[i].upper()
                if self.has_leading_uppercase:
                    self.matches[i] = self.matches_shift[i]
                elif self.is_all_lowercase:
                    self.matches[i] = self.matches[i].lower()
            return True

        # No exact matches or tag matches? Let's check individual characters
        
        # Characters can repeat, so make sure we only check for each
        #   character once
        used_chars = set()
        
        # Go through each word in the input string
        for word in words:
            # Each character in the word
            for ch in word:
                if ch in used_chars: # ignore repeating characters
                    continue
                try:
                    # Each snippet associated with this character
                    for snippet in self.chars[ch]:
                        used_chars.add(ch) # don't reuse this char
                        try:
                            self.char_matches[snippet] += 1
                        except KeyError:
                            self.char_matches[snippet] = 1
                except KeyError:
                    pass

        # We found a char match
        if self.char_matches:
            
            # Find the best match based on the number of characters matched
            # self.best_match = max(self.char_matches, key=self.char_matches.get)
            
            self.matches = list(
                sorted(self.char_matches, key=self.char_matches.get)[:MAX_MATCHES]
            )
            self.matches_shift = [None] * len(self.matches)

            # Restore the original case of the match
            # self.best_match = self.matches[0]

            # If the user's input had leading uppercase, we'll assume they
            #   want uppercase output
            for i in range(len(self.matches)):
                self.matches_shift[i] = self.matches[i].upper()
                if self.has_leading_uppercase:
                    self.matches[i] = self.matches_shift[i]
                elif self.is_all_lowercase:
                    self.matches[i] = self.matches[i].lower()
            
            if VERBOSE:
                print("Char matches: {}".format(self.char_matches))
            return True
        
        # No match found
        return False
        
    def run(self):

        # loop until the app is done (user quits somehow)
        while not self.done:
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # window was closed
                    self.done = True
                    break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # escape was pressed, quit the app
                        self.cancel()
                    elif event.key in (pygame.K_RSHIFT, pygame.K_LSHIFT):
                        # shift pressed down, redraw
                        self.shift = True
                        self.redraw_screen = True
                    elif event.key == pygame.K_BACKSPACE:
                        # backspace our text and update the match
                        self.input_text = self.input_text[:-1]
                        self.update_text()
                    elif event.key == pygame.K_RETURN:
                        # the user has selected a match
                        self.submit()
                    elif event.key == pygame.K_TAB:
                        # tab between selections
                        if self.matches:
                            if self.shift:
                                self.selection = (self.selection - 1) % len(self.matches)
                            else:
                                self.selection = (self.selection + 1) % len(self.matches)
                            self.redraw_screen = True
                    elif event.key == pygame.K_LEFT:
                        if self.matches:
                            self.selection = (self.selection - 1) % len(self.matches)
                            self.redraw_screen = True
                    elif event.key == pygame.K_RIGHT:
                        if self.matches:
                            self.selection = (self.selection + 1) % len(self.matches)
                            self.redraw_screen = True
                    else:
                        # append the unicode key to our input text string
                        self.input_text += event.unicode
                        # update our match
                        self.update_text()
                elif event.type == pygame.KEYUP:
                    if event.key in (pygame.K_RSHIFT, pygame.K_LSHIFT):
                        # shift released, redraw
                        self.shift = False
                        self.redraw_screen = True

            # if we're done, quit here instead of proceeding to next frame
            if self.done:
                break
            
            # calculate delta time based on our given frames per second
            dt = self.clock.tick(FPS) * 0.001

            # advance app by given delta time
            self.update(dt)
            
            # if something on the screen updated, we'll redraw it
            if self.redraw_screen:
                self.render()
                self.redraw_screen = False # reset the redraw flag
            
            # draw
            pygame.display.flip()
            
    def update(self, dt):
        # cursor blink timer
        self.cursor_time += dt * self.cursor_blink_speed
        if self.cursor_time >= 1.0:
            self.cursor_time = 0
            self.cursor_blink = not self.cursor_blink
            # every time the cursor toggles visibility, redraw the screen
            self.redraw_screen = True

    def submit(self):
        # send the best match to the clipboard and stdout, then quit
        result = None
        if self.shift:
            result = self.matches_shift[self.selection]
        else:
            result = self.matches[self.selection]
        pyperclip.copy(result)
        self.done = True
        print(result) # stdout

    def cancel(self):
        # restore the clipboard state and quit the app
        # pyperclip.copy(self.old_clipboard)
        self.done = True

    def render_title_bar(self, border, x, y, w, h):
        self.render_shadow_box(border, x, y, w, h, multiplier=0.25, invert=True)
        pygame.draw.rect(self.screen, (0,0,0), (x+border, y+border, w-border*2, h-border*2))

    def render_shadow_box(self, border, x, y, w, h, multiplier=1.0, invert=False):
        # draw a box with a shadow of size `border`
        for layer in range(border):
            if invert:
                c = int(255 * ((1-layer/(border-1)) * multiplier))
            else:
                c = int(255 * (layer/(border-1) * multiplier))
            pygame.draw.rect(self.screen, (c, c, c), (x+layer, y+layer, w-layer*2, h-layer*2), 1)
    
    def render(self):
        # clear background
        self.background.fill((255, 255, 255))

        titlebar_text_surfaces = [
            self.title_font.render(TITLE, True, (128, 128, 128)),
            self.title_font.render(TITLE, True, (255, 255, 255))
        ]
        titlebar_rect = titlebar_text_surfaces[0].get_rect()
        
        # render our input text
        input_text_surface = self.font.render(self.input_text, True, pygame.Color(0, 0, 0))
        input_text_rect = input_text_surface.get_rect(
            # center=ivec2(SCREEN_SIZE.x/2, SCREEN_SIZE.y*3/4)
            center=INPUT_FIELD_RECT.center
        )

        # if we have a match, render it
        if self.matches:
            
            # emoji = None
            # if len(self.best_match) == 1:
            #     # try to load emoji
            #     emoji = load_emoji(best)
        
            # if emoji:
            #     output_text_surface = emoji
            # else:
            
            if self.shift:
                output_text_surface = self.font.render(self.matches_shift[self.selection], True, pygame.Color(0, 0, 0))
            else:
                output_text_surface = self.font.render(self.matches[self.selection], True, pygame.Color(0, 0, 0))
            output_text_rect = output_text_surface.get_rect(
                # center=ivec2(SCREEN_SIZE.x/2, SCREEN_SIZE.y/4)
                center=OUTPUT_FIELD_RECT.center
            )

        # gradient line
        # for ofs in range(-2, 2):
        #     col = vec3(1.0) * abs(ofs)/3 # floating point color
        #     col = ivec3(col * 255.0) # convert to integer color
        #     pygame.draw.line(
        #         self.background,
        #         pygame.Color(col.x, col.y, col.z), # convert to pygame color
        #         (0, SCREEN_SIZE.y/2 + ofs),
        #         (SCREEN_SIZE.x, SCREEN_SIZE.y/2 + ofs)
        #     )
        
        # draw the background
        self.screen.blit(self.background, (0, 0))
        
        # draw the 3 boxes around our fields
        # self.render_shadow_box(3,0,0,SCREEN_SIZE.x,SCREEN_SIZE.y/2)
        # self.render_shadow_box(3,0,SCREEN_SIZE.y/2,SCREEN_SIZE.x,SCREEN_SIZE.y/2)
        
        # draw title bar's black box
        self.render_title_bar(8, *TITLEBAR_RECT)
        self.screen.blit(titlebar_text_surfaces[0], (SCREEN_SIZE.x/2 - titlebar_rect.width/2, 0))
        self.screen.blit(titlebar_text_surfaces[1], (SCREEN_SIZE.x/2 - titlebar_rect.width/2 + 1, 1))
        
        self.render_shadow_box(3, *INPUT_FIELD_RECT)
        self.render_shadow_box(3, *OUTPUT_FIELD_RECT)

        if self.cursor_blink:
            cursor = self.font.render('_', True, pygame.Color(0, 0, 0))

            # push the cursor forwards if we have text
            if self.input_text:
                cursor_ofs = 10
            else:
                cursor_ofs = 0
                
            # put the cursor after the centered text
            cursor_rect = cursor.get_rect(
                center=ivec2(
                    input_text_rect.right + cursor_ofs,
                    input_text_rect.centery
                )
            )
            
            # draw cursor
            self.screen.blit(cursor, cursor_rect)
        
        # draw input text
        self.screen.blit(input_text_surface, input_text_rect)

        # if we have a match, draw the match
        if self.matches:
            self.screen.blit(output_text_surface, output_text_rect)

def main():
    # Create the app instance
    try:
        app = App()
    except Exception as e:
        traceback.print_exc()
        return 1
    
    # Run it
    try:
        app.run()
    except Exception as e:
        traceback.print_exc()
        return 1
    
    pygame.quit()
    return 0

if __name__ == '__main__':
    sys.exit(main())

