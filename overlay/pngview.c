#define _GNU_SOURCE

#include <assert.h>
#include <ctype.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <string.h>
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

#include "ilclient.h"

#include "log.h"
#include "text.h"

#include "imageLayer.h"

#include "bcm_host.h"

//-------------------------------------------------------------------------

#define NDEBUG

//-------------------------------------------------------------------------

uint8_t* g_canvas;
uint32_t g_canvas_size;
uint32_t g_canvas_width;
uint32_t g_canvas_height;

int startTimestampTextId;
int endTimestampTextId;

#define TIMESTAMP_PADDING 100

//-------------------------------------------------------------------------

#define DISP_CANVAS_BYTES_PER_PIXEL 4 // RGBA32 (RGBA8888)

void setStartTimestamp(const char *str, int strlen) {

    startTimestampTextId = createTextBitmap(str, strlen);

    text_set_text(startTimestampTextId, str, strlen);
    
    redraw_text(startTimestampTextId);
}

void setEndTimestamp(const char *str, int strlen) {

    endTimestampTextId = createTextBitmap(str, strlen);

    text_set_text(endTimestampTextId, str, strlen);
    
    redraw_text(endTimestampTextId);
}

int createTextBitmap(const char *str, int strlen)
{
    const char *font_file = "arial.ttf";
	
    // This comes out to a font size of 80 on a 1440p display
    //int font_size = round(g_modeInfo.width / 30.0);
    int font_size = 72;
    
    printf("Font size: %d\n", font_size);

    return text_create(font_file, 0, font_size, 96);
}

void drawTextOverlay(int textId, uint32_t display, int32_t layer, IMAGE_LAYER_T *imageLayer, int32_t x, int32_t y, bool xFromRight, bool yFromBottom) {
    int textWidth;
    int textHeight;
    char *textBitmapData; 

    get_textdata(textId, &textWidth, &textHeight, &textBitmapData);

    initImageWithData(
        &(imageLayer->image),
        VC_IMAGE_RGBA32,
        textWidth,
        textHeight,
        false,
        textBitmapData);
    
    printf("Image dimensions: %dx%d\n", imageLayer->image.width, imageLayer->image.height);
    printf("Image aligned dimensions: %dx%d\n", imageLayer->image.pitch / (imageLayer->image.bitsPerPixel / 8), imageLayer->image.alignedHeight);   

    //---------------------------------------------------------------------

    createResourceImageLayer(imageLayer, layer);

    //---------------------------------------------------------------------

    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    assert(update != 0);
    
    int computedX = x;
    int computedY = y;
    
    if (xFromRight) {
        computedX = x - imageLayer->image.width;
    }
    
    if (yFromBottom) {
        computedY = y - imageLayer->image.height;
    }

    addElementImageLayerOffset(imageLayer,
                               computedX,
                               computedY,
                               display,
                               update);

    int result = vc_dispmanx_update_submit_sync(update);
    assert(result == 0);
}

int main(int argc, char *argv[])
{
    // Transparent (no) background.  Opaque black background causes graphics driver to crash?
    int32_t layer = 101;
    uint32_t displayNumber = 0;
    
    // Initialize text library   
    text_init();

    //---------------------------------------------------------------------   

    bcm_host_init();

    //---------------------------------------------------------------------

    DISPMANX_DISPLAY_HANDLE_T display = vc_dispmanx_display_open(displayNumber);
    assert(display != 0);

    //---------------------------------------------------------------------

    DISPMANX_MODEINFO_T info;
    int result = vc_dispmanx_display_get_info(display, &info);
    assert(result == 0);
    
    

    //---------------------------------------------------------------------   
    
    g_canvas_width  = info.width;
    g_canvas_height = info.height;
    int pitch = g_canvas_width * DISP_CANVAS_BYTES_PER_PIXEL;
    g_canvas_size = pitch * g_canvas_height;
    g_canvas = calloc(1, g_canvas_size);
    assert(g_canvas);

    setStartTimestamp("1:00:00", 7);

    setEndTimestamp("2:00:00", 7);
    
    // Render all text bitmaps
    text_draw_all(g_canvas, g_canvas_width, g_canvas_height, 0); // is_video = 0

/////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////// START TIMESTAMP //////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
    IMAGE_LAYER_T startImageLayer;

    int startTextWidth;
    int startTextHeight;

    get_textsize(startTimestampTextId, &startTextWidth, &startTextHeight);

    drawTextOverlay(startTimestampTextId, display, layer, &startImageLayer, TIMESTAMP_PADDING, info.height, false, true);

/////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////// START TIMESTAMP //////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////// END TIMESTAMP ///////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
    IMAGE_LAYER_T endImageLayer;

    int endTextWidth;
    int endTextHeight;

    get_textsize(endTimestampTextId, &endTextWidth, &endTextHeight);

    drawTextOverlay(endTimestampTextId, display, layer, &endImageLayer, info.width - TIMESTAMP_PADDING, info.height, true, true);

/////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////// END TIMESTAMP ///////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////

    //---------------------------------------------------------------------

    // Sleep for 10 milliseconds every run-loop
    const int sleepMilliseconds = 10;

    while (true)
    {
        usleep(sleepMilliseconds * 1000);
    }

    destroyImageLayer(&startImageLayer);
    destroyImageLayer(&endImageLayer);

    //---------------------------------------------------------------------

    result = vc_dispmanx_display_close(display);
    assert(result == 0);

    //---------------------------------------------------------------------

    return 0;
}

