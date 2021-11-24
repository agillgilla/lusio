
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <signal.h>
#include <fcntl.h>
#include <errno.h>
#include <math.h>
#include <pthread.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/statvfs.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <libavutil/mathematics.h>
#include <getopt.h>

#include "bcm_host.h"
#include "ilclient.h"

#include "log.h"
#include "text.h"
#include "dispmanx.h"
#include "timestamp.h"
#include "subtitle.h"

static int is_timestamp_enabled = 0;
static char timestamp_format[128];
static const char *timestamp_format_default = "%a %b %d %l:%M:%S %p";
static LAYOUT_ALIGN timestamp_layout;
static const LAYOUT_ALIGN timestamp_layout_default = LAYOUT_ALIGN_BOTTOM | LAYOUT_ALIGN_RIGHT;
static int timestamp_horizontal_margin;
static const int timestamp_horizontal_margin_default = 10;
static int timestamp_vertical_margin;
static const int timestamp_vertical_margin_default = 10;
static int timestamp_pos_x;
static int timestamp_pos_y;
static int is_timestamp_abs_pos_enabled = 0;
static TEXT_ALIGN timestamp_text_align;
static const TEXT_ALIGN timestamp_text_align_default = TEXT_ALIGN_LEFT;
static char timestamp_font_name[128];
static const char *timestamp_font_name_default = "FreeMono:style=Bold";
static char timestamp_font_file[1024];
static int timestamp_font_face_index;
static const int timestamp_font_face_index_default = 0;
static float timestamp_font_points;
static const float timestamp_font_points_default = 14.0f;
static int timestamp_font_dpi;
static const int timestamp_font_dpi_default = 96;
static int timestamp_color;
static const int timestamp_color_default = 0xffffff;
static int timestamp_stroke_color;
static const int timestamp_stroke_color_default = 0x000000;
static float timestamp_stroke_width;
static const float timestamp_stroke_width_default = 1.3f;
static int timestamp_letter_spacing;
static const int timestamp_letter_spacing_default = 0;

int main(int argc, char **argv) {
    
    // initialize text library
    text_init();
    // setup timestamp
    if (is_timestamp_enabled) {
        if (timestamp_font_file[0] != 0) {
            timestamp_init(timestamp_font_file, timestamp_font_face_index, timestamp_font_points, timestamp_font_dpi);
        } else if (timestamp_font_name[0] != 0) {
            timestamp_init_with_font_name(timestamp_font_name, timestamp_font_points, timestamp_font_dpi);
        } else {
            timestamp_init_with_font_name(NULL, timestamp_font_points, timestamp_font_dpi);
        }
        timestamp_set_format(timestamp_format);
        if (is_timestamp_abs_pos_enabled) {
            timestamp_set_position(timestamp_pos_x, timestamp_pos_y);
        } else {
            timestamp_set_layout(timestamp_layout,
                    timestamp_horizontal_margin, timestamp_vertical_margin);
        }
        timestamp_set_align(timestamp_text_align);
        timestamp_set_color(timestamp_color);
        timestamp_set_stroke_color(timestamp_stroke_color);
        timestamp_set_stroke_width(timestamp_stroke_width);
        timestamp_set_letter_spacing(timestamp_letter_spacing);
        timestamp_fix_position(200, 200);
    }
    
    dispmanx_init();
    
    //dispmanx_add_text("ARJUN", 5);

    set_start_timestamp("ARJUN", 5);
    set_end_timestamp("GILL", 4);
    
    dispmanx_loop();
}
