import pygame, numpy as np, os, sys, math
from collections import deque

pygame.init()
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])

SCR_W, SCR_H = SCR_SIZE = (1080,720)
SCR_CENTER = (SCR_W // 2, SCR_H // 2)
scr = pygame.display.set_mode(SCR_SIZE)
gui_font = pygame.font.Font(None,30)

ERROR_THRES = 1

clock = pygame.time.Clock()

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(f'{dir_path}/images')

img = pygame.image.load('img.jpg').convert_alpha()

img_arr = pygame.surfarray.pixels3d(img)

avg_dp = {}

# w_h is a [int int], numpy array
def make_dp(topleft: (int,int), w_h, depth: int):
    if w_h[0] == 1 or w_h[1] == 1:
        avg = np.array([0, 0, 0])
        for y in range(w_h[1]):
            for x in range(w_h[0]):
                avg += img_arr[topleft[0] + x][topleft[1] + y]
        avg = avg // (w_h[0] * w_h[1])

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

ld_bg = pygame.Surface(SCR_SIZE).convert_alpha()
ld_bg.fill('BLACK')
scr.blit(ld_bg,(0,0))
txt_surf = gui_font.render("Loading color averages...",True,'WHITE')
txt_rect = txt_surf.get_rect(center=ld_bg.get_rect().center)
scr.blit(txt_surf,txt_rect)
pygame.display.update()

make_dp((0,0),np.array(img_arr.shape[0:2]),0)

bg = pygame.Surface(SCR_SIZE).convert_alpha()
bg.fill(pygame.Color(150,150,150))
scr.blit(bg,(0,0))
pygame.display.update()

result = pygame.Surface(img_arr.shape[0:2]).convert_alpha()
result_rec = result.get_rect(center=SCR_CENTER)

q = deque([((0,0),img_arr.shape[0:2],0)])

max_depth = 8

max_depth = min(math.ceil(math.log2(img_arr.shape[0])),math.ceil(math.log2(img_arr.shape[1]))) - 1

done = 0
is_running = True
while is_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

    if q:
        e = q.pop()
        r = pygame.Rect(e[0], e[1])
        c = avg_dp[e]
        pygame.draw.rect(result,pygame.Color(0,0,0,0),r)
        # pygame.draw.rect(result,c,r)
        pygame.draw.circle(result,c,r.center,min(r.w,r.h)//2)

        if e[2] != max_depth:

            # tl = make_dp(topleft, w_h // 2, depth+1)
            # tr = make_dp((topleft[0] + w_h[0] // 2, topleft[1]), np.array([w_h[0]-w_h[0]//2,w_h[1]//2]), depth+1)
            # bl = make_dp((topleft[0], topleft[1] + w_h[1] // 2), np.array([w_h[0]//2,w_h[1]-w_h[1]//2]), depth+1)
            # br = make_dp((topleft[0] + w_h[0] // 2, topleft[1] + w_h[1] // 2), np.array([w_h[0]-w_h[0]//2,w_h[1]-w_h[1]//2]), depth+1)

            topleft = e[0]
            w_h = e[1]
            depth = e[2]

            children = ((topleft, (w_h[0] // 2,w_h[1] // 2), depth+1), 
                        ((topleft[0] + w_h[0] // 2, topleft[1]), (w_h[0]-w_h[0]//2,w_h[1]//2), depth+1),
                        ((topleft[0], topleft[1] + w_h[1] // 2), (w_h[0]//2,w_h[1]-w_h[1]//2), depth+1),
                        ((topleft[0] + w_h[0] // 2, topleft[1] + w_h[1] // 2), (w_h[0]-w_h[0]//2,w_h[1]-w_h[1]//2), depth+1))

            colors = [avg_dp[i] for i in children]

            errors = [np.mean(np.abs(c-color),axis=0,dtype=np.int32) for color in colors]

            avg_error = np.mean(errors)

            if avg_error > ERROR_THRES:
                [q.appendleft(child) for child in children]
    elif not done:
        done = 1
        print('done!')
            
    pygame.display.update(scr.blit(result,result_rec))
    clock.tick()

pygame.quit()
sys.exit()

# notes

# error is computed via average manhattan for performance