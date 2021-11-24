#include "dispmanx.h"
#include "log.h"
#include "text.h"

#include <stdint.h>
#include <assert.h>

#include <bcm_host.h>

// for debugging: write TEST DATA at startup
// and semi-transparet overlay each refresh to see all th texts overlayed
//#define DEBUG_FILL_TEXT_OVERLAY

DISPMANX_UPDATE_HANDLE_T dispmanx_start_update( int Priority );
void dispmanx_sync( DISPMANX_UPDATE_HANDLE_T Update );

static DISPMANX_DISPLAY_HANDLE_T   g_display;
static DISPMANX_MODEINFO_T         g_modeInfo;

static DISPMANX_RESOURCE_HANDLE_T  g_frontResource;
static DISPMANX_RESOURCE_HANDLE_T  g_backResource;

static uint8_t* g_canvas;
static uint32_t g_canvas_size;
static uint32_t g_canvas_height;
static uint32_t g_canvas_width;

static uint32_t g_video_width;
static uint32_t g_video_height;

#ifndef ALIGN_TO_16
#define ALIGN_TO_16(x)  ((x + 15) & ~15)
#endif

#define DISP_CANVAS_BYTES_PER_PIXEL 4

#ifdef DEBUG_FILL_TEXT_OVERLAY
// just for testing: works only with ARGB images
static void fill_rect(VC_IMAGE_TYPE_T type, void *canvas, int width, int height, int x, int y, int w, int h, int val)
{
    int         row;
    int         col;

    int pitch = width * DISP_CANVAS_BYTES_PER_PIXEL;
    uint32_t *line = (uint32_t*)((uint8_t *)(canvas) + ((y * width) + x) * DISP_CANVAS_BYTES_PER_PIXEL);

    for (row = 0; (row < h) && (y + row < height); ++row) {
        for (col = 0; (col < w) && (x + col < width); ++col) {
                line[col] = val;
        }
        line = (uint32_t*)((uint8_t *)line + pitch);
    }
}
#endif

void dispmanx_create_text_overlay(void)
{
    VC_RECT_T dst_rect, src_rect;
    DISPMANX_UPDATE_HANDLE_T update;
    uint32_t vc_image_ptr;
    int ret;

    int width  = ALIGN_UP(g_video_width,  32);
    int height = ALIGN_UP(g_video_height, 16);
    int x = (g_modeInfo.width - width) / 2;
    int y = (g_modeInfo.height - height) / 2;

#if 0
    VC_DISPMANX_ALPHA_T alpha = { DISPMANX_FLAGS_ALPHA_FROM_SOURCE | DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS,
                                                     255, //alpha 0->255
                                                     0 };
#endif

    // we will be using double buffering - we're creating two resources with the size of the screen
    g_frontResource = vc_dispmanx_resource_create(VC_IMAGE_ARGB8888, width, height, &vc_image_ptr);
    assert(g_frontResource);
    g_backResource = vc_dispmanx_resource_create(VC_IMAGE_ARGB8888, width, height, &vc_image_ptr);
    assert(g_backResource);

    g_canvas_height = height;
    g_canvas_width  = width;
    int pitch = g_canvas_width * DISP_CANVAS_BYTES_PER_PIXEL;
    g_canvas_size = pitch * g_canvas_height;
    g_canvas = calloc(1, g_canvas_size);
    assert(g_canvas);

#ifdef DEBUG_FILL_TEXT_OVERLAY
    // for debugging: write TEST DATA
    fill_rect(VC_IMAGE_ARGB8888, g_canvas, g_canvas_width, g_canvas_height,  0, 0, 50, 50,     0xFFFFFFFF);
    fill_rect(VC_IMAGE_ARGB8888, g_canvas, g_canvas_width, g_canvas_height,  100, 100, 200, 200,     0xFFFF0000);
    fill_rect(VC_IMAGE_ARGB8888, g_canvas, g_canvas_width, g_canvas_height,  1100, 600, 500, 200,     0xFF0000FF);
    fill_rect(VC_IMAGE_ARGB8888, g_canvas, g_canvas_width, g_canvas_height,  150, 150, 200, 200,     0xFF00FF00);
    fill_rect(VC_IMAGE_ARGB8888, g_canvas, g_canvas_width, g_canvas_height,  500, 500, 200, 200,     0x8800FF00);

    vc_dispmanx_rect_set(&dst_rect, 0, 0, width, height);
    ret = vc_dispmanx_resource_write_data(g_frontResource, VC_IMAGE_ARGB8888, pitch, g_canvas, &dst_rect);
    assert(ret == 0);
#endif

    vc_dispmanx_rect_set(&src_rect, 0, 0, width << 16, height << 16);
    vc_dispmanx_rect_set(&dst_rect, x, y, width, height);

    update = vc_dispmanx_update_start(0);
    assert(update);

    ret = vc_dispmanx_update_submit_sync(update);
    assert(ret == 0);
    log_debug("dispmanx: text overlay created!\n");
}

void dispmanx_add_text(const char *str, int strlen)
{
	const char *font_file = "arial.ttf";
	
	int textid = text_create(font_file, 0, 31, 256);
	
	text_set_text(textid, str, strlen);
	
	redraw_text(textid);
}

void dispmanx_init(void)
{
    if (g_display == 0)
    {
        log_debug("dispmanx: init\n");
        bcm_host_init();
        g_display = vc_dispmanx_display_open(0);
        //g_display = vc_dispmanx_display_open(DISP_DISPLAY_DEFAULT);
        assert(g_display);

        int ret = vc_dispmanx_display_get_info(g_display, &g_modeInfo);
        assert(ret == 0);
        log_info("dispmanx: display %d: %d x %d\n", DISP_DISPLAY_DEFAULT, g_modeInfo.width, g_modeInfo.height);
    }
    
    dispmanx_create_text_overlay();
}

