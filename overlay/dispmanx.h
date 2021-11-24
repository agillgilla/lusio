#ifndef DISPMANX_H
#define DISPMANX_H

#include <stdint.h>

// dispmanx layers consts for displaying multiple accelerated overlays in preview
#define DISP_LAYER_BACKGROUD     0xe
#define DISP_LAYER_VIDEO_PREVIEW 0xf
#define DISP_LAYER_TEXT          0x1f

// default ARGB color for preview background (black)
#define BLANK_BACKGROUND_DEFAULT    0xff000000

// display to which we will output the preview overlays
#define DISP_DISPLAY_DEFAULT     0

int msleep(long msec);
void dispmanx_init(void);
int dispmanx_add_text(const char *str, int strlen);
void dispmanx_create_text_overlay(void);
void dispmanx_draw_text_overlay(int text_id, int x, int y, void *resource);
void dispmanx_loop(void);
void dispmanx_destroy(void);
void dispmanx_update_text_overlay(void);

void set_start_timestamp(const char *str, int strlen);
void set_end_timestamp(const char *str, int strlen);

#endif
