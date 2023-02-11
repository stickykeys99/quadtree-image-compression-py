import pygame, numpy as np, os, sys, math, datetime, time
from collections import deque
from PIL import Image

t0 = time.time_ns()
nano_to_sec = 1e-09

pygame.init()
SCR_W, SCR_H = SCR_SIZE = (1080,720)
SCR_CENTER = (SCR_W // 2, SCR_H // 2)
scr = pygame.display.set_mode(SCR_SIZE)

# anything that is marked as EDITABLE can be modified by the user

# EDITABLE
# edit the filename to load (without the folder)
file_name = 'test2.jpg'

# (converts to an array)
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(f'{dir_path}/images')
img = pygame.image.load(file_name).convert_alpha()
img_arr = pygame.surfarray.pixels3d(img)
max_depth = min(math.ceil(math.log2(img_arr.shape[0])),math.ceil(math.log2(img_arr.shape[1]))) - 1

# EDITABLE
# error threshold
ERROR_THRES = 3.0

# EDITABLE
# max depth without bypass is the highest possible depth with the given image
max_depth_bypass = 0

# EDITABLE
# will only be used if max_depth_bypass = 1
# will not be used if the highest possible depth is less than it anyway
max_depth_given_bypass = 5

# EDITABLE
# recommended values are 0, 1
line_thickness = 1

# EDITABLE
# pass 0 to turn it into an ellipse
rectangle = 1

# EDITABLE
# pass 0 for a transparent bg of the nodes, only makes sense for drawing ellipses, and only has an effect on the on-screen view (it is already transparent for the saved image)
# also reflected on the GUI bg
black_bg = 0

line_depth = 3

# nothing left to edit below

if max_depth_bypass:
    max_depth = min(max_depth_given_bypass,max_depth)

avg_dp = {}

# w_h is a [int int], numpy array
def make_dp(topleft: (int,int), w_h, depth: int):
    if (topleft, tuple(w_h), depth) in avg_dp:
        return avg_dp[(topleft, tuple(w_h), depth)]
    if w_h[0] == 1 or w_h[1] == 1:
        avg = np.array([0, 0, 0])
        for y in range(w_h[1]):
            for x in range(w_h[0]):
                avg += img_arr[topleft[0] + x][topleft[1] + y]
        avg = avg // (w_h[0] * w_h[1])

        # for some reason implementation below is slower, on my end
        # avg = np.mean(img_arr[topleft[0]:topleft[0]+w_h[0],topleft[1]:topleft[1]+w_h[1]],axis=(0,1),dtype=np.int32)
        
        avg_dp[(topleft, tuple(w_h), depth)] = avg
        return avg
    
    tl = make_dp(topleft, w_h // 2, depth+1)
    tr = make_dp((topleft[0] + w_h[0] // 2, topleft[1]), np.array([w_h[0]-w_h[0]//2,w_h[1]//2]), depth+1)
    bl = make_dp((topleft[0], topleft[1] + w_h[1] // 2), np.array([w_h[0]//2,w_h[1]-w_h[1]//2]), depth+1)
    br = make_dp((topleft[0] + w_h[0] // 2, topleft[1] + w_h[1] // 2), np.array([w_h[0]-w_h[0]//2,w_h[1]-w_h[1]//2]), depth+1)

    avg = (tl+tr+bl+br) // 4
    avg_dp[(topleft, tuple(w_h), depth)] = avg
    return avg

pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])
gui_font = pygame.font.Font(None,30)
clock = pygame.time.Clock()

ld_bg = pygame.Surface(SCR_SIZE).convert_alpha()
ld_bg.fill('BLACK')
scr.blit(ld_bg,(0,0))
txt_surf = gui_font.render("Loading color averages...",True,'WHITE')
txt_rect = txt_surf.get_rect(center=ld_bg.get_rect().center)
scr.blit(txt_surf,txt_rect)
pygame.display.update()

make_dp((0,0),np.array(img_arr.shape[0:2]),0)

ld_bg.fill('BLACK')
scr.blit(ld_bg,(0,0))
txt_surf = gui_font.render("Building image...",True,'WHITE')
txt_rect = txt_surf.get_rect(center=ld_bg.get_rect().center)
scr.blit(txt_surf,txt_rect)
pygame.display.update()

if black_bg:
    node_bg_color = pygame.Color(0,0,0)
    bg_color = pygame.Color(0,0,0)
else:
    node_bg_color = pygame.Color(0,0,0,0)
    bg_color = pygame.Color(avg_dp[((0,0),img_arr.shape[0:2],0)])

bg = pygame.Surface(SCR_SIZE).convert_alpha()
bg.fill(bg_color)
scr.blit(bg,(0,0))

result = pygame.Surface(img_arr.shape[0:2]).convert_alpha()

on_screen = pygame.Surface(img_arr.shape[0:2]).convert_alpha()
on_screen_rect = on_screen.get_rect(center=SCR_CENTER)

pygame.display.update()

name = str(datetime.datetime.now()).replace(':','-').split('.', 1)[0]
if not os.path.exists(f'{dir_path}/images/{name}'): 
    os.makedirs(f'{dir_path}/images/{name}')
os.chdir(f'{dir_path}/images/{name}')

q = deque([((0,0),img_arr.shape[0:2],0)])
q2 = deque([((0,0),img_arr.shape[0:2],0)])
mask = pygame.Surface(img_arr.shape[0:2]).convert_alpha()
mask.set_colorkey(pygame.Color(0,0,0))

test_color = pygame.Color(avg_dp[((0,0),img_arr.shape[0:2],0)])

images = []

done = 0
curr_depth = 0
is_running = True
while is_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

    if q2:
        e = q2.pop()
        r = pygame.Rect(e[0], e[1])
        c = avg_dp[e]
        depth = e[2]

        if rectangle:
            b_r = 0
        else:
            b_r = min(r.w,r.h)//2

        pygame.draw.rect(mask,pygame.Color(10,10,10),r,line_thickness,b_r)

        if depth != line_depth:

            topleft = e[0]
            w_h = e[1]
            depth = e[2]

            children = ((topleft, (w_h[0] // 2,w_h[1] // 2), depth+1), 
                        ((topleft[0] + w_h[0] // 2, topleft[1]), (w_h[0]-w_h[0]//2,w_h[1]//2), depth+1),
                        ((topleft[0], topleft[1] + w_h[1] // 2), (w_h[0]//2,w_h[1]-w_h[1]//2), depth+1),
                        ((topleft[0] + w_h[0] // 2, topleft[1] + w_h[1] // 2), (w_h[0]-w_h[0]//2,w_h[1]-w_h[1]//2), depth+1))

            colors = [avg_dp[i] for i in children]

            errors = [np.mean(np.abs(c-color),axis=0) for color in colors]

            avg_error = np.mean(errors)

            if avg_error > ERROR_THRES:
                [q2.appendleft(child) for child in children]

    if q:
        e = q.pop()
        r = pygame.Rect(e[0], e[1])
        c = avg_dp[e]
        depth = e[2]

        if curr_depth != depth :
            result.blit(mask,(0,0))
            pygame.image.save_extended(result,f'{curr_depth}.png')
            data = pygame.image.tostring(result, 'RGBA')
            images.append(Image.frombytes('RGBA', img_arr.shape[0:2], data))
            curr_depth = depth

        if rectangle:
            b_r = 0
        else:
            b_r = min(r.w,r.h)//2

        # for the result

        # pygame.draw.rect(result,pygame.Color(0,0,0,0),r)
        # pygame.draw.rect(result,test_color,r)
        pygame.draw.rect(result,c,r,0,b_r)

        # if line_thickness and (r.w > 3 or r.h > 3) and depth <= line_depth:
        #     pygame.draw.rect(result,pygame.Color(10,10,10),r,line_thickness,b_r)

        # for on-screen

        # r.left = r.left + on_screen_rect.left
        # r.top = r.top + on_screen_rect.top

        # surf = pygame.Surface(r.size).convert_alpha()
        # surf.fill(node_bg_color)
        # pygame.draw.rect(surf,c,surf.get_rect(),0,b_r)

        # if line_thickness and (r.w > 3 or r.h > 3) and depth <= line_depth:
        #     pygame.draw.rect(surf,pygame.Color(10,10,10),surf.get_rect(),line_thickness,b_r)

        # test_color = c

        # dirty = scr.blit(surf,r)

        # dont forget to uncomment the update call below

        if depth != max_depth:

            topleft = e[0]
            w_h = e[1]
            depth = e[2]

            children = ((topleft, (w_h[0] // 2,w_h[1] // 2), depth+1), 
                        ((topleft[0] + w_h[0] // 2, topleft[1]), (w_h[0]-w_h[0]//2,w_h[1]//2), depth+1),
                        ((topleft[0], topleft[1] + w_h[1] // 2), (w_h[0]//2,w_h[1]-w_h[1]//2), depth+1),
                        ((topleft[0] + w_h[0] // 2, topleft[1] + w_h[1] // 2), (w_h[0]-w_h[0]//2,w_h[1]-w_h[1]//2), depth+1))

            colors = [avg_dp[i] for i in children]

            errors = [np.mean(np.abs(c-color),axis=0) for color in colors]

            avg_error = np.mean(errors)

            if avg_error > ERROR_THRES:
                [q.appendleft(child) for child in children]

        
    elif not done:
        done = 1
        pygame.image.save_extended(result,f'{curr_depth}.png')
        data = pygame.image.tostring(result, 'RGBA')
        images.append(Image.frombytes('RGBA', img_arr.shape[0:2], data))

        try:
            images[0].save(f'{name}.gif', save_all=True, append_images=images[1:], loop=0, duration=[200 for i in range(len(images)-1)] + [2000])
        except Exception as e:
            print('Cannot save as gif (not enough images), or see message:')
            print(e)

        t1 = (time.time_ns() - t0) * nano_to_sec
        print('done!')
        print(f'Finished in {t1:.2f} seconds.')
            
    # pygame.display.update(dirty)
    clock.tick()

pygame.quit()
sys.exit()

# notes

# error is computed via average manhattan for performance

# for some images, passing a depth similar to the image does not help much, in fact it gives a slightly higher file size (provided both are pngs)

# i do not have much control over this given this implementation as the format and saving of the image is handled by pygame

# otherwise, passing even slightly lower depths works completely fine