DISPMANX_UPDATE_HANDLE_T dispmanx_start_update(int priority)
{
	return vc_dispmanx_update_start(priority);
}

void dispmanx_sync(DISPMANX_UPDATE_HANDLE_T update)
{
	vc_dispmanx_update_submit_sync(update);
}

void dispmanx_draw_text_overlay(void) 
{
    // Render all text bitmaps
    text_draw_all(g_canvas, g_canvas_width, g_canvas_height, 0); // is_video = 0

    int text_layer = 100;
    int text_width;
    int text_height;
    char *text_bitmap_data; 

    get_textdata(0, &text_width, &text_height, &text_bitmap_data);

    int alignedWidth = ALIGN_TO_16(text_width);
    int alignedHeight = ALIGN_TO_16(text_height);
    int pitchAligned = ALIGN_TO_16(text_width);

    uint32_t img_ptr;

    DISPMANX_RESOURCE_HANDLE_T res = vc_dispmanx_resource_create(VC_IMAGE_ARGB8888, text_width, text_height, &img_ptr);

    VC_RECT_T src_rect;
    VC_RECT_T dst_rect;
    VC_DISPMANX_ALPHA_T alpha;

    DISPMANX_UPDATE_HANDLE_T update = dispmanx_start_update( 10 );
    vc_dispmanx_rect_set( &src_rect, 0, 0, text_width << 16, text_height << 16 );
    uint32_t OutW_ = ALIGN_UP( text_width, 32 );
    //vc_dispmanx_rect_set( &dst_rect, OutW_, text_height, text_width, text_height);
    vc_dispmanx_rect_set(&dst_rect, 500, 500, text_width, text_height);

    vc_dispmanx_element_add(
        update,
        g_display,
        100,
        &dst_rect, res, &src_rect, DISPMANX_PROTECTION_NONE, &alpha, NULL, DISPMANX_NO_ROTATE );    
    
    dispmanx_sync(update);
    
    update = dispmanx_start_update(10);

    VC_RECT_T rect;
    uint32_t pitch = 0;

    pitch = ALIGN_UP(text_width * 4, 32);
    vc_dispmanx_rect_set(&rect, 0, 0, text_width, text_height);

    vc_dispmanx_resource_write_data(
        res,
        VC_IMAGE_ARGB8888,
        pitch,
        text_bitmap_data,
        &rect );

    dispmanx_sync(update);
}

void dispmanx_loop(void) 
{
	dispmanx_draw_text_overlay();	
	
	while (1) {
		msleep(20);

		//dispmanx_update_text_overlay();

		DISPMANX_UPDATE_HANDLE_T update = dispmanx_start_update(10);
		dispmanx_sync(update);
	}
}

#define ELEMENT_REMOVE_IF_EXISTS(_elem) do { if (_elem) { ret = vc_dispmanx_element_remove(update, _elem); assert(ret == 0); } } while(0)
#define RESOURCE_DELETE_IF_EXISTS(_res) do { if (_res) { ret = vc_dispmanx_resource_delete(_res); assert(ret == 0); } } while(0)

void dispmanx_destroy(void)
{
    DISPMANX_UPDATE_HANDLE_T update;
    int ret;

    free(g_canvas);

    log_debug("dispmanx: destroy\n");
    update = vc_dispmanx_update_start(0);
    assert(update != 0);

    ret = vc_dispmanx_update_submit_sync(update);
    assert(ret == 0);

    RESOURCE_DELETE_IF_EXISTS(g_frontResource);
    RESOURCE_DELETE_IF_EXISTS(g_backResource);

    ret = vc_dispmanx_display_close(g_display);
    assert(ret == 0);
}

void dispmanx_update_text_overlay(void)
{
    VC_RECT_T dst_rect;
    int ret;
    //clock_t start_time = clock();
    

    // reset overlay to fully-transparent
    memset(g_canvas, 0, g_canvas_size);
#ifdef DEBUG_FILL_TEXT_OVERLAY // really nice: see refresehed areas (layout boxes)
    fill_rect(VC_IMAGE_ARGB8888, g_canvas, g_canvas_width, g_canvas_height,  0, 0, g_canvas_width, g_canvas_height,     0x33ff0000);
#endif


    // render texts
    text_draw_all(g_canvas, g_canvas_width, g_canvas_height, 0); // is_video = 0
	
    // write data to back resource
    vc_dispmanx_rect_set(&dst_rect, 0, 0, g_canvas_width, g_canvas_height);
    int pitch = g_canvas_width * DISP_CANVAS_BYTES_PER_PIXEL;
	printf("GOT HERRRRRE\n");
    ret = vc_dispmanx_resource_write_data(g_backResource, VC_IMAGE_ARGB8888, pitch, g_canvas, &dst_rect);
    assert(ret == 0);
	
    // change the source of text overlay
    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    assert(update != 0);

    assert(ret == 0);
    ret = vc_dispmanx_update_submit(update, NULL, NULL);
    assert(ret == 0);

    // back <-> front
    DISPMANX_RESOURCE_HANDLE_T tmpResource = g_frontResource;
    g_frontResource = g_backResource;
    g_backResource = tmpResource;
    //log_debug("dispmanx: update took %d ms\n", (clock() - start_time) * 1000 / CLOCKS_PER_SEC);
}

int msleep(long msec)
{
    struct timespec ts;
    int res;

    if (msec < 0)
    {
        errno = EINVAL;
        return -1;
    }

    ts.tv_sec = msec / 1000;
    ts.tv_nsec = (msec % 1000) * 1000000;

    do {
        res = nanosleep(&ts, &ts);
    } while (res && errno == EINTR);

    return res;
}
